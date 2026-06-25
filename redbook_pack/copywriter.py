"""调用 OpenAI 或 Anthropic 生成标题、正文、话题，并格式化为 文案.txt 正文。"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Literal

from redbook_pack.prompts import SYSTEM_XHS, build_user_prompt

Provider = Literal["openai", "anthropic"]


@dataclass
class CopyPayload:
    """LLM 结构化输出在内存中的表示；用于写入 文案.txt。"""

    title: str
    body: str
    topics: list[str]
    hotspot_notes: str

    def to_txt(self, *, theme: str | None, keywords: str | None, external_refs: str | None) -> str:
        """
        渲染为计划约定的 文案.txt 版式。

        作用：与用户在小红书 App 内复制习惯对齐（分段标题）。

        内部行为：话题行将 topics 转为 `#x#` 空格分隔；依据段写入种子词与可选外部参考说明。
        """
        topic_line = " ".join(f"#{t.strip('#')}#" for t in self.topics if t.strip())
        lines = [
            "【标题】",
            self.title.strip(),
            "",
            "【正文】",
            self.body.strip(),
            "",
            "【话题标签】",
            topic_line,
            "",
            "【热点/选题依据】",
        ]
        if theme:
            lines.append(f"- 种子词：{theme}")
        if keywords:
            lines.append(f"- 补充关键词：{keywords}")
        if not theme and not keywords:
            lines.append("- 种子词：（未提供，见模型说明）")
        lines.append(f"- 模型说明：{self.hotspot_notes.strip()}")
        if external_refs:
            lines.append("- 外部参考摘要：")
            for row in external_refs.strip().splitlines():
                lines.append(f"  {row}")
        return "\n".join(lines) + "\n"


def _parse_json_object(text: str) -> dict[str, Any]:
    """
    从模型返回文本中提取 JSON 对象。

    作用：容错少量前后缀空白或误加的 markdown 围栏。

    内部行为：优先整段 json.loads；失败则尝试截取第一个 `{` 到最后一个 `}`。
    """
    raw = text.strip()
    # 去掉 ```json ``` 围栏
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(raw[start : end + 1])
    raise ValueError(f"无法解析 JSON: {text[:500]}...")


def _payload_from_obj(obj: dict[str, Any]) -> CopyPayload:
    topics = obj.get("topics") or []
    if not isinstance(topics, list):
        topics = []
    return CopyPayload(
        title=str(obj.get("title", "")).strip(),
        body=str(obj.get("body", "")).strip(),
        topics=[str(t).strip() for t in topics if str(t).strip()],
        hotspot_notes=str(obj.get("hotspot_notes", "")).strip(),
    )


def resolve_provider() -> Provider:
    """
    根据环境变量决定使用哪家模型。

    作用：支持 REDBOOK_LLM_PROVIDER 强制；否则有 OPENAI_API_KEY 优先 OpenAI，否则 Anthropic。

    内部行为：若两者皆无则抛错，由 CLI 捕获并提示。
    """
    forced = os.environ.get("REDBOOK_LLM_PROVIDER", "").strip().lower()
    if forced in ("openai", "anthropic"):
        return forced  # type: ignore[return-value]
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    raise RuntimeError(
        "未找到 OPENAI_API_KEY 或 ANTHROPIC_API_KEY。请复制 .env.example 为 .env 并填写密钥。"
    )


def generate_copy(
    *,
    theme: str | None,
    keywords: str | None,
    image_names: list[str],
    external_refs: str | None = None,
) -> CopyPayload:
    """
    调用 LLM 生成 CopyPayload。

    作用：单入口封装 OpenAI 与 Anthropic 的差异。

    内部行为：统一要求 JSON 输出；OpenAI 使用 response_format json_object（模型需支持）；失败时抛异常由上层处理。
    """
    provider = resolve_provider()
    user_text = build_user_prompt(
        theme=theme,
        keywords=keywords,
        image_names=image_names,
        external_refs=external_refs,
    )
    if provider == "openai":
        return _generate_openai(user_text)
    return _generate_anthropic(user_text)


def _generate_openai(user_text: str) -> CopyPayload:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_XHS},
            {"role": "user", "content": user_text},
        ],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or ""
    obj = _parse_json_object(content)
    return _payload_from_obj(obj)


def _generate_anthropic(user_text: str) -> CopyPayload:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_XHS,
        messages=[{"role": "user", "content": user_text}],
    )
    parts = []
    for block in msg.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    content = "".join(parts)
    obj = _parse_json_object(content)
    return _payload_from_obj(obj)
