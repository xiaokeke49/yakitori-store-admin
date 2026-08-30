import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


ROOT = Path.cwd()
OUT = ROOT / "03_VI视觉系统" / "05_最终空间融合版_V3" / "04_工厂生产文件"
manifest = json.loads((OUT / "production_manifest.json").read_text(encoding="utf-8"))

for item in manifest:
    png = ROOT / item["pngPath"]
    pdf = png.with_name(png.stem.replace("_高清", "_印刷稿") + ".pdf")
    page_size = (float(item["w"]) * mm, float(item["h"]) * mm)
    c = canvas.Canvas(str(pdf), pagesize=page_size, pageCompression=1)
    c.drawImage(str(png), 0, 0, width=page_size[0], height=page_size[1], preserveAspectRatio=False, mask="auto")
    c.showPage()
    c.save()
    item["pdfPath"] = str(pdf.relative_to(ROOT))

(OUT / "production_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# Visual QA contact sheet.
cols = 3
tile_w, tile_h, label_h, gap = 520, 360, 54, 24
rows = (len(manifest) + cols - 1) // cols
sheet = Image.new("RGB", (gap + cols * (tile_w + gap), gap + rows * (tile_h + label_h + gap)), "#181614")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)
    small = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
except OSError:
    font = small = ImageFont.load_default()

for i, item in enumerate(manifest):
    row, col = divmod(i, cols)
    x = gap + col * (tile_w + gap)
    y = gap + row * (tile_h + label_h + gap)
    im = Image.open(ROOT / item["pngPath"]).convert("RGB")
    im.thumbnail((tile_w, tile_h), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_w, tile_h), "#F3EEE5")
    tile.paste(im, ((tile_w - im.width) // 2, (tile_h - im.height) // 2))
    sheet.paste(tile, (x, y))
    draw.text((x, y + tile_h + 5), item["label"], font=font, fill="#E8D8BC")
    draw.text((x, y + tile_h + 31), f'{item["w"]} x {item["h"]} mm | {item["pxW"]} x {item["pxH"]} px', font=small, fill="#8A7764")

sheet.save(OUT / "00_全部生产文件缩略总览.jpg", quality=92)
print(f"exported {len(manifest)} PDFs and contact sheet")
