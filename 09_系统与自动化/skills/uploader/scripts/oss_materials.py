#!/usr/bin/env python3
"""Idempotent, content-addressed Aliyun OSS media library."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import oss2
except ImportError:
    raise SystemExit("Missing dependency: run `python3 -m pip install oss2`")

MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".tif", ".tiff",
    ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a", ".aac", ".flac",
}
CATEGORIES = (
    "店内环境宣传", "后湖湖边茶饮", "后湖落日湖景", "烧烤成品特写",
    "烧烤烤制过程", "烧烤食材展示", "冰箱展示", "晚霞",
    "烧鸟烤串", "卖花素材", "生串", "Live图", "同行参考", "其他待判断",
)
CATEGORY_HINTS = {
    "Live图": ("Live图",),
    "同行参考": ("同行参考", "竞品参考", "对标账号"),
    "店内环境宣传": ("店内", "门店", "室内", "环境", "装修"),
    "后湖湖边茶饮": ("茶饮", "花束茶", "水果茶", "气泡水", "鸡尾酒"),
    "后湖落日湖景": ("落日", "日落", "湖景", "后湖"),
    "烧烤成品特写": ("成品", "特写", "烧鸟花", "烧鸟花束"),
    "烧烤烤制过程": ("烤制", "炭火", "撒料"),
    "烧烤食材展示": ("食材", "生鲜", "串制", "备料"),
    "冰箱展示": ("冰箱展示", "展示冰箱", "展示柜", "冷藏柜"),
    "晚霞": ("晚霞", "霞光", "彩霞"),
    "烧鸟烤串": ("烧鸟烤串", "烤串", "熟串", "串串成品"),
    "卖花素材": ("卖花素材", "卖花", "花童", "街头送花"),
    "生串": ("生串", "未烤串", "待烤串", "现串"),
}


def load_project_env() -> Path | None:
    """Load the nearest project .env without overriding exported variables."""
    candidates = []
    for start in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for directory in (start, *start.parents):
            if directory not in candidates:
                candidates.append(directory)
    env_path = next(
        (directory / ".env" for directory in candidates if (directory / ".git").exists() and (directory / ".env").is_file()),
        None,
    )
    if env_path is None:
        return None
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)
    return env_path


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing environment variable: {name}")
    return value


def bucket_from_env():
    auth = oss2.Auth(required_env("OSS_ACCESS_KEY_ID"), required_env("OSS_ACCESS_KEY_SECRET"))
    return oss2.Bucket(auth, required_env("OSS_ENDPOINT"), required_env("OSS_BUCKET"))


def prefix() -> str:
    return os.environ.get("OSS_PREFIX", "material-library/v1").strip("/")


def object_key(digest: str) -> str:
    return f"{prefix()}/objects/sha256/{digest[:2]}/{digest}"


def catalog_key(digest: str) -> str:
    return f"{prefix()}/catalog/{digest[:2]}/{digest}.json"


def batch_key(batch_id: str) -> str:
    return f"{prefix()}/batches/{batch_id}.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\s]+", "-", value.strip()).strip("-.")
    return cleaned[:60] or "未命名"


def media_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS)


def human_size(size: int) -> str:
    amount = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} TB"


def suggested_category(path: Path) -> str:
    if 'Live图' in path.parts:
        return 'Live图'  # 包装类型优先于原菜品关键词；新素材仍需审核。
    text = str(path).lower()
    matches = [category for category, hints in CATEGORY_HINTS.items() if any(hint.lower() in text for hint in hints)]
    return matches[0] if len(matches) == 1 else "其他待判断"


def get_json(bucket, key: str) -> dict | None:
    if not bucket.object_exists(key):
        return None
    return json.loads(bucket.get_object(key).read().decode("utf-8"))


def stable_batch_id(files: list[dict]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda value: (value["sha256"], value["relative_path"])):
        digest.update(item["sha256"].encode("ascii"))
        digest.update(item["relative_path"].encode("utf-8"))
    return digest.hexdigest()[:20]


def scan(args) -> int:
    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"Source directory not found: {source}")
    paths = media_files(source)
    if not paths:
        raise SystemExit(f"No supported media files found under: {source}")
    bucket = None if args.offline else bucket_from_env()
    files = []
    for index, path in enumerate(paths, 1):
        digest = sha256(path)
        catalog = get_json(bucket, catalog_key(digest)) if bucket else None
        files.append({
            "local_path": str(path),
            "relative_path": path.relative_to(source).as_posix(),
            "original_name": path.name,
            "size": path.stat().st_size,
            "content_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "sha256": digest,
            "remote_object": object_key(digest),
            "already_uploaded": catalog is not None,
            "category": catalog.get("category") if catalog else suggested_category(path),
            "reviewed": catalog is not None,
            "classification_source": "remote_catalog" if catalog else "path_suggestion_needs_visual_review",
        })
        print(f"[{index}/{len(paths)}] {'EXISTS' if catalog else 'NEW'} {path.relative_to(source)}")
    plan = {
        "schema_version": 3,
        "source_directory": str(source),
        "topic": args.topic or source.name,
        "shoot_date": args.date,
        "batch_id": stable_batch_id(files),
        "categories": list(CATEGORIES),
        "files": files,
    }
    output = Path(args.output or f"output/OSS素材库/上传计划/{safe_name(source.name)}-{plan['batch_id']}.json").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    existing = sum(item["already_uploaded"] for item in files)
    print(f"Plan: {output}")
    print(f"Total: {len(files)} files / {human_size(sum(item['size'] for item in files))}")
    print(f"Already uploaded: {existing}; new and needs classification: {len(files) - existing}")
    return 0


def load_plan(path: Path) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("schema_version") != 3:
        raise SystemExit("Unsupported plan schema; run scan again")
    for item in plan.get("files", []):
        if item.get("category") not in CATEGORIES:
            raise SystemExit(f"Unknown category: {item.get('category')}")
        if item.get("reviewed") is not True:
            raise SystemExit(f"Classification not reviewed: {item['relative_path']}")
        path = Path(item["local_path"])
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise SystemExit(f"File changed after scan; scan directory again: {path}")
    if stable_batch_id(plan["files"]) != plan.get("batch_id"):
        raise SystemExit("Plan batch_id is invalid; scan directory again")
    return plan


def upload(args) -> int:
    plan = load_plan(Path(args.plan).expanduser().resolve())
    new_items = [item for item in plan["files"] if not item["already_uploaded"]]
    counts = {category: sum(item["category"] == category for item in plan["files"]) for category in CATEGORIES}
    print(f"Batch: {plan['batch_id']}; files: {len(plan['files'])}; new: {len(new_items)}")
    print("Categories: " + ", ".join(f"{name} {count}" for name, count in counts.items() if count))
    if not args.execute:
        print("Preview only. Re-run with --execute after confirming this plan.")
        return 0
    bucket = bucket_from_env()
    uploaded = reused = 0
    for index, item in enumerate(plan["files"], 1):
        digest = item["sha256"]
        remote_catalog = get_json(bucket, catalog_key(digest))
        if remote_catalog:
            if remote_catalog.get("category") != item["category"]:
                raise SystemExit(f"Remote category conflict for {digest}: {remote_catalog.get('category')}")
            reused += 1
            print(f"[{index}/{len(plan['files'])}] REUSED {item['original_name']}", flush=True)
            continue
        local = Path(item["local_path"])
        if not bucket.object_exists(object_key(digest)):
            oss2.resumable_upload(bucket, object_key(digest), str(local), num_threads=4, headers={
                "Content-Type": item["content_type"], "x-oss-meta-sha256": digest,
                "x-oss-forbid-overwrite": "true",
            })
        catalog = {
            "schema_version": 1, "sha256": digest, "category": item["category"],
            "object_key": object_key(digest), "size": item["size"], "content_type": item["content_type"],
            "first_seen_name": item["original_name"], "created_at": datetime.now(timezone.utc).isoformat(),
        }
        bucket.put_object(
            catalog_key(digest), json.dumps(catalog, ensure_ascii=False, indent=2).encode("utf-8"),
            headers={"x-oss-forbid-overwrite": "true"},
        )
        uploaded += 1
        print(f"[{index}/{len(plan['files'])}] UPLOADED {item['original_name']}", flush=True)
    manifest = {
        "schema_version": 1, "batch_id": plan["batch_id"], "topic": plan["topic"],
        "shoot_date": plan.get("shoot_date"), "source_name": Path(plan["source_directory"]).name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "assets": [{key: item[key] for key in ("sha256", "relative_path", "original_name", "category", "remote_object")} for item in plan["files"]],
    }
    if not bucket.object_exists(batch_key(plan["batch_id"])):
        bucket.put_object(
            batch_key(plan["batch_id"]), json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            headers={"x-oss-forbid-overwrite": "true"},
        )
    print(f"Done: {uploaded} uploaded, {reused} reused; batch {plan['batch_id']}")
    return 0


def remote_batches(bucket) -> list[tuple[str, dict]]:
    found = []
    for item in oss2.ObjectIterator(bucket, prefix=f"{prefix()}/batches/"):
        if item.key.endswith(".json"):
            found.append((item.key, json.loads(bucket.get_object(item.key).read().decode("utf-8"))))
    return sorted(found, key=lambda item: (item[1].get("created_at", ""), item[1].get("batch_id", "")))


def remote_catalogs(bucket) -> list[dict]:
    found = []
    for item in oss2.ObjectIterator(bucket, prefix=f"{prefix()}/catalog/"):
        if item.key.endswith(".json"):
            found.append(json.loads(bucket.get_object(item.key).read().decode("utf-8")))
    return sorted(found, key=lambda item: (item.get("category", ""), item.get("first_seen_name", "")))


def inventory(args) -> int:
    bucket = bucket_from_env()
    catalogs = remote_catalogs(bucket)
    batches = remote_batches(bucket)
    appearances = {}
    for _, batch in batches:
        for asset in batch.get("assets", []):
            appearances.setdefault(asset["sha256"], {
                "relative_path": asset.get("relative_path") or asset.get("original_name"),
                "topic": batch.get("topic"),
                "shoot_date": batch.get("shoot_date"),
            })

    category_counts = {
        category: {
            "files": sum(item.get("category") == category for item in catalogs),
            "bytes": sum(int(item.get("size", 0)) for item in catalogs if item.get("category") == category),
        }
        for category in CATEGORIES
    }
    selected = catalogs
    if args.category:
        selected = [item for item in selected if item.get("category") == args.category]
    if args.search:
        needle = args.search.casefold()
        selected = [item for item in selected if needle in (
            str(item.get("first_seen_name", "")) + " "
            + str(appearances.get(item.get("sha256"), {}).get("relative_path", "")) + " "
            + str(item.get("category", ""))
        ).casefold()]

    result = {
        "unique_files": len(catalogs),
        "total_bytes": sum(int(item.get("size", 0)) for item in catalogs),
        "batches": len(batches),
        "categories": category_counts,
        "matched": [],
    }
    for item in selected[:args.limit if args.limit else None]:
        occurrence = appearances.get(item.get("sha256"), {})
        result["matched"].append({
            "name": item.get("first_seen_name"),
            "category": item.get("category"),
            "size": int(item.get("size", 0)),
            "sha256": item.get("sha256"),
            "relative_path": occurrence.get("relative_path"),
            "topic": occurrence.get("topic"),
            "shoot_date": occurrence.get("shoot_date"),
        })

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"OSS 素材库：{result['unique_files']} 个唯一素材 / {human_size(result['total_bytes'])} / {result['batches']} 个批次")
    print("分类：")
    for category, summary in category_counts.items():
        if summary["files"]:
            print(f"  {category}: {summary['files']} 个 / {human_size(summary['bytes'])}")
    if args.category or args.search:
        print(f"匹配：{len(selected)} 个")
        for item in result["matched"]:
            print(f"  [{item['category']}] {item['name']}  {human_size(item['size'])}")
            if item["relative_path"]:
                print(f"    {item['relative_path']}")
        if args.limit and len(selected) > args.limit:
            print(f"  ... 还有 {len(selected) - args.limit} 个，可提高 --limit")
    return 0


def list_batches(args) -> int:
    found = remote_batches(bucket_from_env())
    selected = found[-args.limit:] if args.limit else found
    for _, item in reversed(selected):
        print(f"{item.get('shoot_date') or '-'}  {item['topic']}  {len(item['assets'])} files  {item['batch_id']}")
    if not selected:
        print("No batches found.")
    return 0


def pull(args) -> int:
    bucket = bucket_from_env()
    destination = Path(args.destination).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    state_path = destination / ".oss-sync-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"seen_batches": []}
    seen = set(state.get("seen_batches", []))
    batches = remote_batches(bucket)
    selected = batches if args.all else ([item for item in batches if item[1]["batch_id"] not in seen] if seen else batches[-3:])
    downloaded = skipped = conflicts = 0
    for _, batch in selected:
        batch_folder = safe_name(batch.get("topic") or batch["batch_id"])
        date_folder = batch.get("shoot_date") or "日期未记录"
        for asset in batch["assets"]:
            relative = Path(asset["relative_path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise SystemExit(f"Unsafe remote relative path: {relative}")
            target = destination / asset["category"] / date_folder / batch_folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and sha256(target) == asset["sha256"]:
                skipped += 1
                continue
            if target.exists():
                target = target.with_name(f"{target.stem}.remote-{asset['sha256'][:8]}{target.suffix}")
                conflicts += 1
            bucket.get_object_to_file(asset["remote_object"], str(target))
            if sha256(target) != asset["sha256"]:
                target.unlink(missing_ok=True)
                raise SystemExit(f"Checksum mismatch: {asset['remote_object']}")
            downloaded += 1
        seen.add(batch["batch_id"])
    state["seen_batches"] = sorted(seen)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Done: {downloaded} downloaded, {skipped} unchanged, {conflicts} conflicts preserved.")
    return 0


def make_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Manage an idempotent, classified OSS media library.")
    commands = root.add_subparsers(dest="command", required=True)
    scan_cmd = commands.add_parser("scan", help="Hash a supplied directory and identify uploaded/new content.")
    scan_cmd.add_argument("--source", required=True)
    scan_cmd.add_argument("--topic")
    scan_cmd.add_argument("--date", default=date.today().isoformat())
    scan_cmd.add_argument("--output")
    scan_cmd.add_argument("--offline", action="store_true", help="Treat every file as new; only for local testing.")
    scan_cmd.set_defaults(handler=scan)
    upload_cmd = commands.add_parser("upload", help="Preview or upload a reviewed scan plan.")
    upload_cmd.add_argument("--plan", required=True)
    upload_cmd.add_argument("--execute", action="store_true")
    upload_cmd.set_defaults(handler=upload)
    list_cmd = commands.add_parser("list", help="List uploaded directory batches.")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.set_defaults(handler=list_batches)
    inventory_cmd = commands.add_parser("inventory", help="Show a read-only inventory of the OSS media library.")
    inventory_cmd.add_argument("--category", choices=CATEGORIES)
    inventory_cmd.add_argument("--search")
    inventory_cmd.add_argument("--limit", type=int, default=50)
    inventory_cmd.add_argument("--json", action="store_true")
    inventory_cmd.set_defaults(handler=inventory)
    pull_cmd = commands.add_parser("pull", help="Download unseen batches into classified folders.")
    pull_cmd.add_argument("--destination", default="output/OSS素材库/已同步素材")
    pull_cmd.add_argument("--all", action="store_true")
    pull_cmd.set_defaults(handler=pull)
    return root


def main() -> int:
    load_project_env()
    args = make_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
