from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


SOURCE = Path(
    r"C:\Users\admin\.codex\generated_images\019fe53b-80be-7531-8645-8d65651bb593\exec-7b861c40-1a73-4f8a-80bb-20f3b4bbe35e.png"
)
TARGET = Path(__file__).with_name("07_V4_粗粝手作标准组合_无红印_矢量.svg")
PREVIEW = Path(__file__).with_name("07_V4_粗粝手作标准组合_无红印_矢量_预览.png")


def directed_boundary_edges(mask: np.ndarray):
    height, width = mask.shape
    outgoing: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def add(start, end):
        outgoing.setdefault(start, []).append(end)

    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if y == 0 or not mask[y - 1, x]:
            add((x, y), (x + 1, y))
        if x == width - 1 or not mask[y, x + 1]:
            add((x + 1, y), (x + 1, y + 1))
        if y == height - 1 or not mask[y + 1, x]:
            add((x + 1, y + 1), (x, y + 1))
        if x == 0 or not mask[y, x - 1]:
            add((x, y + 1), (x, y))
    return outgoing


def turn_rank(previous, current, following):
    ax, ay = current[0] - previous[0], current[1] - previous[1]
    bx, by = following[0] - current[0], following[1] - current[1]
    angle = math.atan2(ax * by - ay * bx, ax * bx + ay * by)
    preferences = [math.pi / 2, 0.0, -math.pi / 2, math.pi, -math.pi]
    return min(abs(angle - target) for target in preferences)


def trace_loops(mask: np.ndarray):
    outgoing = directed_boundary_edges(mask)
    unused = {(start, end) for start, ends in outgoing.items() for end in ends}
    loops = []
    while unused:
        start_edge = next(iter(unused))
        start, current = start_edge
        previous = start
        loop = [start, current]
        unused.remove(start_edge)
        guard = 0
        while current != start and guard < 2_000_000:
            candidates = [end for end in outgoing.get(current, []) if (current, end) in unused]
            if not candidates:
                break
            following = min(candidates, key=lambda end: turn_rank(previous, current, end))
            unused.remove((current, following))
            loop.append(following)
            previous, current = current, following
            guard += 1
        if len(loop) > 4 and loop[-1] == start:
            loops.append(loop[:-1])
    return loops


def perpendicular_distance(point, start, end):
    if start == end:
        return math.dist(point, start)
    x, y = point
    x1, y1 = start
    x2, y2 = end
    return abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / math.hypot(
        y2 - y1, x2 - x1
    )


def rdp(points, epsilon):
    if len(points) <= 2:
        return points
    distances = [perpendicular_distance(point, points[0], points[-1]) for point in points[1:-1]]
    if not distances:
        return points
    maximum = max(distances)
    index = distances.index(maximum) + 1
    if maximum > epsilon:
        left = rdp(points[: index + 1], epsilon)
        right = rdp(points[index:], epsilon)
        return left[:-1] + right
    return [points[0], points[-1]]


def simplify_closed(points, epsilon=1.05):
    if len(points) < 8:
        return points
    clean = []
    count = len(points)
    for index, point in enumerate(points):
        previous = points[index - 1]
        following = points[(index + 1) % count]
        if (point[0] - previous[0]) * (following[1] - point[1]) != (
            point[1] - previous[1]
        ) * (following[0] - point[0]):
            clean.append(point)
    if len(clean) < 6:
        return clean
    origin = clean[0]
    split = max(
        range(1, len(clean)),
        key=lambda index: (clean[index][0] - origin[0]) ** 2 + (clean[index][1] - origin[1]) ** 2,
    )
    first = rdp(clean[: split + 1], epsilon)
    second = rdp(clean[split:] + [clean[0]], epsilon)
    merged = first[:-1] + second[:-1]
    return merged if len(merged) >= 3 else clean


def polygon_area(points):
    return 0.5 * sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )


def fmt(number):
    return f"{number:.2f}".rstrip("0").rstrip(".")


def smooth_path(points):
    if len(points) < 3:
        return ""
    count = len(points)
    start = ((points[-1][0] + points[0][0]) / 2, (points[-1][1] + points[0][1]) / 2)
    parts = [f"M{fmt(start[0])},{fmt(start[1])}"]
    for index, point in enumerate(points):
        following = points[(index + 1) % count]
        midpoint = ((point[0] + following[0]) / 2, (point[1] + following[1]) / 2)
        parts.append(
            f"Q{fmt(point[0])},{fmt(point[1])} {fmt(midpoint[0])},{fmt(midpoint[1])}"
        )
    parts.append("Z")
    return " ".join(parts)


def main():
    image = Image.open(SOURCE).convert("RGB")
    # Crop to the three-line logo lockup and leave out the generated red seal.
    crop = image.crop((95, 430, 1165, 885))
    array = np.asarray(crop)
    red, green, blue = array[:, :, 0], array[:, :, 1], array[:, :, 2]
    grayscale = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    red_seal = (red > 105) & (red.astype(float) > green * 1.45) & (red.astype(float) > blue * 1.35)
    mask = (grayscale < 168) & ~red_seal
    mask = np.asarray(
        Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.MedianFilter(3))
    ) > 127

    path_parts = []
    loop_count = 0
    for loop in trace_loops(mask):
        if abs(polygon_area(loop)) < 4.0:
            continue
        simplified = simplify_closed(loop, epsilon=1.0)
        if len(simplified) >= 3:
            path_parts.append(smooth_path(simplified))
            loop_count += 1

    path_data = " ".join(path_parts)
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1070" height="455" viewBox="0 0 1070 455">
  <title>游味烧鸟 V4 粗粝手作标准组合</title>
  <desc>无红印版本。中文、英文与品牌标语均已转换为独立矢量轮廓，不依赖外部字体。</desc>
  <path d="{path_data}" fill="#20201E" fill-rule="evenodd"/>
</svg>
'''
    TARGET.write_text(svg, encoding="utf-8")
    preview = Image.new("RGB", crop.size, "#F4EFE5")
    preview_pixels = np.asarray(preview).copy()
    preview_pixels[mask] = np.array([32, 32, 30], dtype=np.uint8)
    Image.fromarray(preview_pixels).save(PREVIEW)
    print(f"created: {TARGET}")
    print(f"size: {crop.width}x{crop.height}; closed vector loops: {loop_count}")


if __name__ == "__main__":
    main()
