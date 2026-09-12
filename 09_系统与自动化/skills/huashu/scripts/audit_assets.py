#!/usr/bin/env python3
"""Audit huashu source assets without modifying the project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}

ALIASES = {
    "raw_originals": ["素材库/串品/生串/原图", "生串 A", "生串"],
    "raw_cutouts": ["素材库/串品/生串/透明", "生串 A/透明抠图_高保真", "生串/透明抠图"],
    "cooked_originals": ["素材库/串品/熟串/原图", "烧鸟烤串", "熟串"],
    "cooked_cutouts": ["素材库/串品/熟串/透明", "烧鸟烤串/透明抠图", "熟串/透明抠图"],
    "packaging": ["素材库/包装材料", "06_公域运营/花束茶/花束材料清单", "花束材料清单"],
    "sunset_backgrounds": ["素材库/背景/晚霞", "背景/晚霞", "晚霞"],
    "store_backgrounds": ["素材库/背景/门店", "背景/门店", "门店"],
    "base_photos": ["素材库/花底座", "素材库/花束底座/实拍", "花束底座", "底座"],
    "brand_assets": ["素材库/品牌", "品牌"],
}


def image_files(directory: Path, exclude_nested_cutouts: bool = False) -> list[Path]:
    if not directory.is_dir():
        return []
    result = []
    for path in directory.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        lowered_name = path.name.lower()
        if (
            "联系表" in path.name
            or "contact_sheet" in lowered_name
            or lowered_name.startswith("00_qa_")
        ):
            continue
        if exclude_nested_cutouts and any(part.startswith("透明抠图") for part in path.parts):
            continue
        result.append(path)
    return sorted(result)


def first_existing(root: Path, aliases: list[str]) -> tuple[Path | None, list[Path]]:
    for relative in aliases:
        candidate = root / relative
        if candidate.is_dir():
            exclude = relative in {"生串", "生串 A", "烧鸟烤串", "熟串"}
            return candidate, image_files(candidate, exclude_nested_cutouts=exclude)
    return None, []


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit assets for the huashu skill")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"project root does not exist: {root}")

    categories = {}
    for key, aliases in ALIASES.items():
        directory, files = first_existing(root, aliases)
        categories[key] = {
            "directory": str(directory) if directory else None,
            "count": len(files),
            "files": [str(path.relative_to(root)) for path in files],
        }

    sku_candidates = [root / "商品数据/sku.csv", root / "sku.csv"]
    sku_file = next((path for path in sku_candidates if path.is_file()), None)

    warnings = []
    if categories["raw_originals"]["count"] == 0:
        warnings.append("缺少生串原图：只能制作 AI 概念图，不能做真实生串商品合成。")
    if categories["raw_originals"]["count"] > categories["raw_cutouts"]["count"]:
        warnings.append("生串透明图少于原图：部分串品尚不能稳定进入真实合成。")
    if categories["cooked_originals"]["count"] == 0:
        warnings.append("缺少熟串实拍：AI 熟化结果只能标为效果图。")
    if categories["cooked_originals"]["count"] > categories["cooked_cutouts"]["count"]:
        warnings.append("熟串透明图少于原图：建议为每个可售熟串补透明图。")
    if categories["sunset_backgrounds"]["count"] == 0:
        warnings.append("未在标准目录发现晚霞原图；现有合成成图不应反向作为背景源。")
    if categories["base_photos"]["count"] == 0:
        warnings.append("缺少底座实拍：可做概念设计，但商品化前需补承重与固定结构照片。")
    if sku_file is None:
        warnings.append("缺少 sku.csv：无法可靠绑定串品身份、状态、成本与售价。")

    report = {
        "project_root": str(root),
        "categories": categories,
        "sku_file": str(sku_file) if sku_file else None,
        "warnings": warnings,
        "ready_for": {
            "concept": True,
            "raw_real_composite": categories["raw_originals"]["count"] > 0 and categories["raw_cutouts"]["count"] > 0,
            "cooked_real_composite": categories["cooked_originals"]["count"] > 0 and categories["cooked_cutouts"]["count"] > 0,
            "bound_commercial_package": sku_file is not None,
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
