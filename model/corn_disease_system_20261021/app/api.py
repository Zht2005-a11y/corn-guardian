"""FastAPI 后端推理服务（玉米病虫害智能识别系统）——单文件应用。

启动：
    uvicorn app.api:app --host 0.0.0.0 --port 8010
    # 或：python app/api.py

接口一览（统一响应格式 {code, message, data, request_id, elapsed_ms}）：
    POST /auth/login           账号密码登录（返回 Bearer 令牌，勾选记住我 7 天有效）
    POST /auth/register        注册账号
    GET  /auth/me              当前登录用户
    POST /auth/logout          退出登录（令牌立即失效）
    GET  /auth/config          登录页配置（注册开关 / 演示账号）
    GET  /                     服务首页（接口自述，避免"忘记地址"）
    GET  /health               健康检查（含模型加载状态、设备、缓存命中）
    GET  /models               可用模型列表 + 类别映射
    GET  /knowledge            4 类病害知识库
    GET  /knowledge/{key}      单个类别知识库（key 可为英文名或中文名或索引）
    GET  /dataset/info         数据集统计（各类别图片数）
    POST /predict              单图识别（multipart: file）
    POST /predict/gradcam      单图识别 + Grad-CAM 热力图（base64）
    POST /predict/batch        多图批量识别（multipart: files）
    POST /predict/compare      多模型对比识别
    POST /predict/base64       前端传 base64 图片（可选，方便 Streamlit / 小程序）

文档：http://localhost:8010/docs  （Swagger，可现场演示接口）
"""
from __future__ import annotations

import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

# 允许 `python app/api.py` 直接运行（把项目根目录加入 sys.path）
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, Response  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from src.config import get_class_cn, get_class_names, load_config  # noqa: E402
from src.knowledge_base import KNOWLEDGE_BASE, get_knowledge  # noqa: E402
from src.predictor import (  # noqa: E402
    CornDiseasePredictor,
    InvalidImageError,
    SUPPORTED_EXT,
    confidence_level,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("corn.api")

CONFIG = load_config()
SERVER_CFG = CONFIG.get("server", {})
MAX_FILES = 20  # 单次批量上传上限


# ==========================================================================
#  统一响应模型
# ==========================================================================
class ApiResponse(BaseModel):
    code: int = Field(0, description="业务状态码，0 表示成功")
    message: str = Field("ok", description="提示信息")
    data: Optional[Any] = Field(None, description="数据体")
    request_id: Optional[str] = Field(None, description="请求追踪 ID")
    elapsed_ms: Optional[float] = Field(None, description="服务端耗时（毫秒）")


def ok(data: Any, message: str = "ok") -> Dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


class Base64Request(BaseModel):
    """POST /predict/base64 的请求体。"""

    image_base64: str = Field(..., description="图片 base64（可带 data:image/jpeg;base64, 前缀）")
    filename: str = "upload.jpg"
    model: Optional[str] = None
    gradcam: bool = False


# ==========================================================================
#  应用生命周期：启动时预加载模型（单例）
# ==========================================================================
PREDICTOR: Optional[CornDiseasePredictor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global PREDICTOR
    t0 = time.perf_counter()
    logger.info("正在加载模型（单例预加载）...")
    PREDICTOR = CornDiseasePredictor(
        config=CONFIG,
        model_specs=SERVER_CFG.get("models"),
        default_model=SERVER_CFG.get("default_model"),
    )
    app.state.predictor = PREDICTOR
    for key, rep in PREDICTOR.load_report.items():
        tag = "已加载权重" if rep["loaded"] else "[警告] 未找到权重，使用随机初始化（仅用于联调）"
        logger.info(f"  模型 {key:<22} arch={rep['arch']:<20} {tag}  ({rep['load_ms']} ms)")
    logger.info(f"模型加载完成，设备={PREDICTOR.device}，耗时 {time.perf_counter() - t0:.2f}s")
    yield
    logger.info("服务关闭，释放资源")
    PREDICTOR = None


app = FastAPI(
    title="玉米病虫害智能识别系统 API",
    description="基于 ResNet50 / MobileNetV3 迁移学习的玉米叶部病害识别服务",
    version="1.0.0",
    lifespan=lifespan,
)

from app.auth import check_request as auth_check
from app.auth import router as auth_router
from app.bigscreen_api import router as screen_router

app.include_router(auth_router)
app.include_router(screen_router)


# ==========================================================================
#  中间件：统一包装响应 + 错误处理 + 耗时统计
# ==========================================================================
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
    t0 = time.perf_counter()

    # ---- 登录认证：除公开路径（/、/health、/auth/*、Swagger）外一律要求令牌 ----
    denied = auth_check(request)
    if denied is not None:
        status_code, body = denied
        resp = JSONResponse(status_code=status_code, content={**body, "request_id": rid})
        resp.headers["X-Request-Id"] = rid
        resp.headers["X-Elapsed-Ms"] = "0.0"
        return resp

    try:
        response = await call_next(request)
    except Exception:  # 兜底，保证不会返回裸 500 堆栈给前端
        logger.exception(f"[{rid}] 未捕获异常")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误，请查看后端日志", "data": None, "request_id": rid},
        )
    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    response.headers["X-Request-Id"] = rid
    response.headers["X-Elapsed-Ms"] = str(elapsed)
    return response


# CORS 必须最后注册：Starlette 后加的外层，这样鉴权失败返回的 401 也会带上跨域头，
# 前端才能读到「登录已过期」而不是被浏览器吞成 Network Error。
app.add_middleware(
    CORSMiddleware,
    allow_origins=SERVER_CFG.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidImageError)
async def invalid_image_handler(request: Request, exc: InvalidImageError):
    return JSONResponse(status_code=400, content={"code": 400, "message": str(exc), "data": None})


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    return JSONResponse(status_code=400, content={"code": 400, "message": str(exc).strip("'"), "data": None})


# ==========================================================================
#  依赖
# ==========================================================================
def _predictor() -> CornDiseasePredictor:
    p = PREDICTOR or getattr(app.state, "predictor", None)
    if p is None:
        raise HTTPException(status_code=503, detail="模型尚未加载完成，请稍后重试")
    return p


def _validate_upload(file: UploadFile) -> None:
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in SUPPORTED_EXT:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型 .{ext}，仅支持 {sorted(SUPPORTED_EXT)}")


async def _read_file(file: UploadFile) -> bytes:
    data = await file.read()
    limit = float(SERVER_CFG.get("max_upload_mb", 10)) * 1024 * 1024
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大（{len(data)/1024/1024:.1f}MB），上限 {SERVER_CFG.get('max_upload_mb', 10)}MB",
        )
    return data


# ==========================================================================
#  基础接口
# ==========================================================================
# ---------------------------------------------------------------------------
# GET /favicon.ico —— 浏览器自动请求的站点图标
# 前端：无需调用（浏览器自动发起）；返回 204 避免日志里出现无意义的 404
# ---------------------------------------------------------------------------
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """浏览器默认会请求 /favicon.ico，返回 204 避免日志里出现无意义的 404。"""
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# GET / —— 服务首页（接口自述，便于直接打开 8010 端口确认服务是否存活）
# 前端：未调用；用于浏览器 / Swagger 查看服务名、版本与接口清单
# 返回：{name, version, docs, endpoints[]}
# ---------------------------------------------------------------------------
@app.get("/", tags=["基础"])
async def index():
    return ok(
        {
            "name": "玉米病虫害智能识别系统 API",
            "version": app.version,
            "docs": "/docs",
            "endpoints": [
                "GET  /health",
                "GET  /models",
                "GET  /knowledge",
                "GET  /dataset/info",
                "POST /predict",
                "POST /predict/gradcam",
                "POST /predict/batch",
                "POST /predict/compare",
                "POST /predict/base64",
            ],
        }
    )


# ---------------------------------------------------------------------------
# GET /health —— 健康检查（设备、模型加载状态、缓存命中、时间戳）
# 前端：未调用；大屏顶部"在线"状态实际由 /screen/samples 是否成功推断
# 依赖：PREDICTOR.load_report（src/predictor.py）与各模型 LRU 缓存统计
# 返回：{status, device, models{key:{loaded,arch,val_acc}}, default_model, cache, timestamp}
# ---------------------------------------------------------------------------
@app.get("/health", tags=["基础"])
async def health():
    p = _predictor()
    return ok(
        {
            "status": "healthy",
            "device": str(p.device),
            "models": {
                k: {
                    "loaded": v["loaded"],
                    "arch": v["arch"],
                    "val_acc": v["val_acc_in_ckpt"],
                }
                for k, v in p.load_report.items()
            },
            "default_model": p.default_model,
            "cache": {k: v.cache.stats for k, v in p.models.items()},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


# ---------------------------------------------------------------------------
# GET /models —— 可用模型列表 + 类别与索引映射
# 前端：未调用；供联调或后续前端扩展模型下拉框使用
# 依赖：predictor.load_report、src/config.py 的 get_class_names / get_class_cn
# 返回：{default_model, models, class_names[], class_names_cn[]}
# ---------------------------------------------------------------------------
@app.get("/models", tags=["模型"])
async def list_models():
    p = _predictor()
    return ok(
        {
            "default_model": p.default_model,
            "models": p.load_report,
            "class_names": get_class_names(CONFIG),
            "class_names_cn": [get_class_cn(i) for i in range(len(get_class_names(CONFIG)))],
        }
    )


# ---------------------------------------------------------------------------
# GET /knowledge —— 4 类病害知识库概览
# 前端：未调用（大屏所需知识由 /screen/samples、/screen/predict 内联返回）
# 依赖：src/knowledge_base.KNOWLEDGE_BASE
# 返回：{类别key: {class_index, name_cn, name_en, pathogen}}
# ---------------------------------------------------------------------------
@app.get("/knowledge", tags=["知识库"])
async def list_knowledge():
    return ok(
        {
            key: {
                "class_index": i,
                "name_cn": v["name_cn"],
                "name_en": v["name_en"],
                "pathogen": v["pathogen"],
            }
            for i, (key, v) in enumerate(KNOWLEDGE_BASE.items())
        }
    )


# ---------------------------------------------------------------------------
# GET /knowledge/{key} —— 单个类别完整知识
# 前端：未调用；key 支持 英文名 / 中文名 / 索引（Blight、玉米大斑病、0）
# 依赖：src/knowledge_base.get_knowledge；未知类别返回 404
# 返回：{key, name_cn, name_en, pathogen, symptoms[], occurrence[], control{}, severity}
# ---------------------------------------------------------------------------
@app.get("/knowledge/{key}", tags=["知识库"])
async def knowledge_detail(key: str):
    """key 支持: Blight / 玉米大斑病 / 0 三种写法。"""
    keys = list(KNOWLEDGE_BASE.keys())
    if key.isdigit() and 0 <= int(key) < len(keys):
        key = keys[int(key)]
    if key not in KNOWLEDGE_BASE:
        for k, v in KNOWLEDGE_BASE.items():
            if key in (v["name_cn"], v["name_en"]):
                key = k
                break
    if key not in KNOWLEDGE_BASE:
        raise HTTPException(status_code=404, detail=f"未找到类别 '{key}'")
    return ok({"key": key, **get_knowledge(key)})


# ---------------------------------------------------------------------------
# GET /dataset/info —— 数据集统计（train/test 总数、各类别分布）
# 前端：未调用；答辩时可直接在浏览器 / Swagger 展示数据集构成
# 依赖：src/dataset.py 的 collect_samples（懒加载，无需安装 torch）
# 返回：{sources, class_names, train_total, test_total, train_distribution, test_distribution}
# ---------------------------------------------------------------------------
@app.get("/dataset/info", tags=["基础"])
async def dataset_info():
    """统计各数据集各类别图片数量（答辩时可展示数据集构成）。"""
    from src.config import get_class_names as _names
    from src.dataset import collect_samples

    train_samples, test_samples, info = collect_samples(CONFIG)
    return ok(
        {
            "sources": info["sources"],
            "class_names": _names(CONFIG),
            "train_total": info["train_total"],
            "test_total": info["test_total"],
            "train_distribution": info["train_distribution"],
            "test_distribution": info["test_distribution"],
        }
    )


# ==========================================================================
#  识别接口
# ==========================================================================
# ---------------------------------------------------------------------------
# POST /predict —— 单张图片识别（multipart 上传）
# 前端：未调用（大屏单图诊断走 /screen/predict）
# 入参：file（必填，multipart）、model（可选 query，缺省取 server.default_model）
# 依赖：predictor.predict_bytes（src/predictor.py）+ get_knowledge
# 返回：预测结果字段（class_name_en/confidence/probabilities 等）+ knowledge
# ---------------------------------------------------------------------------
@app.post("/predict", tags=["识别"], summary="单张图片识别")
async def predict(
    file: UploadFile = File(..., description="待识别的玉米叶片图片"),
    model: Optional[str] = Query(None, description="模型 key，默认取配置中的 default_model"),
):
    p = _predictor()
    _validate_upload(file)
    data = await _read_file(file)
    t0 = time.perf_counter()
    result = p.predict_bytes(data, file.filename or "upload.jpg", model_key=model)
    result["knowledge"] = get_knowledge(result["class_name_en"])
    body = ok(result)
    body["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return body


# ---------------------------------------------------------------------------
# POST /predict/gradcam —— 单张识别 + Grad-CAM 热力图
# 前端：未调用（大屏热力图来自 /screen/predict 的 gradcam_base64）
# 入参：file（必填）、model（可选 query）
# 依赖：predictor.predict_with_gradcam（src/predictor.py → src/gradcam.py）
# 返回：预测结果 + gradcam{class_index, heatmap_base64, overlay_base64, format}
# ---------------------------------------------------------------------------
@app.post("/predict/gradcam", tags=["识别"], summary="单张识别 + Grad-CAM 热力图")
async def predict_gradcam(
    file: UploadFile = File(...),
    model: Optional[str] = Query(None),
):
    p = _predictor()
    _validate_upload(file)
    data = await _read_file(file)
    result = p.predict_with_gradcam(data, file.filename or "upload.jpg", model_key=model)
    # cam_raw 是 numpy 激活矩阵，不能直接 JSON 序列化（会导致 500）；只返回 base64 热力图
    gradcam = result.get("gradcam")
    if isinstance(gradcam, dict):
        gradcam.pop("cam_raw", None)
    return ok(result)


# ---------------------------------------------------------------------------
# POST /predict/batch —— 批量图片识别（单次最多 20 张）
# 前端：未调用（大屏当前只有单图入口）
# 入参：files（必填，多文件）、model（可选 query）
# 依赖：predictor.predict_batch（src/predictor.py）
# 返回：{results[], failed[], summary{}}；单张格式错误不中断整批
# ---------------------------------------------------------------------------
@app.post("/predict/batch", tags=["识别"], summary="批量图片识别")
async def predict_batch(
    files: List[UploadFile] = File(..., description="多张图片，最多 20 张"),
    model: Optional[str] = Query(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传 1 张图片")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"单次批量最多 {MAX_FILES} 张图片")

    payload = []
    for f in files:
        try:
            _validate_upload(f)
        except HTTPException:
            # 单个格式错误不阻断整批，记入 failed
            payload.append((f.filename or "unknown", b""))
            continue
        payload.append((f.filename or "unknown", await _read_file(f)))

    p = _predictor()
    res = p.predict_batch(payload, model_key=model)
    for r in res["results"]:
        r["knowledge"] = {"name_cn": get_knowledge(r["class_name_en"])["name_cn"]}
    return ok(res)


# ---------------------------------------------------------------------------
# POST /predict/compare —— 同一张图跑全部已加载模型做对比
# 前端：未调用；用于 Swagger 演示或离线脚本
# 入参：file（必填）
# 依赖：predictor.compare（src/predictor.py）
# 返回：{results[各模型结果], models[模型 key 列表]}
# ---------------------------------------------------------------------------
@app.post("/predict/compare", tags=["识别"], summary="多模型对比识别")
async def predict_compare(file: UploadFile = File(...)):
    p = _predictor()
    _validate_upload(file)
    data = await _read_file(file)
    results = p.compare(data, file.filename or "upload.jpg")
    return ok({"results": results, "models": list(p.models.keys())})


# ---------------------------------------------------------------------------
# POST /predict/base64 —— JSON 传 base64 图片（兼容小程序 / Streamlit）
# 前端：未调用（大屏 /screen/predict 已覆盖该能力）
# 入参：{image_base64, filename, model, gradcam}
# 依赖：gradcam=true → predict_with_gradcam；否则 predict_bytes + knowledge
# 返回：预测结果（gradcam=true 时附带 gradcam 热力图）
# ---------------------------------------------------------------------------
@app.post("/predict/base64", tags=["识别"], summary="base64 图片识别（兼容小程序/Streamlit）")
async def predict_base64(req: Base64Request):
    import base64
    import binascii

    raw = req.image_base64
    if "," in raw and raw.strip().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"base64 解码失败：{e}")

    p = _predictor()
    if req.gradcam:
        result = p.predict_with_gradcam(data, req.filename, model_key=req.model)
    else:
        result = p.predict_bytes(data, req.filename, model_key=req.model)
        result["knowledge"] = get_knowledge(result["class_name_en"])
    return ok(result)


# ---------------------------------------------------------------------------
# POST /cache/clear —— 清空各模型的图片预处理 LRU 缓存
# 前端：未调用；运维手动调用（长时间运行后可释放内存）
# 依赖：predictor.clear_cache（src/predictor.py）
# 返回：{cleared: true}
# ---------------------------------------------------------------------------
@app.post("/cache/clear", tags=["基础"], summary="清空预处理缓存")
async def clear_cache():
    p = _predictor()
    p.clear_cache()
    return ok({"cleared": True})


# ==========================================================================
#  本地直接运行
# ==========================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api:app",
        host=SERVER_CFG.get("host", "0.0.0.0"),
        port=int(SERVER_CFG.get("port", 8000)),
        reload=False,
        workers=1,  # 模型常驻内存，多 worker 会重复占用显存，单 worker + 异步即可
    )
