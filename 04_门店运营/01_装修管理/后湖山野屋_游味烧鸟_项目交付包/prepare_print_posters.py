from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "04_空间应用物料" / "11_饮品宣传海报"
OUTPUT = SOURCE / "60x90cm印刷版_300DPI"

TARGET = (7087, 10630)  # 60 x 90 cm at 300 DPI


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = min(size[0] / image.width, size[1] / image.height)
    return image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )


def prepare(source: Path, destination: Path) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGB")

    background = cover(image, TARGET)
    background = background.filter(ImageFilter.GaussianBlur(radius=95))
    background = ImageEnhance.Brightness(background).enhance(0.43)

    foreground = contain(image, TARGET)
    foreground = foreground.filter(
        ImageFilter.UnsharpMask(radius=1.6, percent=135, threshold=3)
    )

    left = (TARGET[0] - foreground.width) // 2
    top = (TARGET[1] - foreground.height) // 2
    background.paste(foreground, (left, top))

    destination.parent.mkdir(parents=True, exist_ok=True)
    background.save(
        destination,
        "JPEG",
        quality=96,
        subsampling=0,
        optimize=True,
        dpi=(300, 300),
    )


FILES = {
    "01_水果茶_满杯鲜橙_海报.png": "01_水果茶_满杯鲜橙_60x90cm_300DPI.jpg",
    "02_气泡水_话梅青桔_海报.png": "02_气泡水_话梅青桔_60x90cm_300DPI.jpg",
    "03_鸡尾酒_椰林飘香_海报.png": "03_鸡尾酒_椰林飘香_60x90cm_300DPI.jpg",
}

for source_name, output_name in FILES.items():
    prepare(SOURCE / source_name, OUTPUT / output_name)
    print(OUTPUT / output_name)
