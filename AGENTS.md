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
│   ├── app/bigscreen_api.py           # 大屏 API（/predict /chat/stream /telemetry）
│   ├── src/llm_client.py              # LLM 客户端：流式问答 + 工具循环 + Stop Hook
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

- 工具循环上限 `MAX_TOOL_ROUNDS=6`；Stop Hook 拦截上限 `MAX_STOP_HOOK_BLOCKS=2`（见 `src/llm_client.py` 顶部注释）；
- Stop Hook 语义对齐 Claude Code hooks：`_decide_stop` 归一化返回值，block 时以 `[stop_hook 反馈]` 注入重答；
- SSE 事件类型：`delta` / `tool_call` / `tool_result` / `stop_hook` / `done`，前端处理在 `Layout.vue` 的 `sendMessage()`；
- 前端聊天的联网检索提示文案与 `web_search.py` 实际实现（百度/搜狗抓取）需保持一致，不要写"知网"等不实来源。
