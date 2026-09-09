#!/usr/bin/env python3
"""Create a paired Live Photo from one image on macOS; never imports or publishes."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def default_output(source, digest):
    root = Path(__file__).resolve().parents[4]
    return root / '素材库' / 'Live图' / datetime.now().strftime('%Y-%m-%d') / f'{source.stem}_{digest[:12]}_v1'


def write_library_record(folder, source, report):
    """Keep the two original paired resources and provenance together."""
    names = ['Fridge_Live.JPG', 'Fridge_Live.mov']
    resources = []
    for name in names:
        path = folder / name
        resources.append({'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'bytes': path.stat().st_size})
    record = {'category': 'Live图', 'purpose': '制作候选',
              'asset_identifier': report['asset_identifier'],
              'source': str(source), 'source_sha256': report['source_sha256'],
              'resources': resources, 'preview': '推近效果预览.mp4',
              'verification': '验收/验证结果.json',
              'visual_review_required': True, 'published': False,
              'note': 'JPG与MOV为同一组Live；MP4仅预览，不可替代配对MOV。'}
    (folder / '素材信息.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('output', nargs='?', type=Path, help='可选的新目录；默认入顶层素材库/Live图/日期/，不覆盖已有版本')
    args = parser.parse_args()
    source = args.image.resolve()
    if sys.platform != 'darwin' or not shutil.which('swiftc'):
        parser.error('需要 macOS 和可用的 swiftc（Xcode Command Line Tools）。')
    if not source.is_file():
        parser.error('输入图片不存在。')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    output = args.output.resolve() if args.output else default_output(source, before)
    if output.exists():
        parser.error(f'输出目录已存在，未重复生成：{output}；需要新版本时显式指定新目录。')
    with tempfile.TemporaryDirectory(prefix='fridge-live-') as temp:
        temp = Path(temp)
        executable = temp / 'make_live'
        subprocess.run(['swiftc', str(Path(__file__).with_suffix('.swift')), '-o', str(executable)], check=True)
        rendered = temp / 'rendered'
        rendered.mkdir()
        subprocess.run([str(executable), str(source), str(rendered)], check=True, timeout=180)
        report = json.loads((rendered / '验证结果.json').read_text())
        if not report.get('pair_metadata_valid') or not report.get('photokit_recognized'):
            raise RuntimeError('Live Photo 配对或 PhotoKit 验证未通过，未交付成品。')
        if hashlib.sha256(source.read_bytes()).hexdigest() != before:
            raise RuntimeError('原图校验失败。')
        report.update(source_sha256=before, purpose='制作候选', generated_motion=True,
                      motion_method='静态图裁切推近与平移，无新增场景运动', visual_review_required=True)
        (rendered / '验证结果.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        checks = rendered / '验收'
        checks.mkdir()
        for name in ['验证结果.json', 'check_start.jpg', 'check_end.jpg']:
            (rendered / name).rename(checks / name)
        write_library_record(rendered, source, report)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(rendered), output)
    print(f'已生成并通过 PhotoKit 验证：{output}\n仍须目视验收与平台导入验证；未发布。')


if __name__ == '__main__':
    main()
