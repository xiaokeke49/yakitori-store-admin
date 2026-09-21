#!/usr/bin/env python3
"""Create a truthful 3:4 social image with a deterministic food grade.

This tool performs only geometric framing and pixel-level colour/tone changes.
It does not generate, remove, repaint, or move food and environment content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError as exc:  # pragma: no cover - exercised by CLI users
    raise SystemExit(
        "缺少 Pillow。请先运行：python3 -m pip install Pillow"
    ) from exc


TARGET_WIDTH = 1080
TARGET_HEIGHT = 1440

PROFILES: dict[str, dict[str, Any]] = {
    "food": {
        "description": "食材与成品串增强档：暖色、食欲感和纹理更明显，但不改变商品事实",
        "rgb": (1.030, 1.008, 0.970),
        "brightness": 1.030,
        "contrast": 1.100,
        "color": 1.100,
        "highlight_protection": {"start": 188, "full": 244},
        "sharpness": {"radius": 1.2, "percent": 55, "threshold": 3},
    },
    "environment": {
        "description": "晚霞与环境轻增强档：保留真实天空层次，不制造假晚霞",
        "rgb": (1.020, 1.005, 0.985),
        "brightness": 1.015,
        "contrast": 1.040,
        "color": 1.035,
        "highlight_protection": {"start": 196, "full": 248},
        "sharpness": {"radius": 1.0, "percent": 30, "threshold": 3},
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_fraction(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("必须在 0 到 1 之间")
    return parsed


def vertical_frame(
    image: Image.Image,
    fit: str,
    centering: tuple[float, float],
    width: int,
    height: int,
) -> Image.Image:
    target = (width, height)
    if fit == "crop":
        return ImageOps.fit(
            image,
            target,
            method=Image.Resampling.LANCZOS,
            centering=centering,
        )

    # Keep the whole source. The fill comes from the same photo and is blurred;
    # no scene content is generated or invented.
    background = ImageOps.fit(
        image,
        target,
        method=Image.Resampling.LANCZOS,
        centering=centering,
    )
    background = background.filter(ImageFilter.GaussianBlur(radius=34))
    background = ImageEnhance.Brightness(background).enhance(0.72)

    foreground = ImageOps.contain(
        image,
        target,
        method=Image.Resampling.LANCZOS,
    )
    x = (width - foreground.width) // 2
    y = (height - foreground.height) // 2
    background.paste(foreground, (x, y))
    return background


def multiply_rgb(image: Image.Image, factors: tuple[float, float, float]) -> Image.Image:
    channels = image.convert("RGB").split()
    adjusted = [
        channel.point(lambda value, factor=factor: min(255, round(value * factor)))
        for channel, factor in zip(channels, factors)
    ]
    return Image.merge("RGB", adjusted)


def apply_grade(image: Image.Image, profile: dict[str, Any]) -> Image.Image:
    original = image.convert("RGB")
    graded = multiply_rgb(original, profile["rgb"])
    graded = ImageEnhance.Brightness(graded).enhance(profile["brightness"])
    graded = ImageEnhance.Contrast(graded).enhance(profile["contrast"])
    graded = ImageEnhance.Color(graded).enhance(profile["color"])

    protection = profile["highlight_protection"]
    start = protection["start"]
    full = protection["full"]
    highlight_mask = ImageOps.grayscale(original).point(
        lambda value: 0
        if value <= start
        else 255
        if value >= full
        else round((value - start) * 255 / (full - start))
    )
    image = Image.composite(original, graded, highlight_mask)
    sharpness = profile["sharpness"]
    return image.filter(
        ImageFilter.UnsharpMask(
            radius=sharpness["radius"],
            percent=sharpness["percent"],
            threshold=sharpness["threshold"],
        )
    )


def save_image(image: Image.Image, output: Path, icc_profile: bytes | None) -> None:
    extension = output.suffix.lower()
    common: dict[str, Any] = {"icc_profile": icc_profile} if icc_profile else {}
    if extension in {".jpg", ".jpeg"}:
        image.save(output, quality=94, subsampling=0, optimize=True, **common)
    elif extension == ".png":
        image.save(output, optimize=True, **common)
    elif extension == ".webp":
        image.save(output, quality=94, method=6, **common)
    else:
        raise SystemExit("输出格式只支持 JPG、JPEG、PNG 或 WEBP")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将真实照片制作成竖版3:4并应用非生成式美食滤镜"
    )
    parser.add_argument("input", type=Path, help="只读原图路径")
    parser.add_argument("output", type=Path, help="新成片路径，不得与原图相同")
    parser.add_argument(
        "--mode",
        choices=sorted(PROFILES),
        default="food",
        help="food用于食材/串品，environment用于晚霞/环境",
    )
    parser.add_argument(
        "--fit",
        choices=("crop", "contain"),
        default="crop",
        help="crop为主体取景裁切；contain用原图模糊背景保留完整画面",
    )
    parser.add_argument("--centering-x", type=validate_fraction, default=0.5)
    parser.add_argument("--centering-y", type=validate_fraction, default=0.5)
    parser.add_argument("--width", type=int, default=TARGET_WIDTH)
    parser.add_argument("--height", type=int, default=TARGET_HEIGHT)
    parser.add_argument(
        "--report",
        type=Path,
        help="JSON报告路径；默认在输出文件旁生成 .json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    report = (
        args.report.expanduser().resolve()
        if args.report
        else Path(f"{output}.json")
    )

    if not source.is_file():
        raise SystemExit(f"找不到原图：{source}")
    if source == output:
        raise SystemExit("禁止覆盖原图，请指定新的输出路径")
    if report in {source, output}:
        raise SystemExit("报告路径不得覆盖原图或成片")
    if output.exists() or report.exists():
        raise SystemExit("输出或报告已存在；请使用新的版本名，禁止覆盖")
    if args.width <= 0 or args.height <= 0:
        raise SystemExit("输出宽高必须大于0")
    if args.width * 4 != args.height * 3:
        raise SystemExit("发布成片必须为竖版3:4")

    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as opened:
        source_size = list(opened.size)
        icc_profile = opened.info.get("icc_profile")
        image = ImageOps.exif_transpose(opened).convert("RGB")

    framed = vertical_frame(
        image,
        args.fit,
        (args.centering_x, args.centering_y),
        args.width,
        args.height,
    )
    profile = PROFILES[args.mode]
    finished = apply_grade(framed, profile)
    save_image(finished, output, icc_profile)

    payload = {
        "schema": "fridge-account-food-filter-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {"path": str(source), "sha256": sha256(source), "size": source_size},
        "output": {
            "path": str(output),
            "sha256": sha256(output),
            "size": [args.width, args.height],
        },
        "mode": args.mode,
        "fit": args.fit,
        "centering": [args.centering_x, args.centering_y],
        "profile": profile,
        "generative_ai": False,
        "audio": False,
        "visual_review_required": True,
        "truthfulness_limits": [
            "不得改变商品数量、形状、配料、熟度、新鲜程度或门店结构",
            "食材图需检查肉色不过红、蔬菜不过饱和、玻璃反光不过度",
            "环境图不得生成或替换天空、晚霞和湖景",
        ],
    }
    report.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
