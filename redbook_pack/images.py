"""图片扫描、筛选、复制与可选 3:4 裁剪。"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

# 常见图片扩展名（小写比较）
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif"}


def list_images_in_dir(input_dir: Path) -> list[Path]:
    """
    列出目录内一层（不递归）的图片文件，按文件名排序。

    作用：为组图选择提供稳定、可复现的顺序。

    内部行为：仅根据扩展名过滤；不校验文件内容是否为真实位图。
    """
    if not input_dir.is_dir():
        raise NotADirectoryError(f"输入不是目录: {input_dir}")
    files: list[Path] = []
    for p in input_dir.iterdir():
        if p.is_file() and p.suffix.lower() in _IMAGE_SUFFIXES:
            files.append(p)
    files.sort(key=lambda x: x.name.lower())
    return files


def _crop_center_3_4(img: Image.Image) -> Image.Image:
    """
    将图像居中裁剪为 3:4 竖版比例。

    作用：贴近小红书常见竖图比例；不改变分辨率上限时以短边为基准裁切。

    内部行为：若当前宽高比已等于 3:4 则直接返回；否则按中心裁掉宽或高多余部分。
    """
    w, h = img.size
    target_ratio = 3 / 4  # width / height
    current = w / h
    if abs(current - target_ratio) < 1e-6:
        return img
    if current > target_ratio:
        # 太宽，裁宽度
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    # 太高，裁高度
    new_h = int(w / target_ratio)
    top = (h - new_h) // 2
    return img.crop((0, top, w, top + new_h))


def export_images(
    sources: list[Path],
    dest_dir: Path,
    *,
    crop_3_4: bool = False,
) -> list[str]:
    """
    将源图片导出到目标目录，返回最终写入的相对文件名列表（仅文件名）。

    作用：生成 output/.../redbook/images/ 下的待发布图片。

    内部行为：
      - 目标目录不存在则创建；
      - 文件命名为两位序号 + 原扩展名，避免中文路径在部分工具下异常；
      - crop_3_4 为 True 时用 Pillow 打开、RGB 模式（必要时）、裁剪后按原格式或 JPEG 保存（GIF 转为 JPEG 以简化）。
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for idx, src in enumerate(sources, start=1):
        suffix = src.suffix.lower() or ".jpg"
        if suffix not in _IMAGE_SUFFIXES:
            suffix = ".jpg"
        # HEIC 等可能需 pillow-heif；未安装时让 PIL 抛错给用户提示
        out_name = f"{idx:02d}{suffix if suffix != '.gif' else '.jpg'}"
        dest = dest_dir / out_name
        if not crop_3_4:
            shutil.copy2(src, dest)
            written.append(out_name)
            continue
        with Image.open(src) as im:
            im = im.convert("RGB") if im.mode not in ("RGB", "L") else im
            if im.mode == "L":
                im = im.convert("RGB")
            cropped = _crop_center_3_4(im)
            # 统一 JPEG 减小体积与兼容
            dest_jpg = dest_dir / f"{idx:02d}.jpg"
            cropped.save(dest_jpg, "JPEG", quality=92)
            written.append(dest_jpg.name)
    return written
