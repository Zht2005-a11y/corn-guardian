"""多源玉米病害数据集合并 / 去重 / 重划分。

为什么需要它
------------
1. 现有 MCDD 内部有 244 组重复图片，其中 59 组跨 train/test（占测试集 6.4%），
   会让 val_acc 虚高；合并新数据前必须先按 md5 全局去重、再统一重划分。
2. AI Challenger 等数据源的类别是 label id（9~16），需要映射到我们的类别键。
3. 多个数据源存在同源图片（PlantVillage 血统），必须全局去重，不能只在单源内去重。

输出
----
<output>/{train,val,test}/<Class>/*.jpg  —— 标准 ImageFolder，可直接给 src/dataset.py 用
<output>/../manifest.csv                —— 每张图的来源、类别、划分、md5
<output>/../stats.json                  —— 每类数量、去重与冲突统计

用法
----
    python scripts/prepare_multiclass.py --plan scripts/dataset_plan.example.json --dry-run
    python scripts/prepare_multiclass.py --plan scripts/dataset_plan.example.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def md5_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def resolve_map(src: Dict[str, Any]) -> Dict[str, str]:
    """把 map / map_by_folder 合并成 {文件夹名: 类别键}。"""
    mapping: Dict[str, str] = {}
    mapping.update({str(k): str(v) for k, v in (src.get("map") or {}).items()})
    mapping.update({str(k): str(v) for k, v in (src.get("map_by_folder") or {}).items()})
    return mapping


def scan_source(src: Dict[str, Any]) -> Tuple[List[Tuple[str, Path, str]], List[str]]:
    """扫描一个数据源，返回 [(class, path, split_hint)] 与被跳过的目录。"""
    root = Path(src["root"]).expanduser()
    mapping = resolve_map(src)
    samples: List[Tuple[str, Path, str]] = []
    skipped: List[str] = []

    if not root.exists():
        return [], [f"路径不存在: {root}"]

    splits = src.get("splits") or {}
    if not splits:
        # 默认：根目录下 train/test（或 train/val/test）
        for name in ("train", "val", "test"):
            if (root / name).is_dir():
                splits[name] = name

    for split_name, sub in splits.items():
        d = root / sub
        if not d.is_dir():
            skipped.append(f"{split_name}: 目录不存在 {d}")
            continue
        for folder in sorted(p for p in d.iterdir() if p.is_dir()):
            cls = mapping.get(folder.name)
            if cls is None:
                # 未映射的类别直接跳过（例如 AI Challenger 的其它作物）
                skipped.append(f"{split_name}/{folder.name}（未映射）")
                continue
            for f in folder.iterdir():
                if f.suffix.lower() in IMG_EXT:
                    samples.append((cls, f, split_name))
    return samples, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="数据集合并计划 JSON")
    ap.add_argument("--dry-run", action="store_true", help="只统计，不落盘")
    ap.add_argument("--link", action="store_true", help="用硬链接代替复制（同盘、省空间）")
    ap.add_argument("--min-per-class", type=int, default=100, help="低于该数量给出告警")
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    out_root = Path(plan["output"]).expanduser()
    class_order: List[str] = list(plan["class_order"])
    seed = int(plan.get("seed", 2026))
    ratios = plan.get("ratios", {"train": 0.7, "val": 0.15, "test": 0.15})
    assert abs(sum(ratios.values()) - 1.0) < 1e-6, f"ratios 之和必须为 1：{ratios}"

    # ---------- 1. 扫描 ----------
    print("=" * 68)
    print("扫描数据源")
    print("=" * 68)
    pool: List[Tuple[str, Path, str, str]] = []  # (class, path, src, split_hint)
    for src in plan["sources"]:
        samples, skipped = scan_source(src)
        per_cls = Counter(c for c, _, _ in samples)
        print(f"[{src['name']}] {len(samples)} 张  {dict(sorted(per_cls.items()))}")
        for s in skipped[:6]:
            print(f"    跳过 {s}")
        if len(skipped) > 6:
            print(f"    …… 另有 {len(skipped) - 6} 项未列出")
        pool.extend((c, p, src["name"], h) for c, p, h in samples)

    unknown = {c for c, *_ in pool} - set(class_order)
    if unknown:
        print(f"!! 出现未列入 class_order 的类别：{unknown}", file=sys.stderr)
        return 2

    # ---------- 2. 全局去重（md5） ----------
    print()
    print("=" * 68)
    print("全局去重")
    print("=" * 68)
    by_hash: Dict[str, List[Tuple[str, Path, str, str]]] = defaultdict(list)
    for item in pool:
        by_hash[md5_of(item[1])].append(item)

    deduped: List[Tuple[str, Path, str, str]] = []
    digest_by_path: Dict[str, str] = {}
    dup_removed = 0
    cross_class = 0
    cross_class_dropped = 0
    cross_class_examples: List[str] = []
    policy = str(plan.get("conflict_policy", "skip")).lower()
    assert policy in ("skip", "keep_first"), "conflict_policy 只能是 skip / keep_first"

    for digest, items in by_hash.items():
        classes = {i[0] for i in items}
        if len(classes) > 1:
            cross_class += 1
            if len(cross_class_examples) < 5:
                cross_class_examples.append(
                    f"{digest[:8]}: " + " / ".join(f"{i[0]}<-{i[2]}" for i in items)
                )
            if policy == "skip":
                # 同一张图被标成不同病种 → 真值不明，整组丢弃，避免污染新类别
                cross_class_dropped += 1
                dup_removed += len(items)
                continue
        deduped.append(items[0])  # 同一张图只保留第一条
        digest_by_path[str(items[0][1])] = digest
        dup_removed += len(items) - 1

    print(f"扫描到 {len(pool)} 张，唯一图片 {len(deduped)} 张，去掉重复 {dup_removed} 张")
    if cross_class:
        print(f"!! {cross_class} 组图片被标成了不同类别（策略：{policy}）")
        if policy == "skip":
            print(f"   已整组丢弃 {cross_class_dropped} 组，避免新类别标签被污染")
        for ex in cross_class_examples:
            print(f"   {ex}")

    # ---------- 3. 按类别分层重划分 ----------
    print()
    print("=" * 68)
    print("分层重划分（同一张图不会同时出现在两个 split）")
    print("=" * 68)
    rng = random.Random(seed)
    per_class: Dict[str, List[Tuple[str, Path, str, str]]] = defaultdict(list)
    for item in deduped:
        per_class[item[0]].append(item)

    assigned: Dict[str, List[Tuple[str, Path, str, str]]] = {"train": [], "val": [], "test": []}
    missing = [c for c in class_order if len(per_class.get(c, [])) == 0]
    for cls in class_order:
        items = per_class.get(cls, [])
        rng.shuffle(items)
        n = len(items)
        # ratio 为 0 的 split 完全跳过（train.py 会自己从 train 里再切 val，见 config.val_ratio）
        n_test = int(round(n * ratios["test"])) if ratios["test"] > 0 else 0
        n_val = int(round(n * ratios["val"])) if ratios["val"] > 0 else 0
        if n >= 3 and ratios["test"] > 0:
            n_test = max(1, min(n_test, n - 2))
        if n >= 3 and ratios["val"] > 0:
            n_val = max(1, min(n_val, n - n_test - 1))
        assigned["test"].extend(items[:n_test])
        assigned["val"].extend(items[n_test:n_test + n_val])
        assigned["train"].extend(items[n_test + n_val:])
        print(f"{cls:<24} 共 {n:>5}  train {n - n_test - n_val:>5}  val {n_val:>4}  test {n_test:>4}")

    # 复检：三个 split 之间不应有相同 md5（去重后天然成立，这里显式断言）
    seen: Dict[str, str] = {}
    for split, items in assigned.items():
        for cls, path, src, _ in items:
            d = md5_of(path)
            if d in seen and seen[d] != split:
                print(f"!! 泄漏：{path} 同时出现在 {seen[d]} 与 {split}", file=sys.stderr)
                return 3
            seen[d] = split
    print("\n复检通过：train / val / test 之间零重叠")

    # ---------- 4. 落盘 ----------
    total_warn = [c for c in class_order if 0 < len(per_class.get(c, [])) < args.min_per_class]
    if missing:
        print(f"\n!! 这些类别没有任何样本：{missing}", file=sys.stderr)
        if not args.dry_run:
            return 4
    if total_warn:
        print(f"\n提醒：{', '.join(f'{c}({len(per_class[c])})' for c in total_warn)} 少于 {args.min_per_class} 张，"
              f"训练时容易过拟合，建议用 class_weight 或补数据")

    if args.dry_run:
        print("\n(dry-run，未写入任何文件)")
        return 0

    if out_root.exists():
        print(f"\n清空输出目录 {out_root}")
        shutil.rmtree(out_root)
    manifest_rows: List[Dict[str, Any]] = []
    for split, items in assigned.items():
        for cls, path, src, hint in items:
            dst_dir = out_root / split / cls
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f"{src}_{path.name}"
            k = 1
            while dst.exists():
                dst = dst_dir / f"{src}_{path.stem}_{k}{path.suffix}"
                k += 1
            if args.link:
                try:
                    dst.hardlink_to(path)
                except OSError:
                    shutil.copy2(path, dst)
            else:
                shutil.copy2(path, dst)
            manifest_rows.append(
                {"split": split, "class": cls, "source": src, "orig_split": hint,
                 "dst": str(dst), "orig": str(path), "md5": digest_by_path.get(str(path), "")}
            )

    meta_dir = out_root.parent
    with open(meta_dir / "manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)
    stats = {
        "class_order": class_order,
        "seed": seed,
        "ratios": ratios,
        "scanned": len(pool),
        "unique": len(deduped),
        "duplicates_removed": dup_removed,
        "cross_class_conflicts": cross_class,
        "conflict_policy": policy,
        "cross_class_dropped": cross_class_dropped,
        "cross_class_examples": cross_class_examples,
        "per_class": {c: len(per_class.get(c, [])) for c in class_order},
        "per_split": {sp: len(v) for sp, v in assigned.items()},
        "sources": [s["name"] for s in plan["sources"]],
    }
    (meta_dir / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n已写入 {out_root}")
    print(f"  清单：{meta_dir / 'manifest.csv'}")
    print(f"  统计：{meta_dir / 'stats.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
