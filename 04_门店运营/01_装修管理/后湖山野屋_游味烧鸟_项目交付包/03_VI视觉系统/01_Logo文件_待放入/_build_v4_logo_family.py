from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from _vectorize_new_rustic_logo import (
    SOURCE,
    polygon_area,
    simplify_closed,
    smooth_path,
    trace_loops,
)


HERE = Path(__file__).resolve().parent
OUT = HERE / "08_V4_粗粝手作Logo家族"
INK = "#20201E"
PAPER = "#F4EFE5"


@dataclass
class Asset:
    name: str
    mask: np.ndarray
    path: str
    width: int
    height: int


def logo_mask() -> np.ndarray:
    image = Image.open(SOURCE).convert("RGB").crop((95, 430, 1165, 885))
    array = np.asarray(image)
    red, green, blue = array[:, :, 0], array[:, :, 1], array[:, :, 2]
    grayscale = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    red_seal = (red > 105) & (red.astype(float) > green * 1.45) & (red.astype(float) > blue * 1.35)
    mask = (grayscale < 168) & ~red_seal
    return np.asarray(
        Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.MedianFilter(3))
    ) > 127


def make_asset(name: str, source_mask: np.ndarray, box: tuple[int, int, int, int]) -> Asset:
    x1, y1, x2, y2 = box
    region = source_mask[y1:y2, x1:x2]
    ys, xs = np.nonzero(region)
    if not len(xs):
        raise ValueError(f"empty region: {name}")
    left, right = max(0, int(xs.min()) - 2), min(region.shape[1], int(xs.max()) + 3)
    top, bottom = max(0, int(ys.min()) - 2), min(region.shape[0], int(ys.max()) + 3)
    trimmed = region[top:bottom, left:right]
    paths = []
    for loop in trace_loops(trimmed):
        if abs(polygon_area(loop)) < 4.0:
            continue
        simplified = simplify_closed(loop, epsilon=1.0)
        if len(simplified) >= 3:
            paths.append(smooth_path(simplified))
    return Asset(name, trimmed, " ".join(paths), trimmed.shape[1], trimmed.shape[0])


def fit(asset: Asset, x: float, y: float, max_width: float, max_height: float):
    scale = min(max_width / asset.width, max_height / asset.height)
    width, height = asset.width * scale, asset.height * scale
    return x + (max_width - width) / 2, y + (max_height - height) / 2, scale, width, height


def asset_group(asset: Asset, x: float, y: float, max_width: float, max_height: float) -> str:
    px, py, scale, _, _ = fit(asset, x, y, max_width, max_height)
    return f'<path d="{asset.path}" transform="translate({px:.2f} {py:.2f}) scale({scale:.5f})" fill="{INK}" fill-rule="evenodd"/>'


def render_asset(canvas: Image.Image, asset: Asset, x: float, y: float, max_width: float, max_height: float):
    px, py, _, width, height = fit(asset, x, y, max_width, max_height)
    resized = Image.fromarray((asset.mask * 255).astype("uint8")).resize(
        (max(1, round(width)), max(1, round(height))), Image.Resampling.LANCZOS
    )
    ink_layer = Image.new("RGB", resized.size, INK)
    canvas.paste(ink_layer, (round(px), round(py)), resized)


def write_variant(
    filename: str,
    width: int,
    height: int,
    placements: list[tuple[Asset, float, float, float, float]],
    circles: list[tuple[float, float, float, float]] | None = None,
):
    circles = circles or []
    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'  <title>{filename}</title>',
        '  <desc>游味烧鸟 V4 粗粝手作Logo家族；所有文字均为矢量路径，无字体依赖、无嵌入位图。</desc>',
    ]
    for cx, cy, radius, stroke_width in circles:
        svg_parts.append(
            f'  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{INK}" stroke-width="{stroke_width}"/>'
        )
    for placement in placements:
        svg_parts.append("  " + asset_group(*placement))
    svg_parts.append("</svg>")
    svg_path = OUT / f"{filename}.svg"
    svg_path.write_text("\n".join(svg_parts), encoding="utf-8")

    preview = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(preview)
    for cx, cy, radius, stroke_width in circles:
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=INK,
            width=max(1, round(stroke_width)),
        )
    for placement in placements:
        render_asset(preview, *placement)
    preview.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
    preview.save(OUT / f"{filename}_预览.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mask = logo_mask()
    chinese = make_asset("游味烧鸟", mask, (0, 0, 1070, 255))
    english = make_asset("YOUWEI YAKITORI", mask, (100, 255, 970, 350))
    slogan = make_asset("后湖有风·味在人间", mask, (130, 345, 930, 455))
    # Split only on the four true zero-ink gutters so detached brush strokes are
    # retained while neighboring-character fragments are never duplicated.
    you = make_asset("游", mask, (0, 0, 312, 255))
    wei = make_asset("味", mask, (312, 0, 568, 255))
    shao = make_asset("烧", mask, (568, 0, 816, 255))
    niao = make_asset("鸟", mask, (816, 0, 1070, 255))

    write_variant(
        "01_横版标准组合_门头菜单",
        1200,
        470,
        [
            (chinese, 65, 35, 1070, 245),
            (english, 230, 285, 740, 82),
            (slogan, 350, 380, 500, 48),
        ],
    )
    write_variant(
        "02_方形组合_包装社交媒体",
        1000,
        1000,
        [
            (you, 150, 110, 330, 300),
            (wei, 520, 110, 330, 300),
            (shao, 150, 405, 330, 300),
            (niao, 520, 405, 330, 300),
            (english, 150, 760, 700, 80),
            (slogan, 245, 865, 510, 50),
        ],
    )
    write_variant(
        "03_圆章组合_灯箱杯垫贴纸",
        1000,
        1000,
        [
            (you, 220, 175, 255, 245),
            (wei, 525, 175, 255, 245),
            (shao, 220, 420, 255, 245),
            (niao, 525, 420, 255, 245),
            (english, 205, 720, 590, 70),
            (slogan, 300, 815, 400, 42),
        ],
        circles=[(500, 500, 450, 18), (500, 500, 420, 4)],
    )
    write_variant(
        "04_竖式组合_灯笼门帘侧招",
        520,
        1380,
        [
            (you, 130, 55, 260, 250),
            (wei, 130, 310, 260, 250),
            (shao, 130, 565, 260, 250),
            (niao, 130, 820, 260, 250),
            (english, 55, 1130, 410, 62),
            (slogan, 80, 1235, 360, 45),
        ],
    )
    write_variant(
        "05_游字图形_头像印章小尺寸",
        800,
        800,
        [(you, 165, 155, 470, 445)],
        circles=[(400, 400, 345, 22), (400, 400, 315, 5)],
    )
    print(f"created 5 SVG logo variants and previews in: {OUT}")


if __name__ == "__main__":
    main()
