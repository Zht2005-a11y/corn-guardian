"""推理封装：单张 / 批量预测、异常图像判断、Grad-CAM、模型对比测速。

对外主要接口（后端只依赖这三样）：
    predictor = CornDiseasePredictor(config, arch="resnet50", weight="...")
    predictor.predict_path("a.jpg")                 -> dict
    predictor.predict_bytes(b"...", "a.jpg")        -> dict
    predictor.predict_batch([...paths...])          -> list[dict]
    predictor.predict_with_gradcam(image_bytes)     -> dict（含 base64 热力图）

异常处理策略（任务要求"处理损坏图片、非玉米叶片图片"）：
1. 损坏 / 非图片：PIL 解码失败 -> 抛 InvalidImageError（后端转 400）；
2. 超大图片：超过 max_image_side -> 抛 InvalidImageError（避免内存爆炸）；
3. 极端宽高比 / 过小图片：判定为无效输入；
4. 非玉米叶片（如天空、人脸、白墙）：模型其实给不出"other"类别，
   因此用三重启发式规则综合判断：
     - 模型最大置信度低于阈值；
     - 预测类别与第二类别概率差距（margin）过小；
     - 图像色彩统计不像叶片（绿色占比过低 / 灰度直方图过于平坦）。
   只要命中任一警示，就在返回结果里给出 `is_valid_leaf=False` 与 `warning` 提示，
   但**仍然返回预测结果**，由前端决定是否展示"疑似非玉米叶片"。
"""
from __future__ import annotations

import hashlib
import io
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageOps, UnidentifiedImageError

from .config import (
    PROJECT_ROOT,
    get_class_cn,
    get_class_names,
    load_config,
)
from .dataset import build_eval_transform
from .knowledge_base import get_knowledge
from .models import build_model


class InvalidImageError(ValueError):
    """图片不可用（损坏 / 格式不支持 / 尺寸异常）。"""


SUPPORTED_EXT = {"jpg", "jpeg", "png", "bmp", "webp"}


# ==========================================================================
#  置信度等级
# ==========================================================================
def confidence_level(score: float, high: float = 0.85, mid: float = 0.60) -> Tuple[str, str]:
    """把置信度映射为等级与中文提示。"""
    if score >= high:
        return "high", "高置信度：识别结果可靠"
    if score >= mid:
        return "medium", "中等置信度：建议结合田间观察复核"
    return "low", "低置信度：仅供参考，建议重新拍摄清晰叶片照片"


# ==========================================================================
#  图像校验与预处理（带 LRU 缓存）
# ==========================================================================
def validate_image(data: bytes, max_image_mb: float = 10, max_side: int = 4096) -> Image.Image:
    """校验并解码图片，任何异常都抛出 InvalidImageError 并带明确原因。"""
    if not data:
        raise InvalidImageError("上传内容为空")
    size_mb = len(data) / 1024 / 1024
    if size_mb > max_image_mb:
        raise InvalidImageError(f"图片过大（{size_mb:.1f}MB），请压缩至 {max_image_mb}MB 以内")

    # 先读文件头判断是否为可识别图片格式，再完整解码（防止"只读头成功、解码失败"）
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt = (im.format or "").lower()
            if fmt not in SUPPORTED_EXT and fmt not in {"mpo", "tiff"}:
                raise InvalidImageError(f"不支持的图片格式: {fmt or 'unknown'}")
            im.load()
            # 依据 EXIF 方向信息摆正（手机竖拍的照片很常见）
            img = ImageOps.exif_transpose(im).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise InvalidImageError(f"图片损坏或格式不受支持：{e}") from e
    except Exception as e:  # 罕见解码器异常
        raise InvalidImageError(f"图片解码失败：{e}") from e

    w, h = img.size
    if max(w, h) > max_side:
        raise InvalidImageError(f"图片尺寸过大（{w}x{h}），最长边不得超过 {max_side}px")
    if min(w, h) < 32:
        raise InvalidImageError(f"图片尺寸过小（{w}x{h}），请上传清晰叶片照片")
    return img


def leaf_likelihood_score(img: Image.Image) -> float:
    """非常轻量的"像不像叶片"启发式打分（0~1）。

    思路：玉米叶片照片通常绿色/黄色占比高、饱和度中等、有纹理细节。
    纯色背景、人脸、天空等图片这些统计量会明显偏离。
    这里只是**辅助提示**，不参与分类决策，避免误伤真实样本。
    """
    small = img.convert("RGB").resize((128, 128), Image.BILINEAR)
    arr = np.asarray(small, dtype=np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

    # 绿色像素：G 明显大于 R、B（玉米健康叶 / 病斑周围组织）
    greenish = ((g > r * 0.95) & (g > b * 0.95) & (g > 40)).mean()
    # 黄褐色像素：锈病、枯斑常见色（R 高、G 中、B 低）
    yellowish = ((r > 90) & (g > 50) & (b < g * 0.85) & (r > b)).mean()
    # 纹理丰富度：灰度梯度均值（叶片有叶脉、病斑纹理，纯色背景接近 0）
    gray = arr.mean(axis=2)
    gx = np.abs(np.diff(gray, axis=1)).mean() / 255.0
    gy = np.abs(np.diff(gray, axis=0)).mean() / 255.0
    texture = min((gx + gy) * 8.0, 1.0)

    color_score = min((greenish + 0.8 * yellowish) * 2.0, 1.0)
    return float(np.clip(0.65 * color_score + 0.35 * texture, 0, 1))


class _TensorCache:
    """预处理结果 LRU 缓存：同一张图片重复请求（前端预览→识别）无需重复解码+归一化。

    key 使用图片内容 MD5，天然支持去重；容量固定，避免长时间运行内存膨胀。
    """

    def __init__(self, max_size: int = 256) -> None:
        self.max_size = max_size
        self._store: "OrderedDict[str, torch.Tensor]" = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[torch.Tensor]:
        if key in self._store:
            self._store.move_to_end(key)
            self.hits += 1
            return self._store[key]
        self.misses += 1
        return None

    def put(self, key: str, value: torch.Tensor) -> None:
        self._store[key] = value
        self._store.move_to_end(key)
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()

    @property
    def stats(self) -> Dict[str, int]:
        return {"size": len(self._store), "capacity": self.max_size, "hits": self.hits, "misses": self.misses}


# ==========================================================================
#  单模型封装
# ==========================================================================
class _SingleModel:
    def __init__(self, arch: str, weight: Optional[str], num_classes: int, device: torch.device,
                 image_size: int = 224, dropout: float = 0.3) -> None:
        self.arch = arch
        self.device = device
        self.transform = build_eval_transform(image_size)
        self.image_size = image_size
        self.cache = _TensorCache()
        self.loaded_from_random_init = False

        meta: Dict[str, Any] = {}
        if weight and Path(weight).exists():
            ckpt = torch.load(weight, map_location=device)
            if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
                meta = {k: v for k, v in ckpt.items() if k != "model_state_dict"}
                state = ckpt["model_state_dict"]
            else:
                state = ckpt
            arch = meta.get("arch", arch)
            num_classes = int(meta.get("num_classes", num_classes))
            self.image_size = int(meta.get("image_size", image_size))
            self.transform = build_eval_transform(self.image_size)
        else:
            state = None

        model = build_model(
            arch=arch,
            num_classes=num_classes,
            pretrained=False,   # 权重一律来自本地，避免服务启动时联网
            dropout=dropout,
            use_cbam=bool(meta.get("use_cbam", "cbam" in arch)),
        )
        if state is not None:
            model.load_state_dict(state)
        else:
            self.loaded_from_random_init = True
        self.model: nn.Module = model.to(device).eval()
        self.arch = arch
        self.num_classes = num_classes
        self.weight_meta = meta

        # 特征缓存：avgpool 输出（2048 维），供「非目标图像门控」算特征空间距离
        self._feat: Optional[torch.Tensor] = None
        self._feat_hook = None
        pool = getattr(self.model, "avgpool", None)
        if pool is not None:
            self._feat_hook = pool.register_forward_hook(self._capture_feature)

    def _capture_feature(self, _module, _inputs, output) -> None:
        self._feat = output.detach().flatten(1)

    @torch.no_grad()
    def logits(self, tensors: torch.Tensor) -> torch.Tensor:
        return self.model(tensors.to(self.device))

    def preprocess(self, img: Image.Image, cache_key: Optional[str] = None) -> torch.Tensor:
        """单图 -> [1,3,H,W]；命中缓存直接返回。"""
        if cache_key:
            hit = self.cache.get(cache_key)
            if hit is not None:
                return hit
        tensor = self.transform(img).unsqueeze(0)
        if cache_key:
            self.cache.put(cache_key, tensor)
        return tensor

    def warmup(self, rounds: int = 2) -> float:
        """预热：第一轮包含 cuDNN 算法选择/内存分配，不计入正式耗时。"""
        dummy = torch.randn(1, 3, self.image_size, self.image_size, device=self.device)
        with torch.no_grad():
            for _ in range(rounds):
                self.model(dummy)
        if self.device.type == "cuda":
            torch.cuda.synchronize()
        return 0.0


# ==========================================================================
#  对外主类（支持多模型 + 单例）
# ==========================================================================
class CornDiseasePredictor:
    """多模型推理器。构造时加载全部模型并预热，供 FastAPI 单例使用。"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        model_specs: Optional[Dict[str, Dict[str, str]]] = None,
        default_model: Optional[str] = None,
        device: Optional[str] = None,
        image_size: Optional[int] = None,
    ) -> None:
        self.cfg = config or load_config()
        infer_cfg = self.cfg.get("infer", {})
        server_cfg = self.cfg.get("server", {})

        self.class_names = get_class_names(self.cfg)
        self.class_cn = [get_class_cn(i) for i in range(len(self.class_names))]
        self.num_classes = len(self.class_names)
        self.image_size = image_size or self.cfg.get("train", {}).get("image_size", 224)
        self.dropout = self.cfg.get("model", {}).get("dropout", 0.3)

        dev = device or infer_cfg.get("device", "auto")
        if dev == "auto":
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(dev)

        self.max_image_mb = float(server_cfg.get("max_upload_mb", 10))
        self.max_image_side = int(infer_cfg.get("max_image_side", 4096))
        self.conf_high = float(infer_cfg.get("confidence_high", 0.85))
        self.conf_mid = float(infer_cfg.get("confidence_mid", 0.60))
        self.cache_size = int(server_cfg.get("cache_size", 256))

        specs = model_specs or server_cfg.get("models") or {
            "resnet50": {"path": str(PROJECT_ROOT / "outputs/checkpoints/best_corn_model.pth"),
                         "arch": "resnet50"}
        }

        self.models: Dict[str, _SingleModel] = {}
        self.load_report: Dict[str, Dict[str, Any]] = {}
        for key, spec in specs.items():
            arch = spec.get("arch", key)
            path = spec.get("path") or spec.get("weight")
            t0 = time.perf_counter()
            wrapper = _SingleModel(arch, path, self.num_classes, self.device,
                                   self.image_size, self.dropout)
            wrapper.cache = _TensorCache(self.cache_size)
            wrapper.warmup()
            self.models[key] = wrapper
            self.load_report[key] = {
                "arch": wrapper.arch,
                "weight": str(path),
                "loaded": not wrapper.loaded_from_random_init,
                "num_classes": wrapper.num_classes,
                "val_acc_in_ckpt": wrapper.weight_meta.get("val_acc"),
                "load_ms": round((time.perf_counter() - t0) * 1000, 1),
            }

        self.default_model = default_model or server_cfg.get("default_model", next(iter(self.models)))
        if self.default_model not in self.models:
            self.default_model = next(iter(self.models))

        # 非目标图像门控：类中心缺失时自动降级为「颜色 + 置信度」
        from .image_gate import LeafGate

        self.gate = LeafGate()

        self._gradcams: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    #  基础信息
    # ------------------------------------------------------------------
    @property
    def available_models(self) -> List[str]:
        return list(self.models.keys())

    def _resolve_model(self, model_key: Optional[str]) -> Tuple[str, _SingleModel]:
        key = model_key or self.default_model
        if key not in self.models:
            raise KeyError(f"未知模型 '{key}'，可用: {list(self.models.keys())}")
        return key, self.models[key]

    def info(self) -> Dict[str, Any]:
        return {
            "device": str(self.device),
            "class_names": self.class_names,
            "class_names_cn": self.class_cn,
            "image_size": self.image_size,
            "default_model": self.default_model,
            "models": self.load_report,
            "cache": {k: v.cache.stats for k, v in self.models.items()},
        }

    # ------------------------------------------------------------------
    #  核心推理
    # ------------------------------------------------------------------
    def _build_result(
        self,
        prob: np.ndarray,
        elapsed_ms: float,
        model_key: str,
        image_size: Optional[Tuple[int, int]] = None,
        filename: Optional[str] = None,
        leaf_score: Optional[float] = None,
        gate: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        order = np.argsort(prob)[::-1]
        idx = int(order[0])
        top1 = float(prob[order[0]])
        top2 = float(prob[order[1]]) if len(order) > 1 else 0.0
        level, hint = confidence_level(top1, self.conf_high, self.conf_mid)

        warnings: List[str] = []
        is_valid_leaf = True
        if level == "low":
            warnings.append("模型置信度较低，图片可能不属于四类中的任何一类，或画质不足")
            is_valid_leaf = False
        if (top1 - top2) < 0.15 and top1 < self.conf_high:
            warnings.append("前两类概率接近，存在类别混淆风险")
        if leaf_score is not None and leaf_score < 0.28:
            warnings.append("图像色彩/纹理特征与玉米叶片差异较大，疑似非玉米叶片图片")
            is_valid_leaf = False

        # 门控判定（颜色/植被指数 + 特征空间距离 + 置信度兜底）
        is_target = True
        gate_info: Dict[str, Any] = {}
        if gate is not None:
            is_target = bool(gate.get("is_target", True))
            gate_info = gate
            if not is_target:
                warnings.append("未检测到玉米叶片：图像可能不是叶片（桌面/天空/截图等），已拒绝出方")
                is_valid_leaf = False

        result = {
            "filename": filename,
            "class_index": idx,
            "class_name_en": self.class_names[idx],
            "class_name": self.class_cn[idx],
            "confidence": round(top1, 4),
            "confidence_percent": f"{top1 * 100:.2f}%",
            "confidence_level": level,
            "confidence_hint": hint,
            "is_healthy": self.class_names[idx].lower() == "healthy",
            "is_valid_leaf": is_valid_leaf,
            "is_target": is_target,
            "leaf_gate": gate_info,
            "warning": "；".join(warnings) if warnings else None,
            "top2": {
                "class_name": self.class_cn[int(order[1])] if len(order) > 1 else None,
                "confidence": round(top2, 4),
            },
            "probabilities": {self.class_cn[i]: round(float(prob[i]), 4) for i in range(len(prob))},
            "model": model_key,
            "inference_time_ms": round(elapsed_ms, 2),
            "image_size": list(image_size) if image_size else None,
        }
        return result

    def _infer_tensor(self, wrapper: _SingleModel, tensor: torch.Tensor) -> Tuple[np.ndarray, float]:
        if wrapper.device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        logits = wrapper.logits(tensor)
        prob = torch.softmax(logits.float(), dim=1)[0].cpu().numpy()
        if wrapper.device.type == "cuda":
            torch.cuda.synchronize()
        return prob, (time.perf_counter() - t0) * 1000

    # ---------------- 单张：字节流 ----------------
    def predict_bytes(
        self,
        data: bytes,
        filename: str = "upload.jpg",
        model_key: Optional[str] = None,
        use_cache: bool = True,
        with_gradcam: bool = False,
    ) -> Dict[str, Any]:
        key, wrapper = self._resolve_model(model_key)
        img = validate_image(data, self.max_image_mb, self.max_image_side)
        cache_key = hashlib.md5(data).hexdigest() if use_cache else None
        tensor = wrapper.preprocess(img, cache_key)
        prob, ms = self._infer_tensor(wrapper, tensor)
        # 非目标图像门控：特征取 avgpool 输出（hook 在推理时已缓存）
        feat = wrapper._feat.cpu().numpy()[0] if wrapper._feat is not None else None
        gate = self.gate.evaluate(img, feat, prob, model_key=key)
        result = self._build_result(
            prob, ms, key, image_size=img.size,
            filename=filename, leaf_score=leaf_likelihood_score(img), gate=gate,
        )
        if with_gradcam:
            result["gradcam"] = self.explain(img, tensor, wrapper, result["class_index"])
        return result

    # ---------------- 单张：路径 ----------------
    def predict_path(self, path: str | Path, model_key: Optional[str] = None,
                     with_gradcam: bool = False) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"图片不存在: {p}")
        with open(p, "rb") as f:
            data = f.read()
        return self.predict_bytes(data, p.name, model_key, with_gradcam=with_gradcam)

    # ---------------- 批量 ----------------
    def predict_batch(
        self,
        files: Sequence[Tuple[str, bytes]],
        model_key: Optional[str] = None,
        batch_chunk: int = 16,
    ) -> Dict[str, Any]:
        """批量推理：一次性前向（按 chunk 分块），显著快于逐张循环。

        files: [(filename, bytes), ...]
        返回 {"results": [...], "summary": {...}, "failed": [...]}
        """
        key, wrapper = self._resolve_model(model_key)
        results: List[Dict[str, Any]] = []
        failed: List[Dict[str, str]] = []
        tensors, metas = [], []

        for name, data in files:
            try:
                img = validate_image(data, self.max_image_mb, self.max_image_side)
            except InvalidImageError as e:
                failed.append({"filename": name, "error": str(e)})
                continue
            ck = hashlib.md5(data).hexdigest()
            tensors.append(wrapper.preprocess(img, ck))
            metas.append((name, img.size, leaf_likelihood_score(img), img))

        if tensors:
            if wrapper.device.type == "cuda":
                torch.cuda.synchronize()
            t_all = time.perf_counter()
            for i in range(0, len(tensors), batch_chunk):
                chunk = torch.cat(tensors[i:i + batch_chunk], dim=0)
                with torch.no_grad():
                    logits = wrapper.logits(chunk)
                    probs = torch.softmax(logits.float(), dim=1).cpu().numpy()
                per = (time.perf_counter() - t_all) * 1000 / max(len(tensors), 1)
                feats = wrapper._feat.cpu().numpy() if wrapper._feat is not None else None
                for j, ((name, size, leafs, vimg), prob) in enumerate(
                    zip(metas[i:i + batch_chunk], probs)
                ):
                    # 批量场景用平均耗时估算单图耗时，避免逐张同步的开销失真
                    feat = feats[j] if feats is not None else None
                    gate = self.gate.evaluate(vimg, feat, prob, model_key=key)
                    results.append(self._build_result(prob, per, key, image_size=size,
                                                      filename=name, leaf_score=leafs, gate=gate))
            if wrapper.device.type == "cuda":
                torch.cuda.synchronize()

        summary = self._summarize(results)
        summary["failed_count"] = len(failed)
        return {"results": results, "failed": failed, "summary": summary}

    def _summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts: Dict[str, int] = {cn: 0 for cn in self.class_cn}
        confs = []
        for r in results:
            counts[r["class_name"]] = counts.get(r["class_name"], 0) + 1
            confs.append(r["confidence"])
        n = len(results)
        return {
            "total": n,
            "success_count": n,
            "avg_confidence": round(float(np.mean(confs)), 4) if confs else 0.0,
            "class_counts": counts,
            "disease_count": sum(v for k, v in counts.items() if k != "健康叶片"),
            "healthy_count": counts.get("健康叶片", 0),
        }

    # ---------------- 多模型对比 ----------------
    def compare(self, data: bytes, filename: str = "upload.jpg") -> List[Dict[str, Any]]:
        """同一张图片跑全部已加载模型，返回各模型结果与耗时，用于前端"模型对比"。"""
        out = []
        for key in self.models:
            try:
                r = self.predict_bytes(data, filename, key)
                out.append(r)
            except Exception as e:  # 单个模型失败不影响其他模型
                out.append({"model": key, "error": str(e)})
        return out

    # ---------------- Grad-CAM ----------------
    def explain(self, img: Image.Image, tensor: torch.Tensor, wrapper: _SingleModel,
                class_idx: int) -> Dict[str, Any]:
        from .gradcam import GradCAM, cam_to_base64, overlay_cam

        if wrapper.arch not in self._gradcams:
            self._gradcams[wrapper.arch] = GradCAM(wrapper.model)
        gcam = self._gradcams[wrapper.arch]
        cam, idx = gcam(tensor.to(self.device), class_idx)
        heat = overlay_cam(img, cam)
        return {
            "class_index": idx,
            "heatmap_base64": cam_to_base64(Image.fromarray((cam * 255).astype(np.uint8))),
            "overlay_base64": cam_to_base64(heat),
            "format": "PNG(base64)",
            "cam_raw": cam,
        }

    def predict_with_gradcam(self, data: bytes, filename: str = "upload.jpg",
                             model_key: Optional[str] = None) -> Dict[str, Any]:
        return self.predict_bytes(data, filename, model_key, with_gradcam=True)

    def clear_cache(self) -> None:
        for m in self.models.values():
            m.cache.clear()


# ==========================================================================
#  全局单例（FastAPI 启动时调用一次）
# ==========================================================================
_PREDICTOR: Optional[CornDiseasePredictor] = None


def get_predictor(config_path: Optional[str] = None, force_reload: bool = False) -> CornDiseasePredictor:
    """单例获取：服务启动时预加载，避免每个请求重复加载模型（几十毫秒~数秒）。"""
    global _PREDICTOR
    if _PREDICTOR is None or force_reload:
        cfg = load_config(config_path) if config_path else load_config()
        _PREDICTOR = CornDiseasePredictor(cfg)
    return _PREDICTOR


# ==========================================================================
#  命令行：单图 / 批量 / 目录评估
# ==========================================================================
def _cli() -> None:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="玉米病害单张/批量推理")
    ap.add_argument("input", help="图片路径或目录")
    ap.add_argument("--config", default=None)
    ap.add_argument("--model", default=None, help="模型 key，如 resnet50")
    ap.add_argument("--gradcam", action="store_true", help="输出 Grad-CAM 叠加图")
    ap.add_argument("--out", default="outputs/inference", help="Grad-CAM 保存目录")
    args = ap.parse_args()

    predictor = get_predictor(args.config)
    p = Path(args.input)
    if p.is_dir():
        files = [(f.name, f.read_bytes()) for f in sorted(p.iterdir()) if f.suffix.lower().lstrip(".") in SUPPORTED_EXT]
        res = predictor.predict_batch(files, args.model)
        print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
        for r in res["results"][:10]:
            print(f"{r['filename']:<40} {r['class_name']:<8} {r['confidence']:.4f}")
    else:
        r = predictor.predict_path(p, args.model, with_gradcam=args.gradcam)
        g = r.pop("gradcam", None)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if g:
            import base64
            out = Path(args.out) / f"{p.stem}_gradcam.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(base64.b64decode(g["overlay_base64"]))
            print(f"Grad-CAM 已保存: {out}")


if __name__ == "__main__":
    _cli()
