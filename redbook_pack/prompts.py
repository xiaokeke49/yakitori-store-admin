"""小红书向 LLM 提示词模板（与业务规则绑定；若生成策略变更请同步修改此处）。"""

SYSTEM_XHS = """你是熟悉小红书平台的内容编辑。你的输出将用于用户手动复制到小红书发布，需：
1. 标题：吸睛但不标题党，20字内优先，避免违规承诺与虚假数据。
2. 正文：首句钩子 + 短段落/换行（适合手机阅读），可含少量 emoji，避免编造未提供的销量、排名、热搜名次。
3. 话题标签：6-12 个，与正文强相关；使用小红书常见形式 #话题名#（每个话题用空格分隔）。
4. 热点/选题依据：只根据用户给出的种子词与素材信息撰写，不要虚构「小红书热榜第几名」等可核验虚假信息。

你必须只输出一个 JSON 对象，不要 markdown 代码围栏，不要其它解释。JSON 键为：
title, body, topics（字符串数组）, hotspot_notes（字符串，说明选题如何呼应种子词；若无种子词则说明从素材出发的切入角度）。"""


def build_user_prompt(
    *,
    theme: str | None,
    keywords: str | None,
    image_names: list[str],
    external_refs: str | None = None,
) -> str:
    """
    构造发给模型的用户侧提示。

    作用：把种子词、可选外部摘要、图片文件名列表压缩成一段可解析上下文。

    内部行为：纯字符串拼接；external_refs 为空时不写入该段。
    """
    parts: list[str] = []
    if theme:
        parts.append(f"主题/种子词：{theme}")
    if keywords:
        parts.append(f"补充关键词：{keywords}")
    if not theme and not keywords:
        parts.append("未提供主题种子词：请仅根据下方素材文件名推断场景，并在 hotspot_notes 中说明推断依据。")
    parts.append(f"已选图片（共 {len(image_names)} 张）文件名：{', '.join(image_names) if image_names else '无'}")
    if external_refs:
        parts.append("外部参考摘要（可融入正文角度，勿捏造具体排名数据）：\n" + external_refs)
    parts.append("请生成 JSON：title, body, topics, hotspot_notes。")
    return "\n".join(parts)
