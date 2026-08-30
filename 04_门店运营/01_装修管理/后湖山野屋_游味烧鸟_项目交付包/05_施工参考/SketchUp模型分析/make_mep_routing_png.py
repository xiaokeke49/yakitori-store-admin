from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\admin\Documents\Codex\2026-08-06\referenced-chatgpt-conversation-this-is-an\outputs\后湖山野屋_游味烧鸟_项目交付包")
OUT = ROOT / "02_空间效果图" / "01_最终效果图_待放入" / "最终版" / "07_水电走线图_概念校验版_v3_板前插座与分区照明.png"

W, H = 2000, 1450
BG, INK, GRID = "#f6f1e8", "#26231f", "#ad9f8e"
WATER, DRAIN, POWER, LIGHT, WEAK = "#2477c9", "#248260", "#d35b34", "#d4a21d", "#7856a4"
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

font_path = r"C:\Windows\Fonts\msyh.ttc"
bold_path = r"C:\Windows\Fonts\msyhbd.ttc"
F_TITLE = ImageFont.truetype(bold_path, 42)
F_HEAD = ImageFont.truetype(bold_path, 25)
F = ImageFont.truetype(font_path, 21)
F_SMALL = ImageFont.truetype(font_path, 17)

OX, OY, S = 100, 115, 1.5
def P(x, y):
    return OX + x * S, OY + y * S

def rect(x1, y1, x2, y2, fill="#eee6da", outline=GRID, width=2):
    d.rectangle((*P(x1, y1), *P(x2, y2)), fill=fill, outline=outline, width=width)

def label(x, y, text, font=F, anchor="mm", fill=INK):
    d.text(P(x, y), text, font=font, fill=fill, anchor=anchor, stroke_width=3, stroke_fill=BG)

def route(points, color, width=7, dash=False):
    pts = [P(x, y) for x, y in points]
    if not dash:
        d.line(pts, fill=color, width=width, joint="curve")
    else:
        for a, b in zip(pts, pts[1:]):
            x1, y1 = a; x2, y2 = b
            length = ((x2-x1)**2 + (y2-y1)**2) ** .5
            if length == 0: continue
            ux, uy = (x2-x1)/length, (y2-y1)/length
            pos = 0
            while pos < length:
                end = min(pos + 14, length)
                d.line((x1+ux*pos, y1+uy*pos, x1+ux*end, y1+uy*end), fill=color, width=width)
                pos += 24

def point(x, y, code, color, dx=10, dy=-12):
    px, py = P(x, y)
    d.ellipse((px-8, py-8, px+8, py+8), fill=BG, outline=color, width=4)
    d.text((px+dx, py+dy), code, font=F_SMALL, fill=color, stroke_width=3, stroke_fill=BG)

d.text((100, 35), "游味烧鸟｜概念水电走线校验图", font=F_TITLE, fill=INK)
d.text((100, 88), "依据六视角效果图与 SketchUp 空间骨架绘制｜单位：cm｜非施工图", font=F, fill="#6e6459")

# Deck, two outside steps and road.
rect(0, 0, 1160, 490, fill="#f1e7d8", outline=INK, width=4)
rect(0, 490, 1160, 510, fill="#e3d5c1")
rect(0, 510, 1160, 530, fill="#d7c5ad")
rect(-20, 530, 1180, 585, fill="#c5b9a9", outline="#8f8375")
label(580, -25, "湖面 / 后侧", F_HEAD)
label(580, 548, "湿路面（两级台阶以下）", F_SMALL)

# Main zones.
rect(60, 25, 260, 108); label(160, 67, "左侧沙发", F_HEAD)
rect(400, 25, 600, 108); label(500, 67, "中央沙发", F_HEAD)
rect(75, 420, 406, 466); label(240, 443, "左前横向吧台", F_HEAD)
rect(745, 80, 807, 445); label(776, 260, "板前五席", F_HEAD)
rect(825, 60, 1110, 455); label(968, 250, "板前厨房 / 操作区", F_HEAD)
rect(940, 440, 1140, 490); label(1040, 465, "右前低展示柜", F_SMALL)
rect(420, 310, 690, 490); label(555, 400, "中央步入区", F_HEAD)

# Column grid.
for x in (52.5, 386.14, 728.14, 1093.97):
    d.line((*P(x, 0), *P(x, 490)), fill=GRID, width=2)
for y in (61.5, 297.5, 470.5):
    d.line((*P(0, y), *P(1160, y)), fill=GRID, width=2)
for x in (52.5, 386.14, 728.14, 1093.97):
    for y in (61.5, 297.5, 470.5):
        px, py = P(x, y); d.ellipse((px-6, py-6, px+6, py+6), fill=INK)

# Water supply.
route([(1140, 560), (1140, 55), (1040, 55)], WATER, 8)
route([(1110, 145), (1030, 145)], WATER, 5)
route([(1110, 255), (990, 255)], WATER, 5)
route([(1140, 450), (1040, 450)], WATER, 5)
route([(1040, 55), (240, 55), (240, 420)], WATER, 4, dash=True)
point(1040, 55, "S1 洗手盆", WATER)
point(1030, 145, "S2 清洗池", WATER)
point(990, 255, "S3 备餐水点", WATER)
point(1040, 450, "S4 冷凝水预留", WATER, -155, -25)
point(240, 420, "S5 左吧台预留", WATER, 12, -32)

# Drainage.
route([(1115, 55), (1115, 520), (1150, 520)], DRAIN, 8)
for x, y in ((1040, 68), (1030, 158), (990, 268), (1040, 463)):
    route([(x, y), (1115, y)], DRAIN, 5)
route([(240, 433), (610, 433), (610, 520), (1115, 520)], DRAIN, 4, dash=True)
rect(1075, 505, 1120, 535, fill=BG, outline=DRAIN, width=4); label(1098, 500, "GT 隔油池", F_SMALL, "ms", DRAIN)
point(960, 350, "FD1 地漏", DRAIN, -125, -25); route([(960, 350), (1115, 350)], DRAIN, 5)

# Power.
rect(1115, 15, 1150, 50, fill=BG, outline=POWER, width=4); label(1132, 5, "DB 配电箱", F_SMALL, "ms", POWER)
route([(1132, 50), (1132, 470)], POWER, 8)
for y, x, code in ((120, 1060, "P1 烤炉/排烟"), (220, 1020, "P2 冷藏操作台"), (330, 980, "P3 厨房插座"), (462, 1035, "P4 展示柜专线")):
    route([(1132, y), (x, y)], POWER, 5); point(x, y, code, POWER, -150, -28)
route([(1132, 390), (680, 390), (680, 455), (330, 455)], POWER, 5)
point(330, 455, "P5 左吧台插座", POWER, -155, 12)
# Rear-wall guest charging outlets: two groups per sofa, positioned near sofa ends.
route([(1132, 50), (1132, 12), (70, 12)], POWER, 5)
for x, code in ((78, "P6 客用充电"), (285, "P7 客用充电"), (415, "P8 客用充电"), (625, "P9 客用充电")):
    route([(x, 12), (x, 88)], POWER, 4)
    point(x, 88, code, POWER, 10, 8)
# High-level dedicated air-conditioner outlet at the innermost left sofa bay.
route([(1132, 24), (38, 24), (38, 48)], POWER, 5)
point(38, 48, "P10 空调专用插座（高位）", POWER, 12, -30)
# Two splash-resistant guest charging outlets below the five-seat board-front row.
route([(1132, 370), (835, 370), (835, 175), (790, 175)], POWER, 5)
route([(835, 370), (790, 370)], POWER, 5)
point(790, 175, "P11 板前座下插座", POWER, -205, -28)
point(790, 370, "P12 板前座下插座", POWER, -205, 10)

# Lighting scene controller and independent zone circuits.
rect(1040, 55, 1095, 92, fill=BG, outline=LIGHT, width=4)
label(1068, 48, "LC 场景控制", F_SMALL, "ms", LIGHT)
# L-L: left lounge, bar and planter ambient lighting.
route([(1068, 72), (80, 72), (80, 455), (400, 455)], LIGHT, 5)
# L-M: center sofa, paper globe and central circulation lighting.
route([(1068, 80), (700, 80), (700, 285), (410, 285)], LIGHT, 5)
# L-R-A: right guest-side ambient, sign and display lighting.
route([(1068, 88), (855, 88), (855, 450), (1060, 450)], LIGHT, 5)
# L-R-W: right kitchen task lighting, kept independent for preparation/closing.
route([(1068, 96), (890, 96), (890, 345), (1090, 345)], LIGHT, 5, dash=True)
for x, y in ((130, 140), (210, 140), (290, 140), (120, 455), (200, 455), (280, 455), (360, 455)):
    px, py = P(x, y); d.ellipse((px-8, py-8, px+8, py+8), fill=BG, outline=LIGHT, width=4)
for x, y in ((450, 140), (550, 140), (500, 340), (610, 340)):
    px, py = P(x, y); d.ellipse((px-8, py-8, px+8, py+8), fill=BG, outline=LIGHT, width=4)
for x, y in ((825, 155), (825, 270), (825, 410), (1030, 440)):
    px, py = P(x, y); d.ellipse((px-8, py-8, px+8, py+8), fill=BG, outline=LIGHT, width=4)
for x, y in ((930, 120), (1010, 120), (1090, 120), (970, 255), (1060, 255)):
    px, py = P(x, y); d.rectangle((px-8, py-8, px+8, py+8), fill=BG, outline=LIGHT, width=4)
label(210, 92, "L-L 左区：沙发/吧台/花坛", F_SMALL, fill=LIGHT)
label(545, 268, "L-M 中区：沙发/大纸灯/通道", F_SMALL, fill=LIGHT)
label(805, 430, "L-R-A 右区客席/招牌/展示柜", F_SMALL, "ms", LIGHT)
label(980, 238, "L-R-W 右区操作工作灯", F_SMALL, fill=LIGHT)

# Low voltage.
route([(1120, 50), (1120, 410), (1060, 410)], WEAK, 4, dash=True)
route([(1120, 380), (650, 380), (650, 445), (390, 445)], WEAK, 4, dash=True)
point(1060, 410, "POS", WEAK)
point(390, 445, "AP/POS", WEAK)

# Legend and notes.
legend_y = 1040
items = [(WATER, "给水"), (DRAIN, "排水"), (POWER, "强电"), (LIGHT, "照明"), (WEAK, "弱电/预留")]
for i, (color, text) in enumerate(items):
    x = 110 + i * 250
    d.line((x, legend_y, x+55, legend_y), fill=color, width=8)
    d.text((x+70, legend_y-15), text, font=F, fill=INK)
# Lighting scene matrix.
table_x, table_y = 100, 1090
d.text((table_x, table_y), "照明场景控制建议", font=F_HEAD, fill=INK)
cols = ["回路", "开店准备", "营业中", "打烊清洁"]
rows = [
    ("L-L 左区氛围", "关", "开", "关"),
    ("L-M 中区照明", "关", "开", "开"),
    ("L-R-A 右区客席氛围", "关", "开", "关"),
    ("L-R-W 右区操作工作灯", "开", "开", "开"),
    ("台阶/疏散安全灯", "开", "开", "开"),
]
cw = [410, 230, 230, 230]
cx = [table_x]
for width in cw: cx.append(cx[-1] + width)
top = table_y + 42
row_h = 42
for x in cx:
    d.line((x, top, x, top + row_h * (len(rows) + 1)), fill=GRID, width=2)
for i in range(len(rows) + 2):
    y = top + i * row_h
    d.line((cx[0], y, cx[-1], y), fill=GRID, width=2)
for i, text in enumerate(cols):
    d.text((cx[i] + 14, top + 8), text, font=F_SMALL, fill=INK)
for r, row in enumerate(rows, 1):
    for c, text in enumerate(row):
        color = DRAIN if text == "开" else "#7d746a"
        d.text((cx[c] + 14, top + r * row_h + 8), text, font=F_SMALL, fill=color if c else INK)
d.text((1320, 1135), "控制原则", font=F_HEAD, fill=INK)
d.text((1320, 1180), "准备中：仅开启右区操作工作灯和安全灯。", font=F_SMALL, fill=INK)
d.text((1320, 1220), "营业中：左、中、右区全部开启。", font=F_SMALL, fill=INK)
d.text((1320, 1260), "打烊清洁：中区通道 + 右区操作 + 安全灯。", font=F_SMALL, fill=INK)
d.text((1320, 1300), "建议使用场景面板，同时保留各回路手动开关。", font=F_SMALL, fill=INK)
d.text((100, 1390), "板前五席下设置2个带保护盖插座；沙发区4组客用充电插座；空调、冷柜、排烟均设专用回路。设备功率、线径及漏保参数需深化。", font=F, fill=INK)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, quality=95)
print(OUT)
