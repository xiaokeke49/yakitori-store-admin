from pathlib import Path
from PIL import Image, ImageDraw
import sys

root = Path(sys.argv[1])
out = root / "contact_sheets"
out.mkdir(exist_ok=True)
pages = sorted(root.glob("doc_*/page-*.png"))
for batch_no, start in enumerate(range(0, len(pages), 4), 1):
    batch = pages[start:start + 4]
    loaded = [Image.open(p).convert("RGB") for p in batch]
    cell_w = max(im.width for im in loaded)
    cell_h = max(im.height for im in loaded) + 44
    sheet = Image.new("RGB", (cell_w * 2, cell_h * 2), "#D7DCE3")
    draw = ImageDraw.Draw(sheet)
    for idx, (path, im) in enumerate(zip(batch, loaded)):
        x = (idx % 2) * cell_w
        y = (idx // 2) * cell_h
        sheet.paste(im, (x, y + 44))
        draw.rectangle((x, y, x + cell_w, y + 43), fill="#1F2937")
        draw.text((x + 14, y + 12), f"{path.parent.name} / {path.name}", fill="white")
    sheet.save(out / f"sheet_{batch_no:02d}.jpg", quality=92, subsampling=0)
print(len(pages), len(list(out.glob('sheet_*.jpg'))))
