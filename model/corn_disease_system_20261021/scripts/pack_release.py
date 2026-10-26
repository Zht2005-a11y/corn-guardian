"""把项目打包成可直接发给别人的压缩包。

设计要点：
1. 默认**不带**数据集、**不带** `last_*.pth`（断点续训用，收件人不需要），
   只保留三个 `best_*.pth` + 全部代码 + 评估报告 —— 约 200MB。
2. `--no-weights` 只打代码（约 2MB，邮件可发）；`--with-dataset` 连数据集一起打（约 450MB）。
3. 自动排除 `__pycache__` / `*.pyc` / `*.log` / `.workbuddy` / `dist` 等无关内容。
4. 打包时对 `configs/config.yaml` 做一份副本改写：把作者机器上的绝对路径改成包内相对路径
   （仅当 `--with-dataset` 时有意义），源文件不动。
5. 压缩包写到项目**外面**的 `D:/shape/dist/`，避免"自己压缩自己"。

用法：
    python -m scripts.pack_release                      # 默认：代码 + 三个权重 + 报告
    python -m scripts.pack_release --no-weights         # 只发代码，约 2MB
    python -m scripts.pack_release --with-dataset       # 连数据集，约 450MB
    python -m scripts.pack_release --out D:/我的目录     # 指定输出目录
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 逐项白名单：目录（整个纳入）与文件（单独纳入）
INCLUDE_DIRS = ["src", "app", "scripts", "configs"]
INCLUDE_FILES = ["README.md", "requirements.txt", "run_server.bat"]
REPORT_DIR = "outputs/reports"
CKPT_DIR = "outputs/checkpoints"
OPTIONAL_DIRS = ["outputs/inference"]  # 有就带上，没有也不报错

# 名字或后缀命中即排除
EXCLUDE_DIR_NAMES = {"__pycache__", ".git", ".workbuddy", ".idea", ".vscode", "dist", "tmp_dl", ".pytest_cache"}
EXCLUDE_SUFFIX = {".pyc", ".pyo", ".log", ".zip", ".tmp", ".state"}

# 图片已经压缩过，再 deflate 只会浪费时间
STORE_SUFFIX = {".jpg", ".jpeg", ".png", ".zip", ".pth"}

DATASETS = [
    # (包内目标目录, 源目录)
    ("data/MCDD_data", "D:/shape/Multimodal-Corn-Disease-Dataset-master/MCDD/data"),
    ("data/PV_color", "D:/shape/corn_dataset/raw/color"),
]


def iter_files(base: Path, skip_last: bool = True):
    """递归产出 base 下的文件，按排除规则过滤。"""
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIR_NAMES for part in p.parts):
            continue
        if p.suffix.lower() in EXCLUDE_SUFFIX:
            continue
        if skip_last and p.name.startswith("last_"):
            continue
        yield p


def patch_config() -> bytes:
    """返回改写后的 config.yaml 内容（绝对路径 → 包内相对路径）。"""
    src = (ROOT / "configs" / "config.yaml").read_text(encoding="utf-8")
    src = src.replace(
        "D:/shape/Multimodal-Corn-Disease-Dataset-master/MCDD/data", "data/MCDD_data"
    )
    src = src.replace("D:/shape/corn_dataset/raw", "data/PV_color")
    src = src.replace("D:/shape/corn_dataset", "data/PV_color")
    header = (
        "# === 打包版本：数据集路径已改为包内相对路径 ===\n"
        "# 收件人若自行准备数据集，请把下方 data.sources[].root 改成自己的路径（支持相对路径）。\n"
    )
    return (header + src).encode("utf-8")


def add_path(zf: zipfile.ZipFile, path: Path, arcname: str, stats: dict) -> None:
    """把单个文件写入压缩包，按后缀决定压缩方式。"""
    compress = zipfile.ZIP_STORED if path.suffix.lower() in STORE_SUFFIX else zipfile.ZIP_DEFLATED
    zf.write(path, arcname, compress_type=compress)
    stats["files"] += 1
    stats["bytes"] += path.stat().st_size
    if stats["files"] % 50 == 0:
        print(f"    已写入 {stats['files']:4d} 个文件 / {stats['bytes'] / 1048576:6.1f} MB", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="项目打包脚本")
    ap.add_argument("--out", default="D:/shape/dist", help="压缩包输出目录")
    ap.add_argument("--no-weights", action="store_true", help="不打包模型权重")
    ap.add_argument("--with-dataset", action="store_true", help="同时打包数据集（体积大）")
    ap.add_argument("--name", default=None, help="压缩包名（不含 .zip）")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    name = args.name or f"corn_disease_system_{stamp}"
    if args.no_weights:
        name += "_代码only"
    if args.with_dataset:
        name += "_含数据"
    zip_path = out_dir / f"{name}.zip"
    if zip_path.exists():
        zip_path.unlink()

    t0 = time.time()
    stats = {"files": 0, "bytes": 0}

    print(f"打包目标: {zip_path}")
    print(f"  权重: {'不含' if args.no_weights else '含三个 best_*.pth'}")
    print(f"  数据集: {'含' if args.with_dataset else '不含'}")
    print("-" * 70)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        # 1) 顶层文件
        for fn in INCLUDE_FILES:
            p = ROOT / fn
            if p.exists():
                add_path(zf, p, f"{name}/{fn}", stats)

        # 2) 代码目录
        for d in INCLUDE_DIRS:
            base = ROOT / d
            if not base.exists():
                continue
            for p in iter_files(base):
                # configs/config.yaml 稍后用改写版写入，这里跳过以免重复
                if d == "configs" and p.name == "config.yaml":
                    continue
                add_path(zf, p, f"{name}/{p.relative_to(ROOT).as_posix()}", stats)

        # 3) 配置：写改写后的副本覆盖原条目
        cfg_bytes = patch_config()
        zf.writestr(f"{name}/configs/config.yaml", cfg_bytes)
        stats["files"] += 1
        stats["bytes"] += len(cfg_bytes)

        # 4) 权重
        if not args.no_weights:
            ck = ROOT / CKPT_DIR
            for p in sorted(ck.glob("best_*.pth")):
                add_path(zf, p, f"{name}/{p.relative_to(ROOT).as_posix()}", stats)

        # 5) 报告（png/json/md/txt）
        for d in [REPORT_DIR] + OPTIONAL_DIRS:
            base = ROOT / d
            if not base.exists():
                continue
            for p in iter_files(base):
                add_path(zf, p, f"{name}/{p.relative_to(ROOT).as_posix()}", stats)

        # 6) 数据集
        if args.with_dataset:
            for arc_base, src_dir in DATASETS:
                src = Path(src_dir)
                if not src.exists():
                    print(f"    [跳过] 数据集不存在: {src}")
                    continue
                for p in iter_files(src, skip_last=False):
                    add_path(zf, p, f"{name}/{arc_base}/{p.relative_to(src).as_posix()}", stats)

        # 7) 清单
        manifest = {
            "package": name,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "includes_weights": not args.no_weights,
            "includes_dataset": args.with_dataset,
            "file_count": stats["files"],
            "uncompressed_mb": round(stats["bytes"] / 1048576, 1),
            "entry_point": "run_server.bat 或 python -m uvicorn app.api:app --port 8010",
        }
        zf.writestr(f"{name}/打包清单.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        stats["files"] += 1

    size_mb = zip_path.stat().st_size / 1048576
    print("-" * 70)
    print(f"完成：{stats['files']} 个文件，原始 {stats['bytes'] / 1048576:.1f} MB → "
          f"压缩后 {size_mb:.1f} MB，用时 {time.time() - t0:.1f}s")

    h = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    print(f"SHA256: {h.hexdigest()}")

    # 顺手做一次完整性自检
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        print("完整性自检:", "OK" if bad is None else f"损坏条目 {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
