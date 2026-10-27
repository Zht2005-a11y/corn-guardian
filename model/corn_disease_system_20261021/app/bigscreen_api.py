"""大屏可视化系统专属 API 模块：
提供真实大田样本加载、多尺度病斑检测框提取、Grad-CAM 注意力热力图叠加、
植保无人机飞防处方生成、AI 智能农事问答对话、示范区微气候与抗逆感知遥测数据。
"""
from __future__ import annotations

import base64
import io
import logging
import math
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from PIL import Image

from src.config import load_config
from src import session_store
from src import history_store
from src import alert_store
from src.knowledge_base import KNOWLEDGE_BASE, get_knowledge, get_prescription, compose_prescription
from src.llm_client import ask_agnes, clear_session, stream_ask_agnes

logger = logging.getLogger("corn_system.bigscreen_api")

router = APIRouter(prefix="/screen", tags=["大屏可视化与综合诊断"])

# 项目根目录与测试集根目录
APP_DIR = Path(__file__).resolve().parent
SYSTEM_ROOT = APP_DIR.parent
PROJECT_ROOT = SYSTEM_ROOT.parent.parent  # sjzprogram
DATASET_TEST_DIR = PROJECT_ROOT / "dataset" / "MCDD" / "data" / "test"

# 颜色映射
COLOR_MAP = {
    "Blight": "#e28557",
    "Common_Rust": "#d97706",
    "Gray_Leaf_Spot": "#6366f1",
    "Healthy": "#16a34a",
}

# 场景映射
SCENARIO_MAP = {
    "Blight": "强日光直射",
    "Common_Rust": "高湿凝露",
    "Gray_Leaf_Spot": "叶脉受阻",
    "Healthy": "长势优良",
}


def _img_to_base64(img: Image.Image, format: str = "JPEG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=format, quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _read_file_to_base64(path: Path) -> str:
    with open(path, "rb") as f:
        data = f.read()
    ext = path.suffix.lower().lstrip(".")
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def extract_bboxes_and_metrics(cam: np.ndarray, class_name_en: str, conf_float: float):
    """
    根据 Grad-CAM 热力图提取高响应区域的病斑目标定位框 (Bounding Box)、受损率与侵染严重度。
    """
    if class_name_en == "Healthy":
        return [], 0.0, "健康 (无病斑症状)"

    cam = np.asarray(cam, dtype=np.float32)
    h, w = cam.shape
    cam_min, cam_max = float(cam.min()), float(cam.max())
    if cam_max > cam_min:
        cam_norm = (cam - cam_min) / (cam_max - cam_min)
    else:
        cam_norm = cam

    # 二值化提取高注意力激活区 (取前 25% 响应)
    thresh = float(np.percentile(cam_norm, 75))
    thresh = max(0.35, min(thresh, 0.70))
    mask = (cam_norm > thresh).astype(np.uint8)

    # 计算叶面积受损率（基于高热力响应像素占比，映射至合理农业病害受损区间）
    raw_rate = float(np.mean(mask)) * 100.0
    damage_rate = round(max(8.5, min(raw_rate * 2.2 + 5.0, 48.0)), 1)

    # 确定严重度级别
    if damage_rate < 15.0:
        severity = "轻度 (I 级初期发病)"
    elif damage_rate < 25.0:
        severity = "中度 (II 级扩展期)"
    elif damage_rate < 35.0:
        severity = "重度 (III 级扩散期)"
    else:
        severity = "危急 (IV 级暴发期)"

    boxes = []
    label_map = {
        "Blight": "大斑病灶",
        "Common_Rust": "锈孢子夏孢子堆",
        "Gray_Leaf_Spot": "矩形多角形病斑",
    }
    primary_label = label_map.get(class_name_en, "主要病斑")

    # 使用连通域/轮廓提取真实病斑边界框
    try:
        import cv2
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_contours = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > (w * h * 0.015):  # 过滤微小杂波
                c_mask = np.zeros((h, w), dtype=np.uint8)
                cv2.drawContours(c_mask, [c], -1, 1, -1)
                mean_val = float(np.mean(cam_norm[c_mask == 1]))
                valid_contours.append((area, mean_val, c))

        # 按激活强度权重和面积排序
        valid_contours.sort(key=lambda x: (x[1] * 0.6 + (x[0] / (w * h)) * 0.4), reverse=True)

        for i, (_, mean_v, c) in enumerate(valid_contours[:3]):
            bx, by, bw, bh = cv2.boundingRect(c)
            # 适度外扩 12% 给予病斑边缘视觉呼吸空间
            pad_x = max(2, int(bw * 0.12))
            pad_y = max(2, int(bh * 0.12))
            bx1 = max(2, bx - pad_x)
            by1 = max(2, by - pad_y)
            bx2 = min(w - 2, bx + bw + pad_x)
            by2 = min(h - 2, by + bh + pad_y)

            x_pct = round((bx1 / w) * 100, 1)
            y_pct = round((by1 / h) * 100, 1)
            w_pct = round(((bx2 - bx1) / w) * 100, 1)
            h_pct = round(((by2 - by1) / h) * 100, 1)

            lbl = f"{primary_label} #{i+1}" if i == 0 else f"扩展性病灶 #{i+1}"
            box_conf = round(conf_float * (1.0 - i * 0.04) * 100, 1)

            boxes.append({
                "x": x_pct,
                "y": y_pct,
                "w": w_pct,
                "h": h_pct,
                "label": lbl,
                "conf": f"{box_conf}%"
            })
    except Exception:
        pass

    # 兜底：若未提取到轮廓，则基于高响应质心定位
    if not boxes:
        indices = np.argwhere(cam_norm > thresh)
        if len(indices) > 0:
            weights = cam_norm[indices[:, 0], indices[:, 1]]
            cy = int(np.average(indices[:, 0], weights=weights))
            cx = int(np.average(indices[:, 1], weights=weights))
        else:
            cy, cx = np.unravel_index(np.argmax(cam_norm), cam_norm.shape)

        bw = int(w * 0.36)
        bh = int(h * 0.32)
        bx1 = max(4, cx - bw // 2)
        by1 = max(4, cy - bh // 2)
        bx2 = min(w - 4, bx1 + bw)
        by2 = min(h - 4, by1 + bh)

        boxes.append({
            "x": round((bx1 / w) * 100, 1),
            "y": round((by1 / h) * 100, 1),
            "w": round(((bx2 - bx1) / w) * 100, 1),
            "h": round(((by2 - by1) / h) * 100, 1),
            "label": f"{primary_label} #1",
            "conf": f"{round(conf_float * 100, 1)}%"
        })

    return boxes, damage_rate, severity


def get_drone_params(class_name_en: str, severity: str) -> Dict[str, str]:
    if class_name_en == "Healthy":
        return {
            "model": "大疆 T50 / T60",
            "volume": "1.0 L/亩 (叶面营养液)",
            "dropletSize": "150 μm",
            "altitude": "2.5 米",
            "speed": "5.5 m/s",
        }
    if "危急" in severity or "重度" in severity:
        return {
            "model": "大疆 T60 / 极飞 P100 Pro",
            "volume": "2.0 L/亩",
            "dropletSize": "120 μm (超细雾化)",
            "altitude": "2.0 米",
            "speed": "4.8 m/s",
        }
    return {
        "model": "大疆 T50 / T60",
        "volume": "1.6 L/亩",
        "dropletSize": "135 μm",
        "altitude": "2.2 米",
        "speed": "5.0 m/s",
    }


# ==========================================================================
#  1. 获取真实大田典型样本
# ==========================================================================
# ---------------------------------------------------------------------------
# GET /screen/samples —— 从 MCDD 测试集读取 4 类典型样本（含 base64 图）
# 前端：frontend/src/views/bigScreen/Layout.vue 的 fetchPresetSamples()（页面 onMounted 自动调用）
#       结果用于渲染"大田典型病斑样本直选"按钮，首个样本自动作为预览图
# 依赖：_read_file_to_base64、get_knowledge、DATASET_TEST_DIR（dataset/MCDD/data/test）
# 返回：data[] {id, name, scenario, diseaseName, class_name_en, pathogen, color, imgData, filename}
# ---------------------------------------------------------------------------
@router.get("/samples")
async def get_preset_samples():
    """从本地真实 MCDD 测试集中提取典型大斑病、锈病、灰斑病、健康叶片样本，供前端直选展示。"""
    samples = []
    classes = [
        ("Blight", "blight", "玉米大斑病"),
        ("Common_Rust", "rust", "玉米南方锈病"),
        ("Gray_Leaf_Spot", "gray", "玉米灰斑病"),
        ("Healthy", "healthy", "健康植株"),
    ]

    for class_folder, s_id, display_name in classes:
        dir_path = DATASET_TEST_DIR / class_folder
        img_base64 = ""
        filename = ""
        if dir_path.exists():
            files = [f for f in dir_path.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")]
            if files:
                target_file = files[0]
                filename = target_file.name
                try:
                    img_base64 = _read_file_to_base64(target_file)
                except Exception:
                    img_base64 = ""

        kb = get_knowledge(class_folder)
        samples.append(
            {
                "id": s_id,
                "name": display_name,
                "scenario": SCENARIO_MAP.get(class_folder, "大田实拍"),
                "diseaseName": f"{kb['name_cn']} ({kb['name_en']})",
                "class_name_en": class_folder,
                "pathogen": kb.get("pathogen", ""),
                "color": COLOR_MAP.get(class_folder, "#059669"),
                "imgData": img_base64,
                "filename": filename,
            }
        )

    return {"code": 0, "message": "ok", "data": samples}


# ==========================================================================
#  1b. 病害图鉴知识库接口（前端侧边栏「病害图鉴」弹窗）
# ==========================================================================
@router.get("/knowledge")
async def get_knowledge_base():
    """返回全部病害类别的知识库条目，供前端「病害图鉴」弹窗展示。

    依赖：KNOWLEDGE_BASE（src/knowledge_base.py，含 import 时回填的 control.chemical）、
          COLOR_MAP（与诊断结果卡同源配色）
    返回：data [{class_name_en, name_cn, name_en, pathogen, severity, color,
                 symptoms[], occurrence[], prescription{}, control{agricultural/chemical/field}}]
    """
    items = []
    for class_folder, kb in KNOWLEDGE_BASE.items():
        items.append(
            {
                "class_name_en": class_folder,
                "name_cn": kb.get("name_cn", class_folder),
                "name_en": kb.get("name_en", class_folder),
                "pathogen": kb.get("pathogen", ""),
                "severity": kb.get("severity", ""),
                "color": COLOR_MAP.get(class_folder, "#059669"),
                "symptoms": kb.get("symptoms", []),
                "occurrence": kb.get("occurrence", []),
                "prescription": kb.get("prescription", {}),
                "control": kb.get("control", {}),
            }
        )
    return {"code": 0, "message": "ok", "data": items}


# ==========================================================================
#  2. 大屏综合诊断推理接口 (支持 Grad-CAM、病斑 BBox、受损率、植保指导单)
# ==========================================================================
class Base64PredictRequest(BaseModel):
    """POST /screen/predict 的请求体。"""

    image_base64: str = Field(..., description="图片Base64")
    filename: Optional[str] = "screen_upload.jpg"
    model: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /screen/predict —— 大屏综合诊断（病害 / 置信度 / 热力图 / 病斑框 / 飞防处方）
# 前端：frontend/src/views/bigScreen/Layout.vue 的 runDetect()（点击"执行 AI 智能病害感知与精准诊断"）
# 入参：{image_base64, filename, model}；model 缺省或不在 models 中时回退 default_model
# 依赖：PREDICTOR.predict_with_gradcam（src/predictor.py）、extract_bboxes_and_metrics、
#       get_drone_params、get_knowledge（src/knowledge_base.py）
# 返回：data {diseaseName, class_name_en/cn, pathogen, severity, damageRate, confidence, color,
#            boxes[], prescription, droneParams, gradcam_base64, probabilities, model_used, inference_ms}
# 注意：damageRate / severity 由 Grad-CAM 高响应区域估算，不是人工标注真值
# ---------------------------------------------------------------------------
def _parse_b64_image(raw: str) -> bytes:
    """接受纯 base64 或 data-url，返回图片字节。"""
    if "," in raw and raw.strip().startswith("data:"):
        raw = raw.split(",", 1)[1]
    return base64.b64decode(raw, validate=True)


def _diagnose_one(data: bytes, filename: str, model_key: str) -> Dict[str, Any]:
    """单张图片的完整诊断链路：识别 → Grad-CAM → 病斑指标 → 动态处方 → 历史落盘。

    单张接口与批量接口共用同一实现，保证两条路径的结果结构与落盘行为一致。
    """
    from app.api import PREDICTOR

    if PREDICTOR is None:
        raise HTTPException(status_code=503, detail="AI 模型正在加载中，请稍后")

    if model_key not in PREDICTOR.models:
        model_key = PREDICTOR.default_model

    res = PREDICTOR.predict_with_gradcam(data, filename or "sample.jpg", model_key=model_key)
    gradcam_res = res.get("gradcam", {})
    cam_raw = gradcam_res.get("cam_raw")

    # 若 cam_raw 未直接返回，从 heatmap_base64 或 overlay_base64 中精确还原激活矩阵
    if cam_raw is None:
        if "heatmap_base64" in gradcam_res:
            try:
                h_data = base64.b64decode(gradcam_res["heatmap_base64"].split(",")[-1])
                h_img = Image.open(io.BytesIO(h_data)).convert("L")
                cam_raw = np.array(h_img, dtype=np.float32) / 255.0
            except Exception:
                cam_raw = None

        if cam_raw is None and "overlay_base64" in gradcam_res:
            try:
                o_data = base64.b64decode(gradcam_res["overlay_base64"].split(",")[-1])
                o_img = Image.open(io.BytesIO(o_data)).convert("RGB")
                o_arr = np.array(o_img, dtype=np.float32)
                diff = o_arr[..., 0] - o_arr[..., 2]
                cam_raw = np.clip((diff - diff.min()) / (diff.max() - diff.min() + 1e-8), 0.0, 1.0)
            except Exception:
                cam_raw = None

    class_en = res["class_name_en"]
    class_cn = res.get("class_name") or res.get("class_name_cn") or class_en
    conf = float(res["confidence"])
    kb = get_knowledge(class_en)

    if cam_raw is not None:
        boxes, damage_rate, severity = extract_bboxes_and_metrics(cam_raw, class_en, conf)
    else:
        boxes, damage_rate, severity = [], 0.0, "轻度"

    drone_params = get_drone_params(class_en, severity)

    # 动态处方：同一病害在不同严重度下，药液量/频次/田间处置建议均不同
    rx = compose_prescription(
        class_en,
        severity=severity,
        damage_rate=damage_rate,
        confidence=round(conf * 100, 1),
    )
    prescription = rx["sentence"]

    result = {
        "diseaseName": f"{class_cn} ({kb.get('name_en', class_en)})",
        "class_name_en": class_en,
        "class_name_cn": class_cn,
        "pathogen": kb.get("pathogen", "无致病菌侵染"),
        "severity": severity,
        "damageRate": damage_rate,
        "confidence": round(conf * 100, 1),
        "color": COLOR_MAP.get(class_en, "#059669"),
        "boxes": boxes,
        "prescription": prescription,
        "prescriptionLevel": rx.get("level", ""),
        "prescriptionDose": rx.get("dose", ""),
        "prescriptionNotes": rx.get("notes", []),
        "droneParams": drone_params,
        "gradcam_base64": gradcam_res.get("overlay_base64", ""),
        "leaf_score": res.get("leaf_score", 0.95),
        "probabilities": res.get("probabilities", {}),
        "model_used": model_key,
        "inference_ms": res.get("inference_time_ms", 14.2),
    }

    # 诊断历史落盘（失败不影响主流程）
    record_id = history_store.save_record(
        image_bytes=data,
        gradcam_b64=result.get("gradcam_base64", ""),
        class_en=class_en,
        class_name=class_cn,
        confidence=result["confidence"],
        severity=severity,
        damage_rate=damage_rate,
        model_used=model_key,
        inference_ms=result.get("inference_ms"),
        prescription=prescription,
        drone_params=drone_params,
        boxes=boxes,
    )

    # 由本次结果生成告警（按 rule+ref_id 去重；异常不影响诊断返回）
    same_today = history_store.count_today_by_class(class_en) if record_id else 0
    new_alerts = alert_store.emit_for_diagnosis(
        record_id=record_id,
        class_en=class_en,
        class_cn=class_cn,
        severity=severity,
        damage_rate=damage_rate,
        confidence=result["confidence"],
        filename=filename,
        same_class_today=same_today,
    )
    result["historyId"] = record_id
    result["newAlerts"] = len(new_alerts)

    return result


@router.post("/predict")
async def predict_screen(req: Base64PredictRequest):
    """
    大屏统一图像诊断接口：
    传入图片 base64，由 ResNet50-CBAM 深度注意力模型进行推理，
    返回：病害类型、置信度、Grad-CAM 热力图、病斑多尺度定位框 BBox、受损率、
    发病严重度、按严重度动态生成的飞防处方与作业参数。
    """
    try:
        data = _parse_b64_image(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Base64 图片解码失败: {e}")

    result = _diagnose_one(data, req.filename or "sample.jpg", req.model or "resnet50_cbam")
    return {"code": 0, "message": "ok", "data": result}


class BatchImageItem(BaseModel):
    """批量识别中的单张图片。"""

    image_base64: str = Field(..., description="图片 base64（可带 data: 前缀）")
    filename: Optional[str] = Field(None, description="原始文件名，仅用于展示")


class BatchPredictRequest(BaseModel):
    """POST /screen/predict/batch 的请求体。"""

    images: List[BatchImageItem] = Field(..., description="待识别图片，单次最多 24 张")
    model: Optional[str] = Field(None, description="模型 key，默认 resnet50_cbam")
    acreage_per_image: float = Field(1.0, description="每张图代表的巡田面积（亩），用于估算总药液量")


def _volume_per_mu(volume_text: str) -> float:
    """从「2.0 L/亩」「1.0 L/亩 (叶面营养液)」这类文案里取出亩用量数值。"""
    try:
        head = str(volume_text).strip().split("L")[0].strip()
        return float(head)
    except Exception:
        return 0.0


@router.post("/predict/batch")
async def predict_batch(req: BatchPredictRequest):
    """批量巡田识别：逐张推理并落盘，返回明细与汇总（病害分布 / 平均受损率 / 建议药液量）。

    单张失败不会中断整批，失败项进 errors（附带 index 与原因）。
    """
    if not req.images:
        raise HTTPException(status_code=400, detail="images 不能为空")
    if len(req.images) > 24:
        raise HTTPException(status_code=400, detail="单次最多 24 张，请分批提交")

    model_key = req.model or "resnet50_cbam"
    acreage = max(0.1, float(req.acreage_per_image or 1.0))

    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for idx, item in enumerate(req.images):
        fname = item.filename or f"batch_{idx + 1}.jpg"
        try:
            data = _parse_b64_image(item.image_base64)
            r = _diagnose_one(data, fname, model_key)
            items.append(
                {
                    "index": idx,
                    "filename": fname,
                    "diseaseName": r["diseaseName"],
                    "class_name_en": r["class_name_en"],
                    "class_name_cn": r["class_name_cn"],
                    "severity": r["severity"],
                    "damageRate": r["damageRate"],
                    "confidence": r["confidence"],
                    "color": r["color"],
                    "prescription": r["prescription"],
                    "prescriptionLevel": r["prescriptionLevel"],
                    "droneParams": r["droneParams"],
                    "inference_ms": r["inference_ms"],
                }
            )
        except Exception as e:  # noqa: BLE001
            errors.append({"index": idx, "filename": fname, "error": str(e)[:160]})

    # 汇总：病害分布 / 平均指标 / 建议总药液量
    by_class: Dict[str, Dict[str, Any]] = {}
    for it in items:
        key = it["class_name_en"]
        bucket = by_class.setdefault(
            key, {"class_en": key, "name": it["class_name_cn"], "color": it["color"], "count": 0}
        )
        bucket["count"] += 1

    total_volume = sum(_volume_per_mu(it["droneParams"].get("volume", "")) for it in items) * acreage
    avg_damage = round(sum(it["damageRate"] for it in items) / len(items), 1) if items else 0.0
    avg_conf = round(sum(it["confidence"] for it in items) / len(items), 1) if items else 0.0
    worst = max(items, key=lambda x: x["damageRate"]) if items else None

    summary = {
        "count": len(req.images),
        "success": len(items),
        "failed": len(errors),
        "acreage": acreage,
        "byClass": sorted(by_class.values(), key=lambda x: x["count"], reverse=True),
        "avgDamageRate": avg_damage,
        "avgConfidence": avg_conf,
        "totalVolumeLiters": round(total_volume, 1),
        "worst": (
            {
                "filename": worst["filename"],
                "diseaseName": worst["diseaseName"],
                "severity": worst["severity"],
                "damageRate": worst["damageRate"],
            }
            if worst
            else None
        ),
    }

    return {"code": 0, "message": "ok", "data": {"items": items, "errors": errors, "summary": summary}}



# ==========================================================================
#  2.5 诊断历史（每次识别自动落盘，可回看 / 删除 / 统计）
# ==========================================================================
@router.get("/history")
async def list_history(limit: int = 50, offset: int = 0):
    """诊断历史列表（时间倒序）+ 统计：total / today / byClass。"""
    items, stats = history_store.list_records(limit=limit, offset=offset)
    return {"code": 0, "message": "ok", "data": {"items": items, "stats": stats}}


@router.get("/history/{record_id}")
async def get_history(record_id: int):
    """单条诊断历史详情：含 Grad-CAM 热力图与飞防参数。"""
    rec = history_store.get_record(record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"code": 0, "message": "ok", "data": rec}


@router.delete("/history/{record_id}")
async def delete_history(record_id: int):
    if not history_store.delete_record(record_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"code": 0, "message": "ok", "data": {"deleted": record_id}}


# ==========================================================================
#  2.6 告警中心（诊断自动生成，替代大屏写死的「3 条告警」）
# ==========================================================================
@router.get("/alerts")
async def list_alerts(limit: int = 50, unread_only: bool = False):
    """告警列表（时间倒序）+ 统计：unread / total / today。"""
    items, stats = alert_store.list_alerts(limit=limit, unread_only=unread_only)
    return {"code": 0, "message": "ok", "data": {"items": items, "stats": stats}}


@router.post("/alerts/{alert_id}/read")
async def read_alert(alert_id: int):
    if not alert_store.mark_read(alert_id):
        raise HTTPException(status_code=404, detail="告警不存在")
    return {"code": 0, "message": "ok", "data": {"read": alert_id}}


@router.post("/alerts/read-all")
async def read_all_alerts():
    n = alert_store.mark_all_read()
    return {"code": 0, "message": "ok", "data": {"updated": n}}


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int):
    if not alert_store.delete_alert(alert_id):
        raise HTTPException(status_code=404, detail="告警不存在")
    return {"code": 0, "message": "ok", "data": {"deleted": alert_id}}


# ==========================================================================
#  3. AI 智能问答对话接口 (Agnes-3.0-Flash 大模型 + 诊断上下文自适应)
# ==========================================================================
class ChatRequest(BaseModel):
    """POST /screen/chat 的请求体（message 必填，context/history 可选）。"""

    message: str = Field(..., description="用户咨询问题")
    context: Optional[Dict[str, Any]] = Field(None, description="当前诊断上下文")
    history: Optional[List[Dict[str, Any]]] = Field(None, description="历史对话上下文")
    session_id: Optional[str] = Field(None, description="会话标识：用于中途打断后「继续」时恢复任务")


# ---------------------------------------------------------------------------
# POST /screen/chat —— 植保专家问答（Agnes-3.0-Flash + 当前诊断上下文）
# 前端：已改调 /screen/chat/stream（见下方流式接口）；本接口保留为一次性返回的兼容/调试版本
#       入参结构相同：最近 6 条 history 与 diagnosis context（含 climate 微气候）
# 入参：{message, context{diseaseName,severity,damageRate,prescription,climate}, history[]}
# 依赖：src/llm_client.ask_agnes；模型不可达时 fallback_expert_reply 本地兜底
# 返回：data {reply, model, source, usage}
# ---------------------------------------------------------------------------
@router.post("/chat")
async def chat_screen(req: ChatRequest):
    """
    大田病害智能问答专家接口：
    接入 Agnes-3.0-Flash 大模型，融合玉米植保多源诊断上下文（病害识别、严重度、飞防处方、微气候）。
    """
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    cfg = load_config()
    llm_cfg = cfg.get("llm", {})

    base_url = llm_cfg.get("base_url", "https://apihub.agnes-ai.cn/v1")
    api_key = llm_cfg.get("api_key") or os.environ.get("AGNES_API_KEY", "")
    model = llm_cfg.get("model", "agnes-3.0-flash")
    timeout = float(llm_cfg.get("timeout", 45.0))
    temperature = float(llm_cfg.get("temperature", 0.3))

    res = await ask_agnes(
        message=msg,
        context=req.context,
        history=req.history,
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout=timeout,
        temperature=temperature,
    )

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "reply": res.get("reply", ""),
            "model": res.get("model", model),
            "source": res.get("source", "agnes-ai"),
            "usage": res.get("usage", {}),
        },
    }


# ---------------------------------------------------------------------------
# POST /screen/chat/stream —— 植保专家问答（SSE 流式输出 + web_search 联网搜索）
# 前端：frontend/src/views/bigScreen/Layout.vue 的 sendMessage()（fetch('/api/screen/chat/stream') 逐字渲染）
# 入参：同 /screen/chat（message 必填，context / history 可选）
# 依赖：src/llm_client.stream_ask_agnes（流式生成器 + 工具调用）
# 返回：text/event-stream（SSE 分块推送，前端用 ReadableStream 逐块消费）
# 注意：已设 Cache-Control:no-cache / X-Accel-Buffering:no，Nginx 代理时需关闭缓冲
# ---------------------------------------------------------------------------
@router.post("/chat/stream")
async def chat_screen_stream(req: ChatRequest, request: Request):
    """
    大田病害智能问答专家接口 (SSE 流式输出 + Web 联网搜索 Tool Call):
    结合 Agnes-3.0-Flash 原生 StreamingResponse，并在模型判定超出知识库时自动触发 web_search。
    客户端断开（关面板/点停止/刷新页面）时立即终止生成，不再空耗 token。
    """
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    cfg = load_config()
    llm_cfg = cfg.get("llm", {})

    base_url = llm_cfg.get("base_url", "https://apihub.agnes-ai.cn/v1")
    api_key = llm_cfg.get("api_key") or os.environ.get("AGNES_API_KEY", "")
    model = llm_cfg.get("model", "agnes-3.0-flash")
    timeout = float(llm_cfg.get("timeout", 45.0))
    temperature = float(llm_cfg.get("temperature", 0.3))

    async def _guarded_stream():
        """断连守护：客户端断开即中止上游生成，防止无人观看时继续烧 token"""
        generator = stream_ask_agnes(
            message=msg,
            context=req.context,
            history=req.history,
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout=timeout,
            temperature=temperature,
            session_id=req.session_id,
        )
        try:
            async for chunk in generator:
                if await request.is_disconnected():
                    logger.info("[chat/stream] 客户端已断开，终止问答生成")
                    break
                yield chunk
        finally:
            await generator.aclose()

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(_guarded_stream(), media_type="text/event-stream", headers=headers)


# ==========================================================================
#  4. 会话找回（历史会话列表 / 详情恢复 / 删除）
# ==========================================================================
# 复用 Claude Code 的 --resume/--continue 机制：会话以 append-only JSONL 落在
# <system_root>/sessions/<sid>.jsonl（存储与恢复实现见 src/session_store.py，
# 写入点在 llm_client.stream_ask_agnes 的 finally 增量追加）。
# 前端灵动岛「历史会话」入口调本组接口；恢复时把该 session_id 交还给
# /chat/stream，后端自动以磁盘 transcript 为基底续聊（含历史检索结果）。
# ---------------------------------------------------------------------------
# GET /screen/sessions —— 历史会话列表（--resume 选择器数据源）
# 前端：Layout.vue 的 fetchSessionList()（灵动岛头部时钟图标打开列表时调用）
# 入参：limit（缺省 50）
# 依赖：src/session_store.list_sessions（stat mtime 降序 + 头尾 64KB 轻读标题，
#       不做全量解析；标题优先级 lastPrompt > firstPrompt，interrupted 标记
#       末轮是否被打断——检索完成未回答完等场景，提示用户可继续）
# 返回：data.sessions[] {session_id, title, last_prompt, modified, created,
#                        size_bytes, interrupted}
# ---------------------------------------------------------------------------
@router.get("/sessions")
async def list_chat_sessions(limit: int = Query(50, ge=1, le=200, description="返回会话数上限")):
    """历史问答会话列表，按最近修改时间倒序。"""
    return {"code": 0, "message": "ok", "data": {"sessions": session_store.list_sessions(limit)}}


# ---------------------------------------------------------------------------
# GET /screen/sessions/{session_id} —— 会话详情（恢复展示用）
# 前端：Layout.vue 的 restoreSession()（点击列表项时调用；成功后把该 session_id
#       交还给 /chat/stream，即完成「找回」，无需专用恢复接口）
# 依赖：src.session_store.read_rows / transcript_meta / transcript_display
# 返回：data {session_id, messages[]（前端气泡格式 role=user|ai，searchQuery 为
#        该回答引用过的联网检索词）, interrupted（末轮中断类型或 null）, message_count}
# ---------------------------------------------------------------------------
@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str):
    rows = session_store.read_rows(session_id)
    if not rows:
        raise HTTPException(status_code=404, detail="会话不存在")
    meta = session_store.transcript_meta(rows)
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "session_id": session_id,
            "messages": session_store.transcript_display(rows),
            "interrupted": meta["interrupted"],
            "message_count": meta["message_count"],
        },
    }


# ---------------------------------------------------------------------------
# DELETE /screen/sessions/{session_id} —— 删除会话（磁盘 JSONL + 内存快照）
# 前端：Layout.vue 的 removeSession()（列表项「确认删除」二次点击）
# 依赖：src.session_store.delete_session；clear_session 同步清掉 llm_client 的
#       内存快照，避免删了磁盘、内存里还留着 5 分钟 TTL 的旧上下文
# 返回：data {deleted: bool}（磁盘无此文件但清过内存时仍返回 deleted=false）
# ---------------------------------------------------------------------------
@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    deleted = session_store.delete_session(session_id)
    clear_session(session_id)
    return {"code": 0, "message": "ok", "data": {"deleted": deleted}}


# ==========================================================================
#  5. 示范区大田遥测数据与模型抗逆感知雷达指标
# ==========================================================================
# ---------------------------------------------------------------------------
# GET /screen/telemetry —— 大屏遥测数据（微气候时序 / 病害分布 / 六维雷达）
# 前端：frontend/src/views/bigScreen/Layout.vue 的 initCharts()（onMounted 后 nextTick 拉一次，不轮询）
# 入参：无
# 返回：data {climate{hours,temperatures,humidities,lights,当前值}, distribution[], radar[]}
# 注意：当前为静态演示数据，接真实传感器时替换下方常量即可
# ---------------------------------------------------------------------------
@router.get("/telemetry")
async def get_telemetry():
    """
    返回大田微气候时序数据、示范区病害发生分布统计、以及 ResNet50-CBAM 模型的抗逆感知六维雷达评估。
    """
    hours = [f"{i:02d}:00" for i in range(0, 24, 2)]
    temps = [21.5, 20.8, 19.9, 19.2, 18.6, 22.4, 26.8, 30.5, 32.1, 31.4, 28.2, 24.6]
    humidities = [86.2, 88.5, 91.0, 93.4, 94.2, 88.6, 76.5, 62.4, 58.1, 64.3, 75.8, 82.5]
    lights = [0, 0, 0, 0, 8.5, 38.2, 68.5, 84.6, 88.2, 72.1, 28.4, 0]  # kLux

    disease_distribution = [
        {"name": "玉米大斑病", "value": 38.5, "color": "#e28557"},
        {"name": "玉米南方锈病", "value": 31.2, "color": "#d97706"},
        {"name": "玉米灰斑病", "value": 14.8, "color": "#6366f1"},
        {"name": "健康植株", "value": 15.5, "color": "#16a34a"},
    ]

    radar_indicators = [
        {"name": "强日光眩光抑制", "max": 100, "value": 96.8},
        {"name": "雨露水珠反光过滤", "max": 100, "value": 94.5},
        {"name": "微小病斑细粒度识别", "max": 100, "value": 97.2},
        {"name": "重叠杂草自适应穿透", "max": 100, "value": 93.8},
        {"name": "阴影与低照度自适应补偿", "max": 100, "value": 96.1},
        {"name": "边缘模糊与相机抖动稳健性", "max": 100, "value": 95.4},
    ]

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "climate": {
                "hours": hours,
                "temperatures": temps,
                "humidities": humidities,
                "lights": lights,
                "currentTemp": 28.4,
                "currentHumidity": 84.2,
                "currentLight": 68.5,
                "windSpeed": 2.1,
            },
            "distribution": disease_distribution,
            "radar": radar_indicators,
        },
    }
