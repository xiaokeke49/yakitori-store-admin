import ctypes
import json
import math
import os
from pathlib import Path


SKP_PATH = Path(r"D:\桌面\改造方案.skp")
OUT_DIR = Path(r"C:\Users\admin\Documents\Codex\2026-08-06\referenced-chatgpt-conversation-this-is-an\outputs\后湖山野屋_游味烧鸟_项目交付包\05_施工参考\SketchUp模型分析")
DLL_DIR = Path(r"D:\SketchUtudio2023")
INCH_TO_CM = 2.54


class SURef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class SUPoint3D(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class SUBoundingBox3D(ctypes.Structure):
    _fields_ = [("min_point", SUPoint3D), ("max_point", SUPoint3D)]


class SUTransformation(ctypes.Structure):
    _fields_ = [("values", ctypes.c_double * 16)]


def identity():
    return [1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0]


def multiply(a, b):
    # SketchUp transformations use OpenGL-style column-major matrices.
    result = [0.0] * 16
    for col in range(4):
        for row in range(4):
            result[col * 4 + row] = sum(
                a[k * 4 + row] * b[col * 4 + k] for k in range(4)
            )
    return result


def transform_point(m, p):
    x, y, z = p
    return (
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    )


def bbox_corners(box):
    lo, hi = box[0], box[1]
    return [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]


def transform_bbox(box, m):
    pts = [transform_point(m, p) for p in bbox_corners(box)]
    return (
        tuple(min(p[i] for p in pts) for i in range(3)),
        tuple(max(p[i] for p in pts) for i in range(3)),
    )


def cm(v):
    return round(v * INCH_TO_CM, 2)


def bbox_record(box):
    lo, hi = box
    return {
        "min_cm": [cm(v) for v in lo],
        "max_cm": [cm(v) for v in hi],
        "size_cm": [cm(hi[i] - lo[i]) for i in range(3)],
        "center_cm": [cm((lo[i] + hi[i]) / 2.0) for i in range(3)],
    }


os.add_dll_directory(str(DLL_DIR))
dll = ctypes.WinDLL(str(DLL_DIR / "SketchUpAPI.dll"))


def setup(name, argtypes, restype=ctypes.c_int):
    fn = getattr(dll, name)
    fn.argtypes = argtypes
    fn.restype = restype
    return fn


SUInitialize = setup("SUInitialize", [], None)
SUTerminate = setup("SUTerminate", [], None)
SUModelCreateFromFile = setup("SUModelCreateFromFile", [ctypes.POINTER(SURef), ctypes.c_char_p])
SUModelRelease = setup("SUModelRelease", [ctypes.POINTER(SURef)])
SUModelGetEntities = setup("SUModelGetEntities", [SURef, ctypes.POINTER(SURef)])
SUEntitiesGetBoundingBox = setup("SUEntitiesGetBoundingBox", [SURef, ctypes.POINTER(SUBoundingBox3D)])

SUEntitiesGetNumGroups = setup("SUEntitiesGetNumGroups", [SURef, ctypes.POINTER(ctypes.c_size_t)])
SUEntitiesGetGroups = setup("SUEntitiesGetGroups", [SURef, ctypes.c_size_t, ctypes.POINTER(SURef), ctypes.POINTER(ctypes.c_size_t)])
SUEntitiesGetNumInstances = setup("SUEntitiesGetNumInstances", [SURef, ctypes.POINTER(ctypes.c_size_t)])
SUEntitiesGetInstances = setup("SUEntitiesGetInstances", [SURef, ctypes.c_size_t, ctypes.POINTER(SURef), ctypes.POINTER(ctypes.c_size_t)])
SUEntitiesGetNumFaces = setup("SUEntitiesGetNumFaces", [SURef, ctypes.POINTER(ctypes.c_size_t)])
SUEntitiesGetNumEdges = setup("SUEntitiesGetNumEdges", [SURef, ctypes.POINTER(ctypes.c_size_t)])
SUEntitiesGetFaces = setup("SUEntitiesGetFaces", [SURef, ctypes.c_size_t, ctypes.POINTER(SURef), ctypes.POINTER(ctypes.c_size_t)])
SUFaceGetNumVertices = setup("SUFaceGetNumVertices", [SURef, ctypes.POINTER(ctypes.c_size_t)])
SUFaceGetVertices = setup("SUFaceGetVertices", [SURef, ctypes.c_size_t, ctypes.POINTER(SURef), ctypes.POINTER(ctypes.c_size_t)])
SUVertexGetPosition = setup("SUVertexGetPosition", [SURef, ctypes.POINTER(SUPoint3D)])

SUGroupGetEntities = setup("SUGroupGetEntities", [SURef, ctypes.POINTER(SURef)])
SUGroupGetTransform = setup("SUGroupGetTransform", [SURef, ctypes.POINTER(SUTransformation)])
SUGroupGetName = setup("SUGroupGetName", [SURef, ctypes.POINTER(SURef)])

SUComponentInstanceGetDefinition = setup("SUComponentInstanceGetDefinition", [SURef, ctypes.POINTER(SURef)])
SUComponentInstanceGetTransform = setup("SUComponentInstanceGetTransform", [SURef, ctypes.POINTER(SUTransformation)])
SUComponentInstanceGetName = setup("SUComponentInstanceGetName", [SURef, ctypes.POINTER(SURef)])
SUComponentDefinitionGetEntities = setup("SUComponentDefinitionGetEntities", [SURef, ctypes.POINTER(SURef)])
SUComponentDefinitionGetName = setup("SUComponentDefinitionGetName", [SURef, ctypes.POINTER(SURef)])

SUStringCreate = setup("SUStringCreate", [ctypes.POINTER(SURef)])
SUStringRelease = setup("SUStringRelease", [ctypes.POINTER(SURef)])
SUStringGetUTF8Length = setup("SUStringGetUTF8Length", [SURef, ctypes.POINTER(ctypes.c_size_t)])
SUStringGetUTF8 = setup("SUStringGetUTF8", [SURef, ctypes.c_size_t, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)])


def check(code, where, allow=()):
    if code != 0 and code not in allow:
        raise RuntimeError(f"{where} failed with SUResult={code}")
    return code


def get_name(ref, fn):
    s = SURef()
    check(SUStringCreate(ctypes.byref(s)), "SUStringCreate")
    try:
        result = fn(ref, ctypes.byref(s))
        if result != 0:
            return ""
        length = ctypes.c_size_t()
        check(SUStringGetUTF8Length(s, ctypes.byref(length)), "SUStringGetUTF8Length")
        buf = ctypes.create_string_buffer(length.value + 1)
        copied = ctypes.c_size_t()
        check(SUStringGetUTF8(s, len(buf), buf, ctypes.byref(copied)), "SUStringGetUTF8")
        return buf.value.decode("utf-8", errors="replace")
    finally:
        SUStringRelease(ctypes.byref(s))


def get_bbox(entities):
    raw = SUBoundingBox3D()
    result = SUEntitiesGetBoundingBox(entities, ctypes.byref(raw))
    if result != 0:
        return None
    vals = [raw.min_point.x, raw.min_point.y, raw.min_point.z,
            raw.max_point.x, raw.max_point.y, raw.max_point.z]
    if not all(math.isfinite(v) for v in vals):
        return None
    return ((raw.min_point.x, raw.min_point.y, raw.min_point.z),
            (raw.max_point.x, raw.max_point.y, raw.max_point.z))


def get_transform(ref, fn):
    t = SUTransformation()
    if fn(ref, ctypes.byref(t)) != 0:
        return identity()
    return list(t.values)


def count(entities, fn):
    n = ctypes.c_size_t()
    if fn(entities, ctypes.byref(n)) != 0:
        return 0
    return n.value


def get_refs(entities, count_fn, get_fn):
    n = count(entities, count_fn)
    if not n:
        return []
    array = (SURef * n)()
    written = ctypes.c_size_t()
    check(get_fn(entities, n, array, ctypes.byref(written)), get_fn.__name__)
    return list(array[:written.value])


records = []
polygons = []


def collect_faces(entities, world_t, path):
    faces = get_refs(entities, SUEntitiesGetNumFaces, SUEntitiesGetFaces)
    for face in faces:
        n = ctypes.c_size_t()
        if SUFaceGetNumVertices(face, ctypes.byref(n)) != 0 or n.value < 3:
            continue
        verts = (SURef * n.value)()
        written = ctypes.c_size_t()
        if SUFaceGetVertices(face, n.value, verts, ctypes.byref(written)) != 0:
            continue
        points = []
        for vertex in verts[:written.value]:
            p = SUPoint3D()
            if SUVertexGetPosition(vertex, ctypes.byref(p)) == 0:
                points.append(transform_point(world_t, (p.x, p.y, p.z)))
        if len(points) >= 3:
            polygons.append({"points": points, "path": "/".join(path)})


def walk_entities(entities, parent_transform, path, depth=0, definition_stack=None):
    if definition_stack is None:
        definition_stack = set()
    if depth > 12:
        return

    collect_faces(entities, parent_transform, path)

    groups = get_refs(entities, SUEntitiesGetNumGroups, SUEntitiesGetGroups)
    for index, group in enumerate(groups, 1):
        name = get_name(group, SUGroupGetName) or f"Group_{index}"
        local_t = get_transform(group, SUGroupGetTransform)
        world_t = multiply(parent_transform, local_t)
        child = SURef()
        if SUGroupGetEntities(group, ctypes.byref(child)) != 0:
            continue
        local_box = get_bbox(child)
        rec = {
            "type": "group", "depth": depth, "name": name,
            "path": "/".join(path + [name]),
            "counts": {
                "faces": count(child, SUEntitiesGetNumFaces),
                "edges": count(child, SUEntitiesGetNumEdges),
                "groups": count(child, SUEntitiesGetNumGroups),
                "instances": count(child, SUEntitiesGetNumInstances),
            },
        }
        if local_box:
            rec["bounds"] = bbox_record(transform_bbox(local_box, world_t))
        records.append(rec)
        walk_entities(child, world_t, path + [name], depth + 1, definition_stack)

    instances = get_refs(entities, SUEntitiesGetNumInstances, SUEntitiesGetInstances)
    for index, inst in enumerate(instances, 1):
        inst_name = get_name(inst, SUComponentInstanceGetName)
        definition = SURef()
        if SUComponentInstanceGetDefinition(inst, ctypes.byref(definition)) != 0:
            continue
        def_name = get_name(definition, SUComponentDefinitionGetName)
        name = inst_name or def_name or f"Component_{index}"
        local_t = get_transform(inst, SUComponentInstanceGetTransform)
        world_t = multiply(parent_transform, local_t)
        child = SURef()
        if SUComponentDefinitionGetEntities(definition, ctypes.byref(child)) != 0:
            continue
        local_box = get_bbox(child)
        rec = {
            "type": "component", "depth": depth, "name": name,
            "instance_name": inst_name, "definition_name": def_name,
            "path": "/".join(path + [name]),
            "counts": {
                "faces": count(child, SUEntitiesGetNumFaces),
                "edges": count(child, SUEntitiesGetNumEdges),
                "groups": count(child, SUEntitiesGetNumGroups),
                "instances": count(child, SUEntitiesGetNumInstances),
            },
        }
        if local_box:
            rec["bounds"] = bbox_record(transform_bbox(local_box, world_t))
        records.append(rec)
        key = int(definition.ptr or 0)
        if key not in definition_stack:
            walk_entities(child, world_t, path + [name], depth + 1, definition_stack | {key})


def write_svg_views(overall):
    if not overall:
        return

    def esc(value):
        return (str(value).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    views = [
        ("顶视图", 0, 1, "改造方案_模型线稿_顶视图.svg"),
        ("正视图", 0, 2, "改造方案_模型线稿_正视图.svg"),
        ("右视图", 1, 2, "改造方案_模型线稿_右视图.svg"),
    ]
    width, height, margin = 1600, 900, 70
    for title, ax, ay, filename in views:
        min_x, max_x = overall[0][ax], overall[1][ax]
        min_y, max_y = overall[0][ay], overall[1][ay]
        span_x = max(max_x - min_x, 1e-6)
        span_y = max(max_y - min_y, 1e-6)
        scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)

        def project(p):
            x = margin + (p[ax] - min_x) * scale
            y = height - margin - (p[ay] - min_y) * scale
            return x, y

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#f6f1e8"/>',
            f'<text x="{margin}" y="36" font-family="Microsoft YaHei, sans-serif" font-size="24" fill="#29251f">{title}｜单位：厘米</text>',
            '<g fill="rgba(143,111,72,0.055)" stroke="#66513a" stroke-width="1.1" vector-effect="non-scaling-stroke">',
        ]
        visible_polygons = [item for item in polygons if "KK4286" not in item["path"] and "Heather" not in item["path"]]
        for item in visible_polygons:
            coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in (project(p) for p in item["points"]))
            parts.append(f'<polygon points="{coords}"/>')
        parts.append('</g>')

        # Label the major named top-level blocks without hiding the geometry.
        parts.append('<g font-family="Microsoft YaHei, sans-serif" font-size="13" fill="#9b3f2f">')
        for rec in records:
            if rec.get("depth") != 0 or "bounds" not in rec:
                continue
            name = rec.get("name", "")
            if name.startswith("立柱") or name.startswith("横梁") or name.startswith("Box"):
                continue
            center_in = [v / INCH_TO_CM for v in rec["bounds"]["center_cm"]]
            x, y = project(center_in)
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#b94c37"/>')
            parts.append(f'<text x="{x + 6:.2f}" y="{y - 6:.2f}">{esc(name)}</text>')
        parts.append('</g>')

        overall_cm_x = cm(span_x)
        overall_cm_y = cm(span_y)
        parts.append(f'<text x="{margin}" y="{height - 22}" font-family="Microsoft YaHei, sans-serif" font-size="15" fill="#555">整体投影：{overall_cm_x:.2f} × {overall_cm_y:.2f} cm</text>')
        parts.append('</svg>')
        (OUT_DIR / filename).write_text("\n".join(parts), encoding="utf-8")


def write_png_views(overall):
    from PIL import Image, ImageDraw, ImageFont

    if not overall:
        return
    views = [
        ("顶视图", 0, 1, "改造方案_模型线稿_顶视图.png"),
        ("正视图", 0, 2, "改造方案_模型线稿_正视图.png"),
        ("右视图", 1, 2, "改造方案_模型线稿_右视图.png"),
    ]
    width, height, margin = 1600, 900, 70
    try:
        title_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 24)
        label_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 13)
    except OSError:
        title_font = label_font = ImageFont.load_default()
    visible = [item for item in polygons if "KK4286" not in item["path"] and "Heather" not in item["path"]]
    for title, ax, ay, filename in views:
        min_x, max_x = overall[0][ax], overall[1][ax]
        min_y, max_y = overall[0][ay], overall[1][ay]
        span_x = max(max_x - min_x, 1e-6)
        span_y = max(max_y - min_y, 1e-6)
        scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)

        def project(p):
            return (margin + (p[ax] - min_x) * scale,
                    height - margin - (p[ay] - min_y) * scale)

        image = Image.new("RGB", (width, height), "#f6f1e8")
        draw = ImageDraw.Draw(image)
        draw.text((margin, 22), f"{title}｜单位：厘米", font=title_font, fill="#29251f")
        for item in visible:
            pts = [project(p) for p in item["points"]]
            if len(pts) >= 3:
                draw.line(pts + [pts[0]], fill="#7a634a", width=1)
        for rec in records:
            if rec.get("depth") != 0 or "bounds" not in rec:
                continue
            name = rec.get("name", "")
            if name.startswith(("立柱", "横梁", "Box")):
                continue
            center_in = [v / INCH_TO_CM for v in rec["bounds"]["center_cm"]]
            x, y = project(center_in)
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#b94c37")
            draw.text((x + 6, y - 18), name, font=label_font, fill="#9b3f2f")
        draw.text((margin, height - 30), f"整体投影：{cm(span_x):.2f} × {cm(span_y):.2f} cm", font=label_font, fill="#555555")
        image.save(OUT_DIR / filename, quality=95)


def write_perspective_views():
    from PIL import Image, ImageDraw, ImageFont

    def sub(a, b):
        return tuple(a[i] - b[i] for i in range(3))

    def dot(a, b):
        return sum(a[i] * b[i] for i in range(3))

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    def normalize(v):
        length = math.sqrt(max(dot(v, v), 1e-12))
        return tuple(x / length for x in v)

    # Coordinates below are in centimeters and derive from the inspected SKP axes:
    # X = left/right, Y = road/front toward rear/lake, Z = height.
    cameras = [
        {
            "name": "沙发区机位",
            "file": "改造方案_SKP透视骨架_沙发区机位.png",
            "eye_cm": (650.0, -50.0, 185.0),
            "target_cm": (380.0, 370.0, 78.0),
            "fov": 66.0,
        },
        {
            "name": "坐在板前机位",
            "file": "改造方案_SKP透视骨架_坐在板前机位.png",
            "eye_cm": (680.0, 175.0, 155.0),
            "target_cm": (1055.0, 175.0, 95.0),
            "fov": 66.0,
        },
        {
            "name": "主视角机位",
            "file": "改造方案_SKP透视骨架_主视角机位.png",
            "eye_cm": (580.0, -850.0, 175.0),
            "target_cm": (580.0, 190.0, 105.0),
            "fov": 52.0,
        },
    ]
    width, height = 1800, 1100
    visible = [item for item in polygons if "KK4286" not in item["path"] and "Heather" not in item["path"]]
    try:
        title_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 25)
        note_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 16)
    except OSError:
        title_font = note_font = ImageFont.load_default()

    for camera in cameras:
        eye = tuple(v / INCH_TO_CM for v in camera["eye_cm"])
        target = tuple(v / INCH_TO_CM for v in camera["target_cm"])
        forward = normalize(sub(target, eye))
        right = normalize(cross(forward, (0.0, 0.0, 1.0)))
        up = normalize(cross(right, forward))
        focal = width / (2.0 * math.tan(math.radians(camera["fov"]) / 2.0))

        projected = []
        for item in visible:
            screen = []
            depths = []
            for point in item["points"]:
                rel = sub(point, eye)
                depth = dot(rel, forward)
                if depth <= 0.5:
                    screen = []
                    break
                sx = width / 2.0 + focal * dot(rel, right) / depth
                sy = height / 2.0 - focal * dot(rel, up) / depth
                screen.append((sx, sy))
                depths.append(depth)
            if len(screen) >= 3:
                projected.append((sum(depths) / len(depths), item["path"], screen, item["points"]))

        projected.sort(key=lambda row: row[0], reverse=True)
        image = Image.new("RGB", (width, height), "#eee6d8")
        draw = ImageDraw.Draw(image)
        light = normalize((-0.4, -0.7, 1.0))
        for _, path, screen, world_points in projected:
            if len(world_points) >= 3:
                normal = normalize(cross(sub(world_points[1], world_points[0]), sub(world_points[2], world_points[0])))
                shade = 0.68 + 0.28 * abs(dot(normal, light))
            else:
                shade = 0.8
            if "立柱" in path or "横梁" in path:
                base = (112, 78, 48)
            elif "吧台" in path:
                base = (151, 103, 61)
            elif "底座加树" in path:
                base = (151, 139, 113)
            else:
                base = (190, 165, 128)
            fill = tuple(max(0, min(255, int(channel * shade))) for channel in base)
            draw.polygon(screen, fill=fill, outline="#4f3b28")

        draw.rectangle((0, 0, width, 58), fill="#201a14")
        draw.text((24, 13), f"SKP真实透视骨架｜{camera['name']}｜单位：厘米", font=title_font, fill="#f2e4cc")
        note = f"摄影机 {camera['eye_cm']}  → 目标 {camera['target_cm']}｜仅使用改造方案.skp几何，不含AI重排"
        draw.rectangle((0, height - 42, width, height), fill="#201a14")
        draw.text((24, height - 32), note, font=note_font, fill="#ddc9aa")
        image.save(OUT_DIR / camera["file"], quality=95)


def analyze_root_connected_components():
    root_faces = [item["points"] for item in polygons if item["path"] == "Model"]
    parent = list(range(len(root_faces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    owners = {}
    for face_index, face in enumerate(root_faces):
        for point in face:
            key = tuple(round(v, 5) for v in point)
            if key in owners:
                union(face_index, owners[key])
            else:
                owners[key] = face_index

    groups = {}
    for face_index, face in enumerate(root_faces):
        groups.setdefault(find(face_index), []).extend(face)

    output = []
    for index, points in enumerate(groups.values(), 1):
        lo = tuple(min(p[axis] for p in points) for axis in range(3))
        hi = tuple(max(p[axis] for p in points) for axis in range(3))
        output.append({"id": index, "bounds": bbox_record((lo, hi))})
    output.sort(key=lambda item: math.prod(max(v, 0.01) for v in item["bounds"]["size_cm"]), reverse=True)
    return output


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model = SURef()
    SUInitialize()
    try:
        check(SUModelCreateFromFile(ctypes.byref(model), str(SKP_PATH).encode("utf-8")), "SUModelCreateFromFile")
        entities = SURef()
        check(SUModelGetEntities(model, ctypes.byref(entities)), "SUModelGetEntities")
        overall = get_bbox(entities)
        walk_entities(entities, identity(), ["Model"])
        report = {
            "source": str(SKP_PATH),
            "source_units": "Centimeter",
            "api_internal_units": "Inch",
            "overall_bounds": bbox_record(overall) if overall else None,
            "root_counts": {
                "faces": count(entities, SUEntitiesGetNumFaces),
                "edges": count(entities, SUEntitiesGetNumEdges),
                "groups": count(entities, SUEntitiesGetNumGroups),
                "instances": count(entities, SUEntitiesGetNumInstances),
            },
            "entity_records": records,
            "face_polygon_count": len(polygons),
            "root_connected_components": analyze_root_connected_components(),
        }
        out = OUT_DIR / "改造方案_几何分析_厘米.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        write_svg_views(overall)
        write_png_views(overall)
        write_perspective_views()
        print(json.dumps({
            "output": str(out),
            "overall_bounds": report["overall_bounds"],
            "root_counts": report["root_counts"],
            "records": len(records),
            "face_polygons": len(polygons),
        }, ensure_ascii=False, indent=2))
    finally:
        if model.ptr:
            SUModelRelease(ctypes.byref(model))
        SUTerminate()


if __name__ == "__main__":
    main()
