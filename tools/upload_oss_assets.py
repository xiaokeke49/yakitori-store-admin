#!/usr/bin/env python3
import argparse
import hashlib
import json
import mimetypes
import os
import posixpath
from datetime import datetime, timezone
from pathlib import Path

import oss2


MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".heic",
    ".heif",
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
}


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_media_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS:
            yield path


def normalize_object_key(prefix: str, relative_path: Path) -> str:
    rel = relative_path.as_posix()
    if prefix:
        return posixpath.join(prefix.strip("/"), rel)
    return rel


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload local media assets to Aliyun OSS.")
    parser.add_argument("--source", default="素材库", help="Local media source directory.")
    parser.add_argument("--prefix", default="原始素材/素材库", help="OSS object key prefix.")
    parser.add_argument("--manifest", default="assets_manifest.json", help="Manifest output path.")
    parser.add_argument("--dry-run", action="store_true", help="List files without uploading.")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    if not source.exists():
        raise SystemExit(f"Source directory not found: {source}")

    access_key_id = require_env("OSS_ACCESS_KEY_ID")
    access_key_secret = require_env("OSS_ACCESS_KEY_SECRET")
    bucket_name = require_env("OSS_BUCKET")
    endpoint = require_env("OSS_ENDPOINT")

    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    files = list(iter_media_files(source))
    print(f"Found {len(files)} media files under {source}")

    manifest = {
        "bucket": bucket_name,
        "endpoint": endpoint,
        "prefix": args.prefix.strip("/"),
        "source": str(source),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assets": [],
    }

    checkpoint_dir = Path(".oss-upload-checkpoints")
    checkpoint_dir.mkdir(exist_ok=True)

    for index, path in enumerate(files, start=1):
        relative_path = path.relative_to(source)
        object_key = normalize_object_key(args.prefix, relative_path)
        size = path.stat().st_size
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        print(f"[{index}/{len(files)}] {relative_path} -> oss://{bucket_name}/{object_key}")

        etag = None
        if not args.dry_run:
            headers = {"Content-Type": content_type}
            result = oss2.resumable_upload(
                bucket,
                object_key,
                str(path),
                headers=headers,
                multipart_threshold=16 * 1024 * 1024,
                part_size=8 * 1024 * 1024,
                store=oss2.ResumableStore(root=str(checkpoint_dir)),
            )
            etag = result.etag

        manifest["assets"].append(
            {
                "local_path": str(path),
                "relative_path": relative_path.as_posix(),
                "object_key": object_key,
                "oss_uri": f"oss://{bucket_name}/{object_key}",
                "size": size,
                "content_type": content_type,
                "sha256": sha256_file(path),
                "etag": etag,
            }
        )

    manifest_path = Path(args.manifest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest: {manifest_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
