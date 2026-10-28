"""把 AI Challenger 2018 农作物病害数据集中的「玉米」部分拆成 ImageFolder 目录。

为什么需要
----------
官方下载包是「一堆图片 + 一个标注 json」，json 里每条是
    {"image_id": "xxxx.jpg", "disease_class": 12}
label 是 0~60 的数字（玉米是 9~16）。直接扔给训练脚本没法用，
必须先按 label 落成 <out>/train/<label>/<image_id> 这种结构。

玉米 label 对照（官方 61 分类，按「物种-病害-严重度」切分）
    9  玉米健康
    10 玉米灰斑病 一般   11 玉米灰斑病 严重
    12 玉米南方锈病 一般  13 玉米南方锈病 严重      ← Puccinia polysora，不是普通锈病
    14 玉米弯孢菌叶斑病 一般  15 玉米弯孢菌叶斑病 严重
    16 玉米花叶病毒病
其它作物的 label 会被跳过。

用法
----
    python scripts/split_aic2018.py \
        --ann  D:/dataset/AIC2018/AgriculturalDisease_trainingset/AgriculturalDisease_train_annotations.json \
        --images D:/dataset/AIC2018/AgriculturalDisease_trainingset/images \
        --out D:/shijianzhou/corn-guardian/dataset/AIC2018/data/train

    # 验证集（如有标注）同样处理，输出到 val 目录
    python scripts/split_aic2018.py --ann ...valid_annotations.json --images ... --out .../data/val
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

CORN_LABELS: Dict[int, str] = {
    9: "9_healthy",
    10: "10_gray_leaf_spot_general",
    11: "11_gray_leaf_spot_serious",
    12: "12_southern_rust_general",
    13: "13_southern_rust_serious",
    14: "14_curvularia_general",
    15: "15_curvularia_serious",
    16: "16_mosaic_virus",
}


def load_annotations(path: Path) -> List[Dict[str, Any]]:
    """兼容两种常见存法：单个 json（list）或 目录（多个 json）。"""
    items: List[Dict[str, Any]] = []
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            # 少数镜像会包一层 {"annotations": [...]}
            data = data.get("annotations") or data.get("data") or []
        items.extend(data)
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ann", required=True, help="标注 json 文件或所在目录")
    ap.add_argument("--images", required=True, help="图片目录")
    ap.add_argument("--out", required=True, help="输出目录，通常是 .../data/train")
    ap.add_argument("--link", action="store_true", help="用硬链接代替复制")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ann_path = Path(args.ann).expanduser()
    img_dir = Path(args.images).expanduser()
    out_root = Path(args.out).expanduser()

    if not ann_path.exists():
        print(f"标注不存在: {ann_path}")
        return 2
    if not img_dir.is_dir():
        print(f"图片目录不存在: {img_dir}")
        return 2

    records = load_annotations(ann_path)
    print(f"标注共 {len(records)} 条")

    kept = 0
    missing: List[str] = []
    per_label: Counter = Counter()
    label_of_all: Counter = Counter()

    for rec in records:
        cls = rec.get("disease_class", rec.get("label"))
        name = rec.get("image_id") or rec.get("filename") or rec.get("file_name")
        if cls is None or not name:
            continue
        try:
            cls = int(cls)
        except (TypeError, ValueError):
            continue
        label_of_all[cls] += 1
        folder = CORN_LABELS.get(cls)
        if folder is None:
            continue  # 非玉米，跳过
        src = img_dir / name
        if not src.exists():
            missing.append(name)
            continue
        kept += 1
        per_label[folder] += 1
        if args.dry_run:
            continue
        dst_dir = out_root / folder
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / name
        if dst.exists():
            continue
        if args.link:
            try:
                dst.hardlink_to(src)
                continue
            except OSError:
                pass
        shutil.copy2(src, dst)

    print(f"玉米样本 {kept} 条（另有 {len(missing)} 条在图片目录里找不到）")
    print("按 label 统计：")
    for label in sorted(CORN_LABELS):
        print(f"  {label:>2} {CORN_LABELS[label]:<28} {per_label.get(CORN_LABELS[label], 0):>6}")
    if missing:
        print(f"缺失示例：{missing[:5]}")
    other = {k: v for k, v in label_of_all.items() if k not in CORN_LABELS}
    if other:
        print(f"跳过的非玉米 label {len(other)} 个，共 {sum(other.values())} 条")
    if args.dry_run:
        print("(dry-run，未写入文件)")
    else:
        print(f"已写入 {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
