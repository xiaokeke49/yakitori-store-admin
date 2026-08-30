from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


root = Path(r"C:\Users\admin\Documents\Codex\2026-08-06\referenced-chatgpt-conversation-this-is-an\outputs\后湖山野屋_游味烧鸟_项目交付包")
folder = root / "02_空间效果图" / "01_最终效果图_待放入" / "10_新主母图_SKP同空间多视角初稿"
items = [
    ("01 左前外部视角", folder / "01_左前外部视角_v1.png"),
    ("02 右前外部视角", folder / "02_右前外部视角_v1.png"),
    ("03 左侧沙发区向右", folder / "03_左侧沙发区向右内部视角_v1.png"),
    ("04 板前客席区", folder / "04_板前客席区向左内部视角_v1.png"),
    ("05 坐在沙发上看湖（修正版）", folder / "05_坐在沙发上看湖_v2_统一木台与外侧两级台阶.png"),
    ("06 板前近景（修正版）", folder / "06_板前近景_v1_统一木台修正版.png"),
]

thumb_w, thumb_h = 760, 428
gap, label_h = 24, 42
canvas = Image.new("RGB", (gap * 3 + thumb_w * 2, gap * 4 + (thumb_h + label_h) * 3), "#17130f")
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 22)
except OSError:
    font = ImageFont.load_default()

for index, (label, path) in enumerate(items):
    row, col = divmod(index, 2)
    x = gap + col * (thumb_w + gap)
    y = gap + row * (thumb_h + label_h + gap)
    image = Image.open(path).convert("RGB")
    image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (thumb_w, thumb_h), "#000000")
    tile.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
    canvas.paste(tile, (x, y))
    draw.text((x, y + thumb_h + 8), label, font=font, fill="#ead8b9")

canvas.save(folder / "00_六视角初稿对照页_v2.jpg", quality=92)
