"""玉米病虫害智能识别系统 —— 配置加载与全局常量。

设计要点：
1. 所有配置集中在 configs/config.yaml，代码只做校验与路径解析；
2. 类别中文名 / 病害知识库与类别索引解耦，保证前端、后端、训练脚本共用同一份映射；
3. 提供一个轻量 YAML 解析（优先 PyYAML，缺失时回退到内置简易解析器），
   避免因为少装一个包导致训练脚本跑不起来。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"


# --------------------------------------------------------------------------
# YAML 加载（带简易回退，兼容未安装 pyyaml 的环境）
# --------------------------------------------------------------------------
def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return _mini_yaml_load(path.read_text(encoding="utf-8"))


def _mini_yaml_load(text: str) -> Dict[str, Any]:
    """极简 YAML 解析：仅支持本项目用到的 嵌套字典 / 列表 / 标量。"""
    root: Dict[str, Any] = {}
    stack: List[tuple[int, Any]] = [(-1, root)]


    def cast(v: str) -> Any:
        v = v.strip().strip('"').strip("'")
        low = v.lower()
        if low in ("true", "yes"):
            return True
        if low in ("false", "no"):
            return False
        if low in ("null", "none", "~", ""):
            return None
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            return [cast(x) for x in inner.split(",")] if inner else []
        try:
            return int(v)
        except ValueError:
            pass
        try:
            return float(v)
        except ValueError:
            return v

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        line = raw.split(" #")[0].rstrip()
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, root)]
        parent = stack[-1][1]

        if body.startswith("- "):
            item = body[2:].strip()
            if isinstance(parent, list):
                if ":" in item and not item.startswith(("http", "D:", "C:")):
                    key, _, val = item.partition(":")
                    d: Dict[str, Any] = {key.strip(): cast(val)} if val.strip() else {key.strip(): {}}
                    parent.append(d)
                    stack.append((indent, d))
                else:
                    parent.append(cast(item))
            continue

        if ":" not in body:
            continue
        key, _, val = body.partition(":")
        key = key.strip()
        if val.strip():
            if isinstance(parent, dict):
                parent[key] = cast(val)
        elif isinstance(parent, dict):
            parent[key] = {}
            stack.append((indent, parent[key]))
    return root





def load_config(path: str | os.PathLike | None = None) -> Dict[str, Any]:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {cfg_path}")
    cfg = _load_yaml(cfg_path)
    _normalize(cfg)
    return cfg


def _normalize(cfg: Dict[str, Any]) -> None:
    """补全默认值 + 相对路径转绝对路径。"""
    cfg.setdefault("data", {})
    data = cfg["data"]
    data.setdefault("class_names", CLASS_EN_TO_INDEX)
    data.setdefault("val_ratio", 0.15)
    data.setdefault("split_seed", 42)
    data.setdefault("num_workers", 4)
    for src in data.get("sources", []):
        if not src.get("root"):
            continue
        src["root"] = str(Path(src["root"].replace("\\", "/")).expanduser())
        src.setdefault("train_dir", "train")
        src.setdefault("test_dir", "test")
        src.setdefault("use_for_train", True)
        src.setdefault("evaluate", True)  # False 表示该源的 test 目录不参与"官方测试集"评估
        src.setdefault("name", Path(src["root"]).name)

    for section in ("train", "infer", "server", "model"):
        cfg.setdefault(section, {})

    train = cfg["train"]
    train.setdefault("save_dir", "outputs/checkpoints")
    train.setdefault("best_name", "best_corn_model.pth")
    train.setdefault("image_size", 224)
    train.setdefault("seed", 42)
    train["save_dir"] = str(_abs(train["save_dir"]))
    cfg["outputs_dir"] = str(PROJECT_ROOT / "outputs")

    server = cfg["server"]
    for m in server.get("models", {}).values():
        if isinstance(m, dict) and m.get("path"):
            m["path"] = str(_abs(m["path"]))


def _abs(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (PROJECT_ROOT / path)


# --------------------------------------------------------------------------
# 类别映射（索引顺序 = ImageFolder 文件夹名排序，绝对不能改动顺序）
# --------------------------------------------------------------------------
CLASS_EN_TO_INDEX: List[str] = ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"]

CLASS_INDEX_TO_CN: Dict[int, str] = {
    0: "玉米大斑病",
    1: "玉米普通锈病",
    2: "玉米灰斑病",
    3: "健康叶片",
}

CLASS_KEY_TO_CN: Dict[str, str] = {
    "Blight": "玉米大斑病",
    "Common_Rust": "玉米普通锈病",
    "Gray_Leaf_Spot": "玉米灰斑病",
    "Healthy": "健康叶片",
}

# 不同数据集中"同一病害"的别名，用于合并多数据集时统一类别
CLASS_ALIASES: Dict[str, str] = {
    "blight": "Blight",
    "northern_leaf_blight": "Blight",
    "nlb": "Blight",
    "corn_blight": "Blight",
    "common_rust": "Common_Rust",
    "rust": "Common_Rust",
    "commonrust": "Common_Rust",
    "gray_leaf_spot": "Gray_Leaf_Spot",
    "gray_spot": "Gray_Leaf_Spot",
    "grey_leaf_spot": "Gray_Leaf_Spot",
    "gls": "Gray_Leaf_Spot",
    "healthy": "Healthy",
    "health": "Healthy",
    "normal": "Healthy",
    "health_corn": "Healthy",
}

# 常见数据集对类别名的"包裹形式"，例如 PlantVillage 的
#   "Corn_(maize)___Northern_Leaf_Blight"
#   "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot"
#   "Corn_(maize)___Common_rust_"
# 归一化时先去掉这些前缀/后缀再查别名表。
_CLASS_PREFIX_PATTERNS = [
    "corn_(maize)___",
    "corn___",
    "corn_",
    "maize_",
    "玉米___",
]


def normalize_class_name(name: str) -> str:
    """把数据集文件夹名映射到标准类别名（多数据集合并时的关键）。

    处理顺序：
    1. 去首尾空格、小写、连字符/空格统一成下划线；
    2. 去掉 "corn_(maize)___" 之类的前缀与末尾的多余下划线；
    3. 查别名表（精确匹配优先）；
    4. 仍匹配不上时做"包含式"匹配（如 "cercospora_leaf_spot_gray_leaf_spot" -> Gray_Leaf_Spot）。
    """
    raw = name.strip()
    key = raw.lower().replace("-", "_").replace(" ", "_")
    for prefix in _CLASS_PREFIX_PATTERNS:
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    key = key.strip("_")
    if key in CLASS_ALIASES:
        return CLASS_ALIASES[key]
    # 包含式匹配：较长/较具体的别名优先，避免 "rust" 误吃 "rust_xxx"
    for alias in sorted(CLASS_ALIASES, key=len, reverse=True):
        if len(alias) >= 4 and alias in key:
            return CLASS_ALIASES[alias]
    return raw


def get_class_names(cfg: Dict[str, Any] | None = None) -> List[str]:
    if cfg:
        names = cfg.get("data", {}).get("class_names") or CLASS_EN_TO_INDEX
    else:
        names = CLASS_EN_TO_INDEX
    return [str(n) for n in names]


def get_class_cn(index: int) -> str:
    return CLASS_INDEX_TO_CN.get(int(index), f"未知类别{index}")
