#!/usr/bin/env python3
"""Download, extract, and validate RadioMapSeer."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen


FILE_ID = "1PTaPpLOKraVCRZU_Tzev4D5ZO32tpqMO"
DRIVE_URL = f"https://drive.google.com/uc?id={FILE_ID}"
MANUAL_URL = f"https://drive.google.com/file/d/{FILE_ID}/view"


def run_validate(dataset_dir: Path) -> int:
    cmd = [sys.executable, "scripts/validate_dataset.py", "--dataset-dir", str(dataset_dir)]
    return subprocess.call(cmd)


def download_with_gdown(output: Path) -> bool:
    try:
        import gdown  # type: ignore
    except Exception:
        return False

    print("使用 gdown 下载 RadioMapSeer...")
    gdown.download(DRIVE_URL, str(output), quiet=False, fuzzy=True)
    return output.exists() and output.stat().st_size > 1024 * 1024


def download_with_urllib(output: Path) -> bool:
    print("未检测到 gdown，尝试 urllib 直接下载。Google Drive 大文件可能需要手动下载。")
    try:
        with urlopen(DRIVE_URL, timeout=60) as response, output.open("wb") as f:
            shutil.copyfileobj(response, f)
    except Exception as exc:
        print(f"直接下载失败: {exc}")
        return False
    if output.stat().st_size < 1024 * 1024:
        print("下载文件过小，可能是 Google Drive 的确认页面，而不是数据集压缩包。")
        return False
    return True


def extract_archive(archive: Path, dataset_dir: Path) -> None:
    print(f"解压 {archive} -> {dataset_dir}")
    dataset_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(tmp_path)
        elif tarfile.is_tarfile(archive):
            with tarfile.open(archive) as tf:
                tf.extractall(tmp_path)
        else:
            raise RuntimeError(f"无法识别压缩包格式: {archive}")

        candidates = [p for p in tmp_path.iterdir() if p.is_dir()]
        source = None
        for candidate in candidates:
            if (candidate / "png").exists() and (candidate / "gain").exists():
                source = candidate
                break
        if source is None and (tmp_path / "png").exists() and (tmp_path / "gain").exists():
            source = tmp_path
        if source is None:
            raise RuntimeError("解压后没有找到包含 png/ 和 gain/ 的 RadioMapSeer 目录。")

        if dataset_dir.exists():
            shutil.rmtree(dataset_dir)
        shutil.copytree(source, dataset_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="RadioMapSeer/", help="RadioMapSeer 解压目标目录。")
    parser.add_argument("--archive", help="已下载的数据集压缩包路径。")
    parser.add_argument("--download-dir", default="downloads", help="自动下载压缩包保存目录。")
    parser.add_argument("--skip-download", action="store_true", help="只校验已有 dataset-dir。")
    parser.add_argument("--force", action="store_true", help="重新下载/解压并覆盖 dataset-dir。")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    if dataset_dir.exists() and not args.force:
        print(f"检测到已有数据集目录: {dataset_dir}")
        return run_validate(dataset_dir)

    if args.skip_download:
        print(f"跳过下载，但数据集目录不存在或 --force 被启用: {dataset_dir}")
        print(f"请手动下载 RadioMapSeer: {MANUAL_URL}")
        return 1

    archive = Path(args.archive) if args.archive else Path(args.download_dir) / "RadioMapSeer.zip"
    if not archive.exists() or args.force:
        archive.parent.mkdir(parents=True, exist_ok=True)
        ok = download_with_gdown(archive) or download_with_urllib(archive)
        if not ok:
            print("\n自动下载失败。请手动下载后重试：")
            print(f"  下载地址: {MANUAL_URL}")
            print(f"  目标压缩包: {archive}")
            print(f"  命令示例: {sys.executable} scripts/prepare_dataset.py --archive {archive}")
            return 1

    extract_archive(archive, dataset_dir)
    return run_validate(dataset_dir)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    raise SystemExit(main())

