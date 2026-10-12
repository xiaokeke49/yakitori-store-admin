"""Build labelled review sheets from already-downloaded Drive originals."""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / '99_系统临时区/drive-material-organizer'
STATE = ROOT / 'output/GoogleDrive素材整理/state.json'

def main():
    state = json.loads(STATE.read_text())
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    photos = []
    for index, (fid, record) in enumerate(state['files'].items()):
        ext = Path(record['title']).suffix.lower()
        source = CACHE / (fid + ext)
        if not source.exists() or source.stat().st_size != int(record['size']):
            continue
        if record['mime_type'].startswith('image/'):
            with Image.open(source) as original:
                photos.append((index, record['title'], ImageOps.exif_transpose(original).convert('RGB').copy()))
            continue
        reader = imageio_ffmpeg.read_frames(str(source))
        meta = next(reader)
        reader.close()
        duration = meta['duration']
        times = [min(duration * fraction, max(0, duration - 0.15)) for fraction in [0, .25, .5, .75, .95]]
        canvas = Image.new('RGB', (1500, 620), '#171717')
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 8), f'{index}: {record["title"]}  duration={duration:.2f}s', fill='white')
        for k, seconds in enumerate(times):
            frame = CACHE / f'{fid}-frame-{k}.jpg'
            subprocess.run([ffmpeg, '-v', 'error', '-ss', str(seconds), '-i', str(source), '-frames:v', '1', '-q:v', '3', '-y', str(frame)], check=True, timeout=60)
            with Image.open(frame) as img:
                img = ImageOps.contain(img.convert('RGB'), (290, 550))
                canvas.paste(img, (k * 300 + (300-img.width)//2, 40))
            draw.text((k*300+10, 590), f'{seconds:.2f}s', fill='white')
        canvas.save(CACHE / f'video-{index:02d}.jpg')
        record['duration_seconds'] = duration
        record['sample_times_seconds'] = times
        record['local_cache'] = str(source)
    for start in range(0, len(photos), 6):
        subset = photos[start:start+6]
        canvas = Image.new('RGB', (1500, 1100), '#171717')
        draw = ImageDraw.Draw(canvas)
        for k, (index, name, img) in enumerate(subset):
            x, y = (k % 3)*500, (k//3)*550
            img = ImageOps.contain(img, (490, 510))
            canvas.paste(img, (x+(500-img.width)//2, y+30))
            draw.text((x+8, y+8), f'{index}: {name}', fill='white')
        canvas.save(CACHE / f'photos-{start//6:02d}.jpg')
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    temp.replace(STATE)
    print(f'Prepared {len(photos)} image previews and cached video review sheets.')

if __name__ == '__main__':
    main()
