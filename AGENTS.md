# AGENTS.md — AI 编码代理工作规范

本文件供 AI 编码代理（Claude Code / Codex / Cursor / Jules 等）在本仓库工作时阅读。

---

## ⚠️ 第一铁律：前端设计必须遵循 Tanee Smart Farming UI Kit

**任何涉及前端界面、样式、配色、组件视觉的修改，都必须遵循 Tanee Smart Farming UI Kit 的设计语言。** 本项目前端（`frontend/`）即基于该套件构建，擅自引入外来风格会导致界面割裂。

设计资产位于 **`design/Tanee-Smart-Farming-UI-Kit/`**：

| 资源 | 路径 | 用途 |
|---|---|---|
| 设计令牌（权威来源） | `design/Tanee-Smart-Farming-UI-Kit/tokens/design-tokens.json` | 颜色/字体/圆角/阴影/间距的唯一权威依据 |
| 页面级视觉参考 | `design/Tanee-Smart-Farming-UI-Kit/png/` | 每个界面的完整视觉基准 |
| 矢量图标 | `design/Tanee-Smart-Farming-UI-Kit/svg/` | 直接取用的图标素材 |
| 结构化设计数据 | `design/Tanee-Smart-Farming-UI-Kit/json/` | 节点树（位置/尺寸/样式），用于精确还原 |
| 本地预览画廊 | `design/Tanee-Smart-Farming-UI-Kit/preview.html` | 浏览器打开快速浏览全部页面 |

### 核心设计令牌（速查，详细数据以 tokens JSON 为准）

**颜色**
- 主文字：`#333333`；深色标题/侧边栏：`#181B25`、`#222530`
- 次要文字：`#A4A4A4`、`#525866`、`#8D8D8D`
- 背景/卡片：`#FFFFFF`（卡片）、`#F4F4F4`（画布/分区）、`#ECECEC`（未选中态）、`#DCDCDC`（分割/边框）
- 品牌绿（渐变主色）：`#35C56E → #2E9055`（Linear，侧边栏 Logo/主按钮，实例最多）
- 品牌黄（强调/警示点缀）：`#F9AD19`
- 成功 `#34A853` / 警告 `#FBBC05` / 错误 `#EB4335` / 链接蓝 `#4285F4`

**字体**
- 主字体 Satoshi（Medium 81 处 / Regular 41 处 / Bold 20 处），辅助 Inter
- 字号阶梯：12 / 14（正文主流）/ 16 / 24 / 32 / 40；行高主流 160%、140%
- 字间距主流 `-2%`

**圆角**：`8px` 为绝对主流（61 处），胶囊/圆形元素用 `99999px`；小元素 `4px`，卡片可 `12px`

**间距**：gap 主流 4 / 8 / 12 / 16px；容器 padding 主流 12 / 16px

**效果**：玻璃拟态用 `backdrop-blur 32px`；卡片阴影 `drop-shadow 8px blur, 0/2px offset`

### 修改前端时的硬性要求

1. **新增颜色前先查 tokens**——UI Kit 已覆盖的颜色不得自造近似值（例如不要发明新的绿色，用 `#35C56E→#2E9055` 渐变或 `#17B26A`）；
2. **图标优先从 `svg/` 目录取**，不要引入新的图标库或混用风格；
3. **改动前先看对应页面的 `png/` 视觉基准**，改完与基准对照；
4. 深色/护眼主题（`theme-dark` / `theme-green`，见 `Layout.vue` 的 `themeOptions`）是本项目的扩展主题，新增样式须保证三主题下均可读；
5. 大屏（bigScreen）以科技感绿黑配色为主，登录/注册等辅助页严格复刻 `png/` 中的 Tanee 原设计。

---

## 项目概览

玉米叶部病害多尺度感知与飞防决策大屏系统：
ResNet50-CBAM 病害识别 + Grad-CAM 热力图 + Agnes-3.0-Flash 流式问答（SSE + web_search 工具调用 + Stop Hook 回合结束质量门禁）。

## 快速启动

```bash
# 一键启动（后端 8010 + 前端 5173）
start_all.bat

# 或分别启动
run_backend.bat    # FastAPI: http://127.0.0.1:8010/docs
run_frontend.bat   # Vite:    http://localhost:5173
```

## 目录结构

```
├── frontend/                          # Vue3 + ECharts 大屏前端
│   └── src/views/bigScreen/Layout.vue # 主屏（诊断/问答/灵动岛/主题切换都在这）
├── model/corn_disease_system_20261021/
│   ├── app/bigscreen_api.py           # 大屏 API（/predict /chat/stream /sessions /telemetry）
│   ├── src/llm_client.py              # LLM 客户端：流式问答 + 工具循环 + Stop Hook + 会话基底解析
│   ├── src/session_store.py           # 会话找回存储层（JSONL 落盘，移植 Claude Code --resume 机制）
│   ├── src/web_search.py              # web_search 工具实现
│   ├── configs/config.example.yaml    # 配置模板（真实 config.yaml 不入库）
│   └── docs/                          # Stop Hook 注释讲解 / Claude Code 差距分析
├── design/Tanee-Smart-Farming-UI-Kit/ # ★ 前端设计权威参考（见上方第一铁律）
└── dataset/                           # 数据集（不入库）
```

## 环境与密钥

- LLM 密钥从环境变量 `AGNES_API_KEY` 读取，或写在本地 `configs/config.yaml`（该文件已被 .gitignore 排除）；
- **任何情况下不得把 API Key、config.yaml、数据集、模型权重提交进仓库**。

## 提交约束

- `.gitignore` 已排除：`dataset/`、`*.pth`、`configs/config.yaml`、`node_modules/`、`dist/`、`*.fig`、`design/**/raw/`；
- 前端改动请保持与 `frontend/.git` 无关（它已作为普通文件并入本仓库）；
- 提交信息用中文，格式：`feat|fix|docs: 摘要`。

## 关键架构知识（改问答逻辑前必读）

- 三份额度彼此独立，**不要合并成一个计数器**：`MAX_TOOL_ROUNDS=6`（工具轮次，决定是否下发 tools）、`MAX_RESUME_ROUNDS=3`（截断续写）、`MAX_STOP_HOOK_BLOCKS=2`（打回重答），另有 `MAX_TOTAL_ROUNDS=12` 总闸（Claude Code maxTurns 语义）。历史上四者共用一个 `round_idx`，导致"截断 3 次 + 打回 2 次"就吃掉 6 次工具额度中的 5 次；
- 上游请求带指数退避重试（`MAX_LLM_RETRIES=2`，`RETRYABLE_STATUS` 含 429/5xx），**仅在尚未向用户吐出内容时重试**——已流出文字再重试会重复输出；重试期间向前端推 `retry` 事件；
- 工具结果按 `MAX_TOOL_RESULT_CHARS=8000` 截断（`_truncate_tool_result`），防止检索结果撑爆上下文；
- Stop Hook 语义对齐 Claude Code hooks：`_decide_stop` 归一化返回值，block 时以 `[stop_hook 反馈]` 注入重答；
- SSE 事件类型：`delta` / `tool_call` / `tool_result` / `retry` / `resume` / `stop_hook` / `truncated` / `done`，前端处理在 `Layout.vue` 的 `sendMessage()`；
- **会话快照（打断后可继续）**：`api_messages` 是生成器局部变量，用户点停止即销毁。`llm_client.py` 按 `session_id` 缓存完整 messages（含 tool 消息与半截回答），TTL 300s、上限 50 条、命中即续期。快照在生成器 `finally` 中保存，`aclose()` 触发的 GeneratorExit 同样会走 `finally`；
- **会话找回（JSONL 落盘，复用 Claude Code --resume 机制）**：每段对话 append-only 写入 `<system_root>/sessions/<sid>.jsonl`（存储层 `src/session_store.py`：每行带 uuid/parentUuid/timestamp/message，`[stop_hook 反馈]`/截断续写等注入消息标 `isMeta`；system 消息不落盘、每轮重建）。恢复时基底上下文解析优先级：**内存快照 → 磁盘 transcript → 前端 history**——盘上有该会话时任何追问自动带全上下文（含历史检索结果），不再要求「继续」措辞（`wants_continue()` 现仅决定是否推 `resume` 提示事件，事件带 `source` 字段区分 disk/cache）；恢复基底截断到 `MAX_RESTORED_MESSAGES=40` 条且边界对齐普通用户消息，防止拆散 tool_calls 与 tool 的配对。列表用 stat mtime 排序 + 头尾 64KB 轻读（不做全量解析；标题优先级 lastPrompt > firstPrompt），API 为 `GET /screen/sessions(/{sid})` 与 `DELETE /screen/sessions/{sid}`（删除时同步清内存快照）；前端灵动岛头部时钟图标打开找回列表（两步删除防误触），恢复即切换 session_id 继续对话。`sessions/` 目录已 gitignore，勿把会话数据提交入库；
- **工具结果必须先落库再 yield**：检索完成后立即 `api_messages.append({"role": "tool", ...})`，之后才推 `tool_result` 事件。否则用户恰好在通知那一刻打断，快照里就没有检索结果，「继续」时只能重查。
- 回答被 `max_tokens` 截断时会自动注入续写指令（`MAX_RESUME_ROUNDS=3` 次，对齐 Claude Code 的截断恢复），前端收到 `truncated` 事件显示"正在继续生成"；
- 前端聊天的联网检索提示文案必须与 `web_search.py` 实际实现一致（当前为 360/搜狗/百度国内直连），不要写"知网"等不实来源。

### 工具调用铁律（踩过坑，勿重犯）
- **绝不按关键词门控 `tools` 数组**：工具列表必须每轮声明（对齐 Claude Code `query.ts:674`），是否调用由模型决定。曾用 `need_tools = any(k in message ...)` 决定是否下发工具，导致用户说"你先去查呀"时模型拿不到工具，只能把调用写成正文伪代码，出现"嘴上说检索、实际没检索"。
- **用户明确要求检索时强制调用**：`wants_search()` 命中即首轮下发 `tool_choice={"type":"function","function":{"name":"web_search"}}`（等价 Claude Code `tool_choice:{type:'tool'}`）；网关不支持时自动降级为 `auto` 重试一次。
- **伪工具调用必须拦截**：`PseudoToolCallGuard` 负责摘掉正文里的 `<web_search>…</web_search>` / `<tool_call>…</tool_call>` 等文本形态调用，抽出检索词转为**真实检索**再继续。新增工具时需同步扩充其 `OPENERS` / `CLOSERS`。
- **禁止旁白**：提示词里明确禁止"好的，收到""我将为您检索"这类预告（对齐 Claude Code `prompts.ts:884` "Do not narrate what you're about to do — just do it"）。
- **不要写"严禁调用工具"**：工具描述必须是"何时用/何时不用"的平衡写法；单方面压制会导致该查的时候也不查。
