#!/usr/bin/env python3
"""Build a local Mac GUI importer. Building does not read or modify Photos library."""
import argparse
import plistlib
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='构建Mac实况照片导入器；不会自动运行或导入相册')
    parser.add_argument('output', type=Path, help='新的.app输出路径（不得存在）')
    args = parser.parse_args()
    app = args.output.resolve()
    if app.suffix != '.app' or app.exists():
        parser.error('请选择尚不存在的.app输出路径')
    if not shutil.which('swiftc') or not shutil.which('codesign'):
        parser.error('需要Mac的Swift编译器和codesign')
    macos = app / 'Contents/MacOS'
    macos.mkdir(parents=True)
    info = {
        'CFBundleExecutable': 'LivePhotoImporter',
        'CFBundleIdentifier': 'local.yakitori.fridge.livephotoimporter',
        'CFBundleName': '冰箱实况导入器',
        'CFBundleDisplayName': '冰箱实况导入器',
        'CFBundlePackageType': 'APPL',
        'CFBundleVersion': '1',
        'CFBundleShortVersionString': '1.0',
        'LSMinimumSystemVersion': '12.0',
        'NSHighResolutionCapable': True,
        'NSPhotoLibraryUsageDescription': '将您选定的JPG和MOV作为一张实况照片导入，并仅回读导入项目验证LIVE及防止重复。',
        'NSPhotoLibraryAddUsageDescription': '将您选定的配对文件作为一张实况照片添加到图库。',
    }
    with (app / 'Contents/Info.plist').open('wb') as f:
        plistlib.dump(info, f)
    subprocess.run(['swiftc', '-suppress-warnings', str(Path(__file__).with_name('import_live.swift')), '-o', str(macos / 'LivePhotoImporter')], check=True)
    subprocess.run(['codesign', '--sign', '-', str(app)], check=True)
    print(app)


if __name__ == '__main__':
    main()
