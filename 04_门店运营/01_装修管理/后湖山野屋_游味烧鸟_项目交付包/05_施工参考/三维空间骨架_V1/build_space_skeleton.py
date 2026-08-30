from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
MODEL = "游味烧鸟_固定空间骨架_V1"

MATERIALS = {
    "platform_low": (0.30, 0.22, 0.15),
    "platform_high": (0.38, 0.27, 0.17),
    "wood": (0.30, 0.18, 0.09),
    "wood_light": (0.58, 0.37, 0.18),
    "dark_wood": (0.15, 0.09, 0.055),
    "counter": (0.42, 0.26, 0.13),
    "sofa": (0.66, 0.59, 0.49),
    "rug": (0.42, 0.34, 0.25),
    "black": (0.08, 0.075, 0.07),
    "metal": (0.25, 0.28, 0.29),
    "glass": (0.36, 0.55, 0.62),
    "plant": (0.16, 0.30, 0.18),
    "lantern": (0.95, 0.72, 0.35),
    "wall": (0.32, 0.29, 0.25),
    "accent": (0.75, 0.32, 0.12),
}

objects: list[dict] = []


def box(name: str, center, size, material: str, category: str, note: str = ""):
    objects.append({
        "name": name, "kind": "box", "center": list(center), "size": list(size),
        "material": material, "category": category, "note": note,
    })


def cylinder(name: str, center, radius: float, height: float, material: str, category: str, note: str = ""):
    objects.append({
        "name": name, "kind": "cylinder", "center": list(center), "radius": radius,
        "height": height, "material": material, "category": category, "note": note,
    })


def sphere(name: str, center, radius: float, material: str, category: str, note: str = ""):
    objects.append({
        "name": name, "kind": "sphere", "center": list(center), "radius": radius,
        "material": material, "category": category, "note": note,
    })


def add_sofa_group(prefix: str, x: float):
    # 2.00 x 0.80 m rear sofa, two 0.60 m armchairs, one 1.00 m low table.
    box(f"{prefix}_rug", (x, 3.25, 0.43), (2.95, 1.65, 0.04), "rug", "furniture")
    box(f"{prefix}_sofa_seat", (x, 3.84, 0.70), (2.00, 0.72, 0.34), "sofa", "furniture")
    box(f"{prefix}_sofa_back", (x, 4.13, 1.00), (2.00, 0.16, 0.72), "sofa", "furniture")
    for side, sx in (("L", x - 1.20), ("R", x + 1.20)):
        box(f"{prefix}_armchair_{side}_seat", (sx, 3.05, 0.68), (0.60, 0.60, 0.32), "sofa", "furniture")
        box(f"{prefix}_armchair_{side}_back", (sx, 3.30, 0.95), (0.60, 0.12, 0.62), "sofa", "furniture")
    box(f"{prefix}_tea_table", (x, 2.82, 0.67), (1.00, 0.48, 0.30), "dark_wood", "furniture")


# ---------------------------------------------------------------------------
# Fixed coordinate system
# X: left/west -> right/east; Y: front/lake/visitor -> rear; Z: upward.
# Main dimensions are taken from the user's plan; provisional dimensions are
# clearly recorded in the manifest and the accompanying notes.
# ---------------------------------------------------------------------------

# Two-level deck: front 1.85 m deep, rear 2.60 m deep, 0.20 m level change.
box("front_platform", (5.30, 0.925, 0.10), (10.60, 1.85, 0.20), "platform_low", "architecture", "10.6m front body")
box("rear_platform", (5.85, 3.15, 0.20), (11.70, 2.60, 0.40), "platform_high", "architecture", "11.7m rear edge; top is 0.20m above front")
box("central_transition_step", (6.15, 1.78, 0.28), (2.10, 0.28, 0.16), "wood_light", "architecture")

# Rear and right wall backdrops; left side remains open to lake.
box("rear_lounge_wall", (4.25, 4.40, 1.58), (6.20, 0.10, 2.35), "wall", "architecture")
box("rear_kitchen_wall", (9.55, 4.40, 1.58), (4.10, 0.12, 2.35), "black", "architecture")
box("right_kitchen_wall", (11.64, 3.15, 1.55), (0.12, 2.50, 2.30), "black", "architecture")

# Continuous front/left planter and the fixed horizontal lounge bar.
box("left_front_planter", (2.60, 0.16, 0.28), (5.20, 0.32, 0.56), "plant", "landscape", "plan length from plan: 5.20m")
box("left_side_planter", (0.16, 1.55, 0.28), (0.32, 2.45, 0.56), "plant", "landscape")
box("horizontal_lake_bar", (2.80, 0.78, 0.65), (3.60, 0.30, 0.90), "wood_light", "counter", "MUST remain horizontal; 3.60 x 0.30m; provisional top 1.10m")
for i in range(5):
    box(f"lake_bar_stool_{i+1}", (1.60 + i * 0.60, 1.30, 0.48), (0.45, 0.45, 0.56), "dark_wood", "seating")

# Two fixed lounge groups on the rear raised platform.
add_sofa_group("left_lounge", 2.15)
add_sofa_group("central_lounge", 5.45)

# Central open entry aisle: marker is very low and can be hidden in viewer.
box("central_entry_aisle_marker", (6.25, 1.25, 0.205), (2.05, 2.50, 0.01), "accent", "guide", "Keep clear of fixed furniture")

# Board-front sequence from west/guest side to east/back wall.
box("boardfront_counter", (8.22, 2.45, 0.80), (0.55, 3.75, 0.80), "counter", "counter", "Longitudinal; never rotate to facade; provisional top 1.20m")
box("boardfront_service_ridge", (8.58, 2.45, 1.20), (0.18, 3.75, 0.08), "wood_light", "counter")
for i, y in enumerate((0.95, 1.68, 2.41, 3.14, 3.87), start=1):
    box(f"boardfront_guest_stool_{i}", (7.66, y, 0.56), (0.48, 0.48, 0.72), "dark_wood", "seating")

# 0.80m working aisle and 0.65m rear worktop.
box("kitchen_worktop", (10.08, 2.50, 0.88), (0.65, 3.80, 0.96), "dark_wood", "kitchen", "0.65m deep work zone")
box("yakitori_grill", (10.35, 3.55, 1.13), (0.70, 1.25, 0.34), "black", "kitchen")
box("sink", (10.13, 1.30, 1.05), (0.52, 0.70, 0.12), "metal", "kitchen")
box("rear_bottle_shelf", (10.85, 3.05, 1.82), (1.20, 2.55, 1.05), "dark_wood", "kitchen")

# Display case is independent and fixed at right-front.
box("display_fridge_base", (10.62, -0.45, 0.43), (2.00, 0.90, 0.86), "wood_light", "display", "2.00 x 0.90m; independent from kitchen worktop")
box("display_fridge_glass", (10.62, -0.45, 1.18), (1.90, 0.82, 0.72), "glass", "display")

# Structural posts.
post_x = (0.10, 3.35, 7.25, 11.60)
for px in post_x:
    for py in (0.10, 4.35):
        box(f"post_{px:.2f}_{py:.2f}", (px, py, 1.54), (0.16, 0.16, 2.70), "wood", "roof")

# Roof beams: main horizontal beams plus front-to-rear rafters.
for py in (0.12, 1.85, 4.35):
    box(f"main_beam_y_{py:.2f}", (5.85, py, 2.90), (11.70, 0.18, 0.22), "wood", "roof")
for i in range(18):
    px = 0.18 + i * (11.34 / 17)
    box(f"rafter_{i+1:02d}", (px, 2.23, 3.02), (0.10, 4.70, 0.12), "wood", "roof")

# Lanterns and planters provide stable visual anchors.
sphere("central_round_lantern", (5.45, 3.55, 2.15), 0.48, "lantern", "lighting")
for i, x in enumerate((0.85, 1.55, 2.25, 2.95, 4.10, 5.00), start=1):
    cylinder(f"left_paper_lantern_{i}", (x, 3.95, 2.15), 0.18, 0.48, "lantern", "lighting")
for x, y in ((0.55, 0.50), (4.95, 0.45), (6.95, 0.55), (7.05, 1.80), (11.45, 0.30)):
    cylinder(f"planter_{x:.2f}_{y:.2f}", (x, y, 0.45), 0.26, 0.50, "plant", "landscape")


CAMERAS = {
    "00_俯视校验": {"position": [5.85, 2.10, 15.5], "target": [5.85, 2.10, 0.0], "fov": 46},
    "01_正面主视角": {"position": [5.85, -9.5, 3.65], "target": [5.85, 2.15, 1.20], "fov": 54},
    "02_外部左前": {"position": [-4.2, -5.8, 3.4], "target": [5.0, 2.10, 1.25], "fov": 55},
    "03_外部右前": {"position": [16.5, -5.6, 3.5], "target": [6.6, 2.05, 1.20], "fov": 55},
    "04_中央步入": {"position": [6.25, -1.20, 1.65], "target": [5.70, 3.65, 1.15], "fov": 63},
    "05_左侧沙发区": {"position": [6.35, 0.35, 1.70], "target": [2.45, 3.25, 0.95], "fov": 66},
    "06_板前客席区": {"position": [6.35, 0.35, 1.72], "target": [10.00, 3.20, 1.18], "fov": 66},
    "07_后侧向湖": {"position": [9.20, 4.02, 1.88], "target": [1.00, 1.80, 1.05], "fov": 70},
    "08_轴测总览": {"position": [-4.8, -6.5, 8.5], "target": [5.85, 2.15, 0.85], "fov": 48},
}

ASSUMPTIONS = [
    "Authoritative: overall rear length 11.70m, front main length 10.60m, total depth 4.45m.",
    "Authoritative: front depth 1.85m, rear depth 2.60m, rear deck +0.20m.",
    "Authoritative: left horizontal bar 3.60 x 0.30m with five seats; planter 5.20 x 0.25m nominal.",
    "Authoritative: two rear sofas 2.00 x 0.80m; armchairs 0.60 x 0.60m; low tables about 1.00m.",
    "Authoritative: board-front run about 4.00m; operation aisle 0.80m; worktop depth 0.65m; display fridge 2.00 x 0.90m.",
    "Provisional: pavilion clear/roof heights, exact column grid and wall thickness are inferred from the V12 master and self-made 3D sketch.",
    "Provisional: exact X positions use the V12 visual proportions and must be adjusted after field measurement.",
]


def write_mtl():
    lines = []
    for name, rgb in MATERIALS.items():
        lines += [f"newmtl {name}", f"Kd {rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f}", "Ka 0.0500 0.0500 0.0500", "Ks 0.0800 0.0800 0.0800", "Ns 20.0", ""]
    (OUT / f"{MODEL}.mtl").write_text("\n".join(lines), encoding="utf-8")


def write_obj():
    lines = [f"mtllib {MODEL}.mtl", "s off"]
    vcount = 0

    def emit_box(o):
        nonlocal vcount
        cx, cy, cz = o["center"]
        sx, sy, sz = o["size"]
        x0, x1 = cx - sx/2, cx + sx/2
        y0, y1 = cy - sy/2, cy + sy/2
        z0, z1 = cz - sz/2, cz + sz/2
        verts = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        faces = [(1,2,3,4),(5,8,7,6),(1,5,6,2),(2,6,7,3),(3,7,8,4),(5,1,4,8)]
        lines.extend([f"v {x:.5f} {y:.5f} {z:.5f}" for x,y,z in verts])
        lines.extend(["f " + " ".join(str(vcount+i) for i in face) for face in faces])
        vcount += 8

    def emit_cylinder(o, segments=16):
        nonlocal vcount
        cx, cy, cz = o["center"]
        r, h = o["radius"], o["height"]
        z0, z1 = cz-h/2, cz+h/2
        verts = []
        for z in (z0, z1):
            for i in range(segments):
                a = 2*math.pi*i/segments
                verts.append((cx+r*math.cos(a), cy+r*math.sin(a), z))
        verts += [(cx,cy,z0),(cx,cy,z1)]
        lines.extend([f"v {x:.5f} {y:.5f} {z:.5f}" for x,y,z in verts])
        b = vcount
        for i in range(segments):
            j=(i+1)%segments
            lines.append(f"f {b+i+1} {b+j+1} {b+segments+j+1} {b+segments+i+1}")
            lines.append(f"f {b+2*segments+1} {b+j+1} {b+i+1}")
            lines.append(f"f {b+2*segments+2} {b+segments+i+1} {b+segments+j+1}")
        vcount += len(verts)

    def emit_sphere(o, segments=18, rings=9):
        nonlocal vcount
        cx, cy, cz = o["center"]
        r = o["radius"]
        verts=[]
        for j in range(rings+1):
            p=math.pi*j/rings
            for i in range(segments):
                a=2*math.pi*i/segments
                verts.append((cx+r*math.sin(p)*math.cos(a), cy+r*math.sin(p)*math.sin(a), cz+r*math.cos(p)))
        lines.extend([f"v {x:.5f} {y:.5f} {z:.5f}" for x,y,z in verts])
        b=vcount
        for j in range(rings):
            for i in range(segments):
                ni=(i+1)%segments
                a=b+j*segments+i+1; bb=b+j*segments+ni+1
                c=b+(j+1)*segments+ni+1; d=b+(j+1)*segments+i+1
                lines.append(f"f {a} {bb} {c} {d}")
        vcount += len(verts)

    for o in objects:
        safe = o["name"].replace(" ", "_")
        lines += [f"o {safe}", f"g {o['category']}_{safe}", f"usemtl {o['material']}"]
        if o["kind"] == "box": emit_box(o)
        elif o["kind"] == "cylinder": emit_cylinder(o)
        else: emit_sphere(o)
    (OUT / f"{MODEL}.obj").write_text("\n".join(lines)+"\n", encoding="utf-8")


def color255(material):
    return tuple(round(v*255) for v in MATERIALS[material])


def font(size):
    for p in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf"), Path("C:/Windows/Fonts/arial.ttf")):
        if p.exists(): return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def footprint(o):
    if o["kind"] == "box":
        cx,cy,_=o["center"]; sx,sy,_=o["size"]
        return cx-sx/2, cy-sy/2, cx+sx/2, cy+sy/2
    cx,cy,_=o["center"]; r=o["radius"]
    return cx-r,cy-r,cx+r,cy+r


def write_plan_png():
    W,H=1800,1000; margin=120; scale=125
    img=Image.new("RGB",(W,H),(245,241,233)); d=ImageDraw.Draw(img,"RGBA")
    def pt(x,y): return margin+x*scale, H-margin-y*scale
    order=["architecture","landscape","counter","kitchen","display","furniture","seating","lighting","roof","guide"]
    for cat in order:
        for o in objects:
            if o["category"]!=cat or (cat=="roof"): continue
            x0,y0,x1,y1=footprint(o); a=pt(x0,y0); b=pt(x1,y1)
            rect=(a[0],b[1],b[0],a[1]); col=color255(o["material"])+(190 if cat!="guide" else 65,)
            if o["kind"] in ("sphere","cylinder"): d.ellipse(rect,fill=col,outline=(40,40,35,220),width=2)
            else: d.rectangle(rect,fill=col,outline=(40,40,35,220),width=2)
    # Overall dimensions and main zone labels.
    d.text((70,35),"游味烧鸟｜固定三维空间骨架 V1｜俯视校验",font=font(34),fill=(35,32,29))
    labels=[
        ((2.65,0.65),"左侧横向吧台\n3.60×0.30m"),((2.2,3.5),"左侧沙发组"),
        ((5.45,3.5),"中央圆灯沙发组"),((6.25,1.15),"中央入口通道\n保持净空"),
        ((8.15,2.4),"板前客席\n纵深方向"),((10.15,2.6),"操作区/后墙"),((10.6,-0.45),"展示柜\n2.00×0.90m"),
    ]
    for (x,y),txt in labels:
        px,py=pt(x,y); d.multiline_text((px,py),txt,font=font(20),fill=(20,20,18),anchor="mm",align="center",spacing=3)
    # North/back and front/lake notation.
    d.text((W-330,35),"后侧 / Y+",font=font(22),fill=(55,55,50))
    d.text((W-400,H-70),"正面·湖面·游客视线 / Y−",font=font(22),fill=(55,55,50))
    img.save(OUT/"01_俯视空间关系校验.png")


def camera_basis(pos, target):
    f=[target[i]-pos[i] for i in range(3)]; fl=math.sqrt(sum(v*v for v in f)); f=[v/fl for v in f]
    # A pure top camera looks parallel to world Z, so it needs world Y as its
    # screen-up reference to avoid a zero-length cross product.
    up=[0,1,0] if abs(f[2]) > 0.98 else [0,0,1]
    r=[f[1]*up[2]-f[2]*up[1], f[2]*up[0]-f[0]*up[2], f[0]*up[1]-f[1]*up[0]]
    rl=math.sqrt(sum(v*v for v in r)); r=[v/rl for v in r]
    u=[r[1]*f[2]-r[2]*f[1], r[2]*f[0]-r[0]*f[2], r[0]*f[1]-r[1]*f[0]]
    return r,u,f


def box_corners(o):
    if o["kind"] != "box":
        r=o["radius"]; h=o.get("height",2*r); cx,cy,cz=o["center"]
        sx=sy=2*r; sz=h
    else: cx,cy,cz=o["center"]; sx,sy,sz=o["size"]
    return [(cx+dx*sx/2,cy+dy*sy/2,cz+dz*sz/2) for dx in (-1,1) for dy in (-1,1) for dz in (-1,1)]


FACES=((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3))


def render_preview(filename, camera_name):
    W,H=1800,1050; img=Image.new("RGB",(W,H),(232,231,226)); d=ImageDraw.Draw(img,"RGBA")
    cam=CAMERAS[camera_name]; pos=cam["position"]; target=cam["target"]; right,up,fwd=camera_basis(pos,target)
    focal=(W/2)/math.tan(math.radians(cam["fov"])/2)
    def project(p):
        q=[p[i]-pos[i] for i in range(3)]
        x=sum(q[i]*right[i] for i in range(3)); y=sum(q[i]*up[i] for i in range(3)); z=sum(q[i]*fwd[i] for i in range(3))
        if z<0.05:return None
        return (W/2+focal*x/z,H/2-focal*y/z,z)
    polys=[]
    for o in objects:
        if o["category"]=="guide": continue
        pts=box_corners(o); proj=[project(p) for p in pts]
        if any(p is None for p in proj): continue
        for face in FACES:
            poly=[(proj[i][0],proj[i][1]) for i in face]; depth=sum(proj[i][2] for i in face)/4
            polys.append((depth,poly,o["material"]))
    for _,poly,mat in sorted(polys,reverse=True):
        c=color255(mat); d.polygon(poly,fill=c+(215,),outline=(35,33,30,170))
    d.rectangle((0,0,W,70),fill=(248,245,238,235))
    d.text((40,16),f"游味烧鸟｜固定三维空间骨架 V1｜{camera_name}",font=font(30),fill=(30,28,26))
    img.save(OUT/filename)


def write_manifest():
    data={
        "model": MODEL,
        "units": "meters",
        "axes": {"x":"left/west to right/east","y":"front/lake/visitor to rear","z":"up"},
        "overall": {"rear_width":11.70,"front_main_width":10.60,"depth":4.45,"front_depth":1.85,"rear_depth":2.60,"level_difference":0.20},
        "materials": {k:list(v) for k,v in MATERIALS.items()},
        "objects": objects,
        "cameras": CAMERAS,
        "assumptions": ASSUMPTIONS,
    }
    (OUT/"空间骨架_参数与机位_V1.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    return data


def write_viewer(data):
    scene_json=json.dumps(data,ensure_ascii=False)
    html=r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>游味烧鸟｜固定三维空间骨架 V1</title><style>
*{box-sizing:border-box}body{margin:0;background:#171614;color:#ece6db;font-family:"Microsoft YaHei",sans-serif;overflow:hidden}#bar{position:fixed;left:0;right:0;top:0;height:72px;background:#24211ddd;border-bottom:1px solid #5e503f;display:flex;align-items:center;gap:12px;padding:10px 16px;z-index:3}h1{font-size:17px;margin:0 18px 0 0;white-space:nowrap}.controls{display:flex;gap:8px;flex-wrap:wrap}button{background:#39332c;color:#eee4d5;border:1px solid #6b5a47;border-radius:5px;padding:7px 10px;cursor:pointer}button:hover{background:#544536}#canvas{position:fixed;inset:72px 0 0 0;width:100%;height:calc(100% - 72px)}#side{position:fixed;right:15px;top:90px;width:250px;background:#211e1ad9;border:1px solid #5e503f;border-radius:8px;padding:12px;z-index:2;font-size:13px;line-height:1.6}label{display:block}#tip{position:fixed;left:15px;bottom:14px;background:#211e1ad9;padding:8px 12px;border-radius:6px;font-size:12px;color:#cfc3b1}.sw{display:inline-block;width:10px;height:10px;margin-right:6px}</style></head><body><div id="bar"><h1>游味烧鸟｜固定空间骨架 V1</h1><div class="controls" id="cams"></div></div><canvas id="canvas"></canvas><div id="side"><b>显示分类</b><div id="checks"></div><hr><div id="info">拖动旋转｜滚轮缩放<br>坐标：X 左→右，Y 前→后，Z 向上<br>单位：米</div></div><div id="tip">这是固定白模校验器，不是最终材质效果图。隐藏屋架后可检查内部布局。</div><script>
const SCENE=__SCENE__;const cv=document.getElementById('canvas'),ctx=cv.getContext('2d');let dpr=devicePixelRatio||1;let target=[5.85,2.15,1.1],az=-Math.PI/2,el=.28,dist=15,fov=55;const visible={};
function resize(){cv.width=cv.clientWidth*dpr;cv.height=cv.clientHeight*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);draw()}addEventListener('resize',resize);
const cats=[...new Set(SCENE.objects.map(o=>o.category))];cats.forEach(c=>{visible[c]=c!=='guide';let l=document.createElement('label');l.innerHTML=`<input type=checkbox ${visible[c]?'checked':''}> ${c}`;l.querySelector('input').onchange=e=>{visible[c]=e.target.checked;draw()};document.getElementById('checks').append(l)});
Object.entries(SCENE.cameras).forEach(([n,c])=>{let b=document.createElement('button');b.textContent=n;b.onclick=()=>setCamera(c);document.getElementById('cams').append(b)});
function sub(a,b){return a.map((v,i)=>v-b[i])}function dot(a,b){return a.reduce((s,v,i)=>s+v*b[i],0)}function cross(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]}function norm(a){let l=Math.hypot(...a);return a.map(v=>v/l)}
function setCamera(c){target=[...c.target];let q=sub(c.position,target);dist=Math.hypot(...q);az=Math.atan2(q[1],q[0]);el=Math.asin(q[2]/dist);fov=c.fov;draw()}
function camera(){let ce=Math.cos(el);return[target[0]+dist*ce*Math.cos(az),target[1]+dist*ce*Math.sin(az),target[2]+dist*Math.sin(el)]}
function corners(o){let sx,sy,sz,c=o.center;if(o.kind==='box'){[sx,sy,sz]=o.size}else{sx=sy=2*o.radius;sz=o.height||2*o.radius}let a=[];for(let x of[-1,1])for(let y of[-1,1])for(let z of[-1,1])a.push([c[0]+x*sx/2,c[1]+y*sy/2,c[2]+z*sz/2]);return a}
const faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];
function draw(){let W=cv.clientWidth,H=cv.clientHeight;ctx.clearRect(0,0,W,H);let g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#252a2d');g.addColorStop(1,'#171512');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);let pos=camera(),fw=norm(sub(target,pos)),rt=norm(cross(fw,[0,0,1])),up=cross(rt,fw),f=(W/2)/Math.tan(fov*Math.PI/360);function pr(p){let q=sub(p,pos),z=dot(q,fw);if(z<.05)return null;return[W/2+f*dot(q,rt)/z,H/2-f*dot(q,up)/z,z]}
let ps=[];for(let o of SCENE.objects){if(!visible[o.category])continue;let pp=corners(o).map(pr);if(pp.some(x=>!x))continue;for(let face of faces){let poly=face.map(i=>pp[i]),depth=poly.reduce((s,p)=>s+p[2],0)/4;ps.push({poly,depth,mat:o.material})}}ps.sort((a,b)=>b.depth-a.depth);for(let p of ps){let rgb=SCENE.materials[p.mat].map(x=>Math.round(x*255));ctx.beginPath();p.poly.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();ctx.fillStyle=`rgba(${rgb},.88)`;ctx.fill();ctx.strokeStyle='rgba(15,13,11,.55)';ctx.stroke()} }
let drag=false,lx=0,ly=0;cv.onpointerdown=e=>{drag=true;lx=e.clientX;ly=e.clientY;cv.setPointerCapture(e.pointerId)};cv.onpointermove=e=>{if(!drag)return;az-=(e.clientX-lx)*.008;el=Math.max(-1.45,Math.min(1.45,el+(e.clientY-ly)*.006));lx=e.clientX;ly=e.clientY;draw()};cv.onpointerup=()=>drag=false;cv.onwheel=e=>{e.preventDefault();dist=Math.max(3,Math.min(35,dist*Math.exp(e.deltaY*.001)));draw()};setCamera(SCENE.cameras['08_轴测总览']);resize();
</script></body></html>'''.replace('__SCENE__',scene_json)
    (OUT/"00_离线三维白模查看器.html").write_text(html,encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    write_mtl(); write_obj(); data=write_manifest(); write_viewer(data)
    write_plan_png()
    render_preview("02_轴测骨架校验.png","08_轴测总览")
    render_preview("03_正面骨架校验.png","01_正面主视角")
    render_preview("04_内部中央机位校验.png","04_中央步入")
    camera_dir = OUT / "固定机位白模"
    camera_dir.mkdir(exist_ok=True)
    for camera_name in CAMERAS:
        render_preview(f"固定机位白模/{camera_name}.png", camera_name)
    print(f"Generated {len(objects)} objects and {len(CAMERAS)} fixed cameras in {OUT}")
