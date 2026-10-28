"""登录认证模块（用户库 + 密码哈希 + 无状态签名令牌）。

设计取舍
--------
* **不引入 PyJWT / passlib**：项目 requirements 里没有这些包，为了"装上就能跑"，
  令牌用 HMAC-SHA256 自签（base64url(payload) + "." + base64url(sig)），
  密码用标准库 ``hashlib.pbkdf2_hmac``。安全性等价于 HS256 JWT。
* **用户库用 SQLite**：与 ``src/history_store.py`` 同一个 history 目录，
  整个目录已在 .gitignore 中排除，运行时不污染仓库。
* **令牌两种投递方式**：``Authorization: Bearer`` 为主；
  另外兼容 ``?token=``（EventSource / <img> 这类不能带 header 的场景）。
* **退出登录**：令牌是无状态的，服务端用 ``revoked_tokens`` 表记录 jti 实现立即失效。

令牌格式（三段式，肉眼可调试）::

    eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2MTYwMDAwMH0.9f3c...（payload.signature）

接口一览（挂在 /auth 前缀，无需令牌即可访问 login/register）::

    POST /auth/login      {username, password, remember}  -> {token, expires_in, user}
    POST /auth/register   {username, password, display_name}
    GET  /auth/me                                         -> {user}
    POST /auth/logout                                      -> 注销当前令牌
    GET  /auth/config                                     -> 注册开关 / 演示账号提示

环境变量
--------
``CORN_AUTH_SECRET``          签名密钥（不设则自动生成并落到 history/auth_secret.key）
``CORN_AUTH_ADMIN_PASSWORD``  首次初始化时 admin 的密码
``CORN_AUTH_ALLOW_REGISTER``  "0"/"false" 关闭自助注册（默认开启，方便演示）
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("corn.auth")

# ==========================================================================
#  路径与常量
# ==========================================================================
ROOT = Path(__file__).resolve().parents[1]
HISTORY_DIR = ROOT / "history"
DB_PATH = HISTORY_DIR / "auth.db"
SECRET_PATH = HISTORY_DIR / "auth_secret.key"

TOKEN_TTL_HOURS = 12           # 普通登录有效期
TOKEN_TTL_HOURS_REMEMBER = 24 * 7  # 勾选「记住我」有效期
PBKDF2_ITERATIONS = 210_000
MAX_LOGIN_FAILURES = 5         # 同一账号连续失败次数上限
FAILURE_WINDOW_SECONDS = 300   # 锁定时长

USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{2,31}$")
ROLE_LABELS = {
    "admin": "系统管理员",
    "agronomist": "农艺师",
    "operator": "巡田员",
    "viewer": "访客",
}

# 演示账号：首次初始化写入，方便评审直接登录体验
DEFAULT_USERS = [
    {
        "username": "admin",
        "password": os.environ.get("CORN_AUTH_ADMIN_PASSWORD", "corn@2026"),
        "display_name": "系统管理员",
        "role": "admin",
    },
    {
        "username": "agronomist",
        "password": "field@2026",
        "display_name": "张工 · 农艺师",
        "role": "agronomist",
    },
]

router = APIRouter(prefix="/auth", tags=["登录认证"])


# ==========================================================================
#  基础工具
# ==========================================================================
def _now() -> int:
    return int(time.time())


def _iso(ts: Optional[int] = None) -> str:
    return datetime.fromtimestamp(ts or _now()).strftime("%Y-%m-%d %H:%M:%S")


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _connect() -> sqlite3.Connection:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str, int]:
    """返回 (salt_hex, hash_hex, iterations)。"""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex(), PBKDF2_ITERATIONS


def _verify_password(password: str, salt_hex: str, expected_hex: str, iterations: int) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations)
    return hmac.compare_digest(digest.hex(), expected_hex)


def _load_secret() -> bytes:
    env = os.environ.get("CORN_AUTH_SECRET", "").strip()
    if env:
        return env.encode("utf-8")
    if SECRET_PATH.exists():
        try:
            data = SECRET_PATH.read_bytes().strip()
            if len(data) >= 32:
                return data
        except OSError:  # pragma: no cover - 极端权限问题
            pass
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_bytes(48)
    SECRET_PATH.write_bytes(secret)
    logger.info("已生成新的令牌签名密钥：%s", SECRET_PATH)
    return secret


_SECRET: Optional[bytes] = None


def _secret() -> bytes:
    global _SECRET
    if _SECRET is None:
        _SECRET = _load_secret()
    return _SECRET


# ==========================================================================
#  用户库
# ==========================================================================
def init_db() -> None:
    """建表 + 首次写入演示账号（幂等）。"""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name  TEXT NOT NULL DEFAULT '',
                role          TEXT NOT NULL DEFAULT 'operator',
                pwd_salt      TEXT NOT NULL,
                pwd_hash      TEXT NOT NULL,
                iterations    INTEGER NOT NULL DEFAULT 210000,
                created_at    INTEGER NOT NULL,
                last_login_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti TEXT PRIMARY KEY,
                exp INTEGER NOT NULL
            );
            """
        )
        has_user = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"] > 0
        if not has_user:
            for item in DEFAULT_USERS:
                salt, digest, iters = _hash_password(item["password"])
                conn.execute(
                    "INSERT INTO users (username, display_name, role, pwd_salt, pwd_hash, iterations, created_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (item["username"], item["display_name"], item["role"], salt, digest, iters, _now()),
                )
            logger.info("已初始化演示账号：%s", ", ".join(u["username"] for u in DEFAULT_USERS))
        # 顺手清理过期令牌黑名单
        conn.execute("DELETE FROM revoked_tokens WHERE exp < ?", (_now(),))


def _user_public(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "username": row["username"],
        "display_name": row["display_name"] or row["username"],
        "role": row["role"],
        "role_label": ROLE_LABELS.get(row["role"], row["role"]),
        "created_at": _iso(row["created_at"]),
        "last_login_at": _iso(row["last_login_at"]) if row["last_login_at"] else None,
    }


def get_user(username: str) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


# ==========================================================================
#  令牌签发 / 校验
# ==========================================================================
def issue_token(user: sqlite3.Row, ttl_hours: int = TOKEN_TTL_HOURS) -> Tuple[str, int]:
    now = _now()
    exp = now + ttl_hours * 3600
    payload = {
        "sub": user["username"],
        "uid": user["id"],
        "name": user["display_name"] or user["username"],
        "role": user["role"],
        "iat": now,
        "exp": exp,
        "jti": secrets.token_urlsafe(12),
    }
    body = _b64e(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    sig = _b64e(hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}", exp


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """校验签名与有效期，成功返回 payload，失败返回 None。"""
    try:
        body, sig = token.split(".", 1)
        expect = _b64e(hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expect):
            return None
        payload = json.loads(_b64d(body).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict) or int(payload.get("exp", 0)) < _now():
        return None
    return payload


def revoke_token(payload: Dict[str, Any]) -> None:
    jti = payload.get("jti")
    if not jti:
        return
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO revoked_tokens (jti, exp) VALUES (?, ?)",
            (jti, int(payload.get("exp", _now()))),
        )


def _is_revoked(jti: str) -> bool:
    if not jti:
        return False
    with _connect() as conn:
        return conn.execute("SELECT 1 FROM revoked_tokens WHERE jti = ?", (jti,)).fetchone() is not None


# ==========================================================================
#  请求侧：取令牌 / 鉴权中间件
# ==========================================================================
def extract_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    # SSE / <img> 等无法设置 header 的场景
    token = request.query_params.get("token", "").strip()
    if token:
        return token
    return request.cookies.get("corn_token", "").strip()


PUBLIC_PATHS = {"/", "/health", "/favicon.ico", "/docs", "/redoc", "/openapi.json"}


def is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    if path.startswith("/auth/"):
        return True
    # Swagger UI 的静态资源
    return path.startswith("/docs/")


def check_request(request: Request) -> Optional[Tuple[int, Dict[str, Any]]]:
    """业务接口鉴权。返回 None 表示通过，否则返回 (status_code, body)。

    通过的请求会在 ``request.state.user`` 上挂当前用户信息，供路由内使用。
    """
    if is_public(request.url.path) or request.method == "OPTIONS":
        return None

    token = extract_token(request)
    if not token:
        return 401, {"code": 401, "message": "未登录或登录已过期，请先登录", "data": None}

    payload = decode_token(token)
    if payload is None:
        return 401, {"code": 401, "message": "登录凭证无效或已过期，请重新登录", "data": None}
    if _is_revoked(payload.get("jti", "")):
        return 401, {"code": 401, "message": "该登录凭证已注销，请重新登录", "data": None}

    request.state.user = payload
    return None


def current_user(request: Request) -> Optional[Dict[str, Any]]:
    return getattr(request.state, "user", None)


# ==========================================================================
#  登录失败限流（内存级，进程重启即清空）
# ==========================================================================
_FAILURES: Dict[str, list] = {}


def _failure_key(request: Request, username: str) -> str:
    ip = request.client.host if request.client else "-"
    return f"{username.lower()}@{ip}"


def _locked(key: str) -> int:
    """返回剩余锁定秒数，0 表示未锁定。"""
    stamps = [t for t in _FAILURES.get(key, []) if _now() - t < FAILURE_WINDOW_SECONDS]
    _FAILURES[key] = stamps
    if len(stamps) >= MAX_LOGIN_FAILURES:
        return FAILURE_WINDOW_SECONDS - (_now() - stamps[0])
    return 0


def _record_failure(key: str) -> None:
    _FAILURES.setdefault(key, []).append(_now())


def _clear_failures(key: str) -> None:
    _FAILURES.pop(key, None)


# ==========================================================================
#  请求模型（延迟导入 pydantic，保持模块可独立测试）
# ==========================================================================
from pydantic import BaseModel, Field  # noqa: E402


class LoginBody(BaseModel):
    username: str = Field(..., description="账号")
    password: str = Field(..., description="密码")
    remember: bool = Field(False, description="勾选后令牌有效期延长到 7 天")


class RegisterBody(BaseModel):
    username: str = Field(..., description="账号：字母开头，3-32 位字母数字下划线")
    password: str = Field(..., description="密码：至少 8 位，包含字母和数字")
    display_name: str = Field("", description="显示名，可留空")
    role: str = Field("operator", description="角色：operator / agronomist / viewer")


def _err(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": status, "message": message, "data": None})


def _allow_register() -> bool:
    return os.environ.get("CORN_AUTH_ALLOW_REGISTER", "1").lower() not in ("0", "false", "no")


def _password_problem(password: str) -> Optional[str]:
    if len(password) < 8:
        return "密码至少 8 位"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "密码需同时包含字母和数字"
    return None


# ==========================================================================
#  路由
# ==========================================================================
@router.get("/config", summary="登录页配置（注册开关、演示账号）")
async def auth_config():
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "allow_register": _allow_register(),
            "token_ttl_hours": TOKEN_TTL_HOURS,
            "remember_ttl_hours": TOKEN_TTL_HOURS_REMEMBER,
            "demo_accounts": [
                {"username": u["username"], "password": u["password"], "role_label": ROLE_LABELS.get(u["role"], u["role"])}
                for u in DEFAULT_USERS
            ],
        },
    }


@router.post("/login", summary="账号密码登录")
async def login(body: LoginBody, request: Request):
    username = body.username.strip()
    key = _failure_key(request, username)

    locked = _locked(key)
    if locked > 0:
        return _err(429, f"登录失败次数过多，请 {locked // 60 + 1} 分钟后再试")

    row = get_user(username)
    # 账号不存在与密码错误返回同一提示，避免枚举账号
    if row is None or not _verify_password(body.password, row["pwd_salt"], row["pwd_hash"], row["iterations"]):
        _record_failure(key)
        left = MAX_LOGIN_FAILURES - len(_FAILURES.get(key, []))
        suffix = f"，还可尝试 {left} 次" if left > 0 else ""
        logger.warning("登录失败 username=%s ip=%s", username, request.client.host if request.client else "-")
        return _err(401, f"账号或密码不正确{suffix}")

    _clear_failures(key)
    ttl = TOKEN_TTL_HOURS_REMEMBER if body.remember else TOKEN_TTL_HOURS
    token, exp = issue_token(row, ttl)

    with _connect() as conn:
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_now(), row["id"]))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()

    logger.info("登录成功 username=%s role=%s", row["username"], row["role"])
    response = JSONResponse(
        content={
            "code": 0,
            "message": "ok",
            "data": {
                "token": token,
                "token_type": "Bearer",
                "expires_in": exp - _now(),
                "expires_at": exp,
                "user": _user_public(row),
            },
        }
    )
    # 同时写 cookie：刷新页面 / 直连后端时也能自动带上
    response.set_cookie(
        "corn_token",
        token,
        max_age=exp - _now(),
        httponly=True,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/register", summary="注册账号")
async def register(body: RegisterBody):
    if not _allow_register():
        return _err(403, "当前已关闭自助注册，请联系管理员开通账号")

    username = body.username.strip()
    if not USERNAME_RE.match(username):
        return _err(400, "账号需以字母开头，长度 3-32 位，仅支持字母、数字、下划线、点、短横线")
    problem = _password_problem(body.password)
    if problem:
        return _err(400, problem)

    role = body.role if body.role in ("operator", "agronomist", "viewer") else "operator"
    salt, digest, iters = _hash_password(body.password)
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, display_name, role, pwd_salt, pwd_hash, iterations, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, body.display_name.strip() or username, role, salt, digest, iters, _now()),
            )
    except sqlite3.IntegrityError:
        return _err(409, "该账号已被注册，请换一个")

    row = get_user(username)
    logger.info("注册成功 username=%s role=%s", username, role)
    return {
        "code": 0,
        "message": "ok",
        "data": {"user": _user_public(row)},
    }


@router.get("/me", summary="当前登录用户")
async def me(request: Request):
    token = extract_token(request)
    payload = decode_token(token) if token else None
    if payload is None:
        return _err(401, "登录状态已失效，请重新登录")
    if _is_revoked(payload.get("jti", "")):
        return _err(401, "该登录凭证已注销，请重新登录")
    row = get_user(payload.get("sub", ""))
    if row is None:
        return _err(401, "账号不存在或已被停用")
    return {"code": 0, "message": "ok", "data": {"user": _user_public(row)}}


@router.post("/logout", summary="退出登录")
async def logout(request: Request):
    token = extract_token(request)
    payload = decode_token(token) if token else None
    if payload:
        revoke_token(payload)
    response = JSONResponse(content={"code": 0, "message": "已退出登录", "data": None})
    response.delete_cookie("corn_token", path="/")
    return response


# 启动即建表：模块被 api.py 导入时执行一次，避免首个登录请求才建库
try:
    init_db()
except Exception:  # pragma: no cover - 数据库不可写时不应拖垮整个服务
    logger.exception("用户库初始化失败，登录功能将不可用")
