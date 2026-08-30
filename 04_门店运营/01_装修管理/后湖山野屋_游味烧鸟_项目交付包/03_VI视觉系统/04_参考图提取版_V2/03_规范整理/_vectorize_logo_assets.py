from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "04_参考图提取版_V2" / "02_可用标志"
OUT = ROOT / "01_Logo文件_待放入"


def directed_boundary_edges(mask: np.ndarray):
    h, w = mask.shape
    outgoing: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def add(a, b):
        outgoing.setdefault(a, []).append(b)

    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if y == 0 or not mask[y - 1, x]:
            add((x, y), (x + 1, y))
        if x == w - 1 or not mask[y, x + 1]:
            add((x + 1, y), (x + 1, y + 1))
        if y == h - 1 or not mask[y + 1, x]:
            add((x + 1, y + 1), (x, y + 1))
        if x == 0 or not mask[y, x - 1]:
            add((x, y + 1), (x, y))
    return outgoing


def turn_rank(prev, cur, nxt):
    ax, ay = cur[0] - prev[0], cur[1] - prev[1]
    bx, by = nxt[0] - cur[0], nxt[1] - cur[1]
    angle = math.atan2(ax * by - ay * bx, ax * bx + ay * by)
    preferences = [math.pi / 2, 0.0, -math.pi / 2, math.pi, -math.pi]
    return min(abs(angle - target) for target in preferences)


def trace_loops(mask: np.ndarray):
    outgoing = directed_boundary_edges(mask)
    unused = {(a, b) for a, ends in outgoing.items() for b in ends}
    loops = []
    while unused:
        start_edge = next(iter(unused))
        start, cur = start_edge
        prev = start
        loop = [start, cur]
        unused.remove(start_edge)
        guard = 0
        while cur != start and guard < 2_000_000:
            candidates = [n for n in outgoing.get(cur, []) if (cur, n) in unused]
            if not candidates:
                break
            nxt = min(candidates, key=lambda n: turn_rank(prev, cur, n))
            unused.remove((cur, nxt))
            loop.append(nxt)
            prev, cur = cur, nxt
            guard += 1
        if len(loop) > 4 and loop[-1] == start:
            loops.append(loop[:-1])
    return loops


def perpendicular_distance(p, a, b):
    if a == b:
        return math.dist(p, a)
    x, y = p
    x1, y1 = a
    x2, y2 = b
    return abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / math.hypot(y2 - y1, x2 - x1)


def rdp(points, epsilon):
    if len(points) <= 2:
        return points
    a, b = points[0], points[-1]
    distances = [perpendicular_distance(p, a, b) for p in points[1:-1]]
    if not distances:
        return points
    max_dist = max(distances)
    idx = distances.index(max_dist) + 1
    if max_dist > epsilon:
        left = rdp(points[: idx + 1], epsilon)
        right = rdp(points[idx:], epsilon)
        return left[:-1] + right
    return [a, b]


def simplify_closed(points, epsilon=1.1):
    if len(points) < 8:
        return points
    # Remove collinear grid points first.
    clean = []
    n = len(points)
    for i, p in enumerate(points):
        a = points[i - 1]
        b = points[(i + 1) % n]
        if (p[0] - a[0]) * (b[1] - p[1]) != (p[1] - a[1]) * (b[0] - p[0]):
            clean.append(p)
    if len(clean) < 6:
        return clean
    p0 = clean[0]
    split = max(range(1, len(clean)), key=lambda i: (clean[i][0] - p0[0]) ** 2 + (clean[i][1] - p0[1]) ** 2)
    first = rdp(clean[: split + 1], epsilon)
    second = rdp(clean[split:] + [clean[0]], epsilon)
    merged = first[:-1] + second[:-1]
    return merged if len(merged) >= 3 else clean


def polygon_area(points):
    return 0.5 * sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points)))


def fmt(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


def smooth_path(points):
    if len(points) < 3:
        return ""
    n = len(points)
    start = ((points[-1][0] + points[0][0]) / 2, (points[-1][1] + points[0][1]) / 2)
    parts = [f"M{fmt(start[0])},{fmt(start[1])}"]
    for i, p in enumerate(points):
        nxt = points[(i + 1) % n]
        mid = ((p[0] + nxt[0]) / 2, (p[1] + nxt[1]) / 2)
        parts.append(f"Q{fmt(p[0])},{fmt(p[1])} {fmt(mid[0])},{fmt(mid[1])}")
    parts.append("Z")
    return " ".join(parts)


def mask_to_path(mask, min_area=3.0, epsilon=1.1):
    loops = trace_loops(mask)
    paths = []
    for loop in loops:
        if abs(polygon_area(loop)) < min_area:
            continue
        simple = simplify_closed(loop, epsilon)
        if len(simple) >= 3:
            paths.append(smooth_path(simple))
    return " ".join(paths), len(paths)


def vectorize(source_name, output_name, main_fill, max_width=1200, epsilon=1.1):
    img = Image.open(SOURCE / source_name).convert("RGBA")
    if img.width > max_width:
        h = round(img.height * max_width / img.width)
        img = img.resize((max_width, h), Image.Resampling.LANCZOS)
    arr = np.asarray(img)
    alpha = arr[:, :, 3]
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    red = (alpha > 35) & (r > 75) & (r.astype(np.float32) > g * 1.18) & (r.astype(np.float32) > b * 1.18)
    main = (alpha > 85) & ~red

    # Median smoothing reduces extraction stair-steps before tracing.
    main = np.asarray(Image.fromarray((main * 255).astype("uint8")).filter(ImageFilter.MedianFilter(3))) > 127
    red = np.asarray(Image.fromarray((red * 255).astype("uint8")).filter(ImageFilter.MedianFilter(3))) > 127

    main_path, main_count = mask_to_path(main, min_area=2.5, epsilon=epsilon)
    red_path, red_count = mask_to_path(red, min_area=2.0, epsilon=max(0.8, epsilon - 0.2))

    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{img.width}" height="{img.height}" viewBox="0 0 {img.width} {img.height}">',
        '  <title>游味烧鸟 V2 矢量标志</title>',
        '  <desc>由确认的 V2 位图提取稿进行路径化描摹；所有识别元素均为可无限缩放的 SVG path。</desc>',
    ]
    if main_path:
        svg.append(f'  <path d="{main_path}" fill="{main_fill}" fill-rule="evenodd"/>')
    if red_path:
        svg.append(f'  <path d="{red_path}" fill="#B53A2F" fill-rule="evenodd"/>')
    svg.append('</svg>')
    target = OUT / output_name
    target.write_text("\n".join(svg), encoding="utf-8")
    print(f"{output_name}: {img.width}x{img.height}, main paths={main_count}, red paths={red_count}")


vectorize("01_圆章Logo_透明底.png", "01_V2_圆章Logo_矢量.svg", "#222220", max_width=900, epsilon=1.15)
vectorize("03_中文标准字_透明底.png", "02_V2_中文标准字_矢量.svg", "#222220", max_width=1200, epsilon=1.05)
vectorize("08_标准组合_清稿版_透明底.png", "03_V2_标准组合_矢量.svg", "#222220", max_width=1200, epsilon=1.1)
vectorize("04_竖排标志_反白透明底.png", "04_V2_竖排反白标志_矢量.svg", "#D7CABC", max_width=900, epsilon=1.05)
vectorize("05_红印章_透明底.png", "05_V2_红印章_矢量.svg", "#B53A2F", max_width=600, epsilon=0.9)
