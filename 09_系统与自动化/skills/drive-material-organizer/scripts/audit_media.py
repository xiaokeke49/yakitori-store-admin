"""Non-destructive duplicate and technical-quality screening of cached originals."""
import argparse
import collections
import datetime
import hashlib
import itertools
import json
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[4]
STATE = ROOT / 'output/GoogleDrive素材整理/state.json'
CACHE = ROOT / '99_系统临时区/drive-material-organizer'

def save(state):
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    temporary.replace(STATE)

def fingerprint(image):
    grid = np.asarray(image.convert('L').resize((9, 8), Image.Resampling.LANCZOS))
    return int(''.join('1' if x else '0' for x in (grid[:, 1:] > grid[:, :-1]).ravel()), 2)

def metrics(image):
    image = image.convert('L').resize((256, 256), Image.Resampling.LANCZOS)
    a = np.asarray(image, dtype=np.float32)
    middle = a[1:-1, 1:-1]
    lap = -4 * middle + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return {'brightness': round(float(a.mean()), 2),
            'dark_fraction': round(float((a < 25).mean()), 4),
            'highlight_fraction': round(float((a > 250).mean()), 4),
            'edge_variance': round(float(lap.var()), 2)}

def main():
    args = argparse.ArgumentParser()
    args.add_argument('--manual', action='store_true')
    manual = args.parse_args().manual
    state = json.loads(STATE.read_text())
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    for fid, record in state['files'].items():
        now = datetime.datetime.now(ZoneInfo('Asia/Shanghai'))
        if not manual and not (6 <= now.hour < 10 and (now.hour < 9 or now.minute < 55)):
            save(state)
            print('Outside processing window; checkpoint saved.', flush=True)
            return
        path = CACHE / (fid + Path(record['original_title'] if record.get('original_title') else record['title']).suffix.lower())
        signature = str(record['size']) + ':' + str(record.get('version_fingerprint'))
        previous = record.get('technical_quality', {})
        if previous.get('status') == 'checked' and previous.get('source_signature') == signature and path.exists() and path.stat().st_size == int(record['size']):
            continue
        quality = {'checked_at': now.isoformat(), 'screening_only': True, 'source_signature': signature}
        record['technical_quality'] = quality
        try:
            if path.stat().st_size != int(record['size']):
                raise ValueError('Cached original size differs from Drive metadata')
            with path.open('rb') as stream:
                record['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
            if record['mime_type'].startswith('image/'):
                with Image.open(path) as original:
                    original.load()
                    original = ImageOps.exif_transpose(original)
                    quality.update(width=original.width, height=original.height, decode_ok=True,
                                   image_metrics=metrics(original), dhash=f'{fingerprint(original):016x}')
            else:
                reader = imageio_ffmpeg.read_frames(str(path))
                meta = next(reader)
                reader.close()
                quality.update(width=meta['size'][0], height=meta['size'][1],
                               fps=meta['fps'], duration_seconds=meta['duration'])
                checked = subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-i', str(path),
                                          '-f', 'null', '-'], capture_output=True, timeout=180)
                quality['full_decode_ok'] = checked.returncode == 0
                quality['decode_error'] = checked.stderr.decode(errors='replace')[-1500:] if checked.returncode else None
                frames = subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-i', str(path),
                                         '-vf', 'fps=4,scale=256:256', '-an', '-pix_fmt', 'gray',
                                         '-f', 'rawvideo', '-'], capture_output=True, check=True, timeout=180)
                raw = np.frombuffer(frames.stdout, dtype=np.uint8).reshape((-1, 256, 256))
                samples = []
                for index, frame in enumerate(raw):
                    img = Image.fromarray(frame)
                    samples.append({'approx_seconds': round(index / 4, 2),
                                    'dhash': f'{fingerprint(img):016x}', **metrics(img)})
                quality['sample_rate_fps'] = 4
                quality['sample_count'] = len(samples)
                quality['samples'] = samples
                quality['samples_do_not_prove_full_visual_or_audio_review'] = True
            quality['low_resolution_candidate'] = min(quality['width'], quality['height']) < 720
            quality['status'] = 'checked'
        except Exception as error:
            quality['status'] = 'failed'
            quality['error'] = f'{type(error).__name__}: {error}'
        save(state)
        print(record['category'] + '/' + record['title'] + ': ' + quality['status'], flush=True)
    hashes = collections.defaultdict(list)
    for fid, r in state['files'].items():
        if r.get('sha256') and r['technical_quality'].get('status') == 'checked':
            hashes[r['sha256']].append(fid)
    exact = [ids for ids in hashes.values() if len(ids) > 1]
    images = [(fid, r) for fid, r in state['files'].items() if r['technical_quality'].get('dhash')]
    similar = []
    for (aid, a), (bid, b) in itertools.combinations(images, 2):
        if a['category'] != b['category']:
            continue
        distance = (int(a['technical_quality']['dhash'], 16) ^ int(b['technical_quality']['dhash'], 16)).bit_count()
        if distance <= 10:
            similar.append({'ids': [aid, bid], 'dhash_distance': distance, 'type': 'similar_image_candidate'})
    videos = [(fid, r) for fid, r in state['files'].items() if r['technical_quality'].get('samples')]
    scenes = []
    for (aid, a), (bid, b) in itertools.combinations(videos, 2):
        if a['category'] != b['category']:
            continue
        ah = [int(f['dhash'], 16) for f in a['technical_quality']['samples']]
        bh = [int(f['dhash'], 16) for f in b['technical_quality']['samples']]
        am = float(np.median([min((x ^ y).bit_count() for y in bh) for x in ah]))
        bm = float(np.median([min((y ^ x).bit_count() for x in ah) for y in bh]))
        if max(am, bm) <= 12:
            scenes.append({'ids': [aid, bid], 'bidirectional_median_hash_distance': [am, bm],
                           'type': 'same_scene_candidate_not_duplicate_proof'})
    state.setdefault('quality_audit', {}).update({'checked_at': datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
                             'exact_duplicate_groups': exact, 'similar_image_pairs': similar,
                             'same_scene_video_pairs': scenes, 'deleted_files': 0,
                             'image_similarity_threshold': 10, 'video_scene_threshold': 12,
                             'quality_metrics_are_screening_not_rejection': True})
    save(state)
    print(json.dumps({k: len(state['quality_audit'][k]) for k in
                      ['exact_duplicate_groups', 'similar_image_pairs', 'same_scene_video_pairs']}))

if __name__ == '__main__':
    main()
