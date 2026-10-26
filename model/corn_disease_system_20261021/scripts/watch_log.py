"""日志/产物查看小工具（跨平台，避免 Windows 终端编码与 PowerShell 管道问题）。

用法：
    python -m scripts.watch_log outputs/logs/train_20261021_103917.log      # 看最后 30 行
    python -m scripts.watch_log selftest_full.log --tail 80
    python -m scripts.watch_log selftest_full.log --grep PASS FAIL
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--tail", type=int, default=30)
    ap.add_argument("--grep", nargs="*", default=None)
    ap.add_argument("--encoding", default="utf-8")
    args = ap.parse_args()

    p = Path(args.file)
    if not p.exists():
        print(f"文件不存在: {p}")
        return 1

    text = p.read_text(encoding=args.encoding, errors="replace")
    lines = text.splitlines()
    if args.grep:
        lines = [ln for ln in lines if any(g in ln for g in args.grep)]
    for ln in lines[-args.tail:]:
        print(ln)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
