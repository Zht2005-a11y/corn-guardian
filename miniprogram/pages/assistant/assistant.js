/**
 * 植保 AI 助手 —— 单页对话设计
 * 同一页内完成：欢迎态（欢迎气泡 + 快捷问题 + 最近会话）⇄ 对话态（流式问答），
 * 不再跳转子页面。流式实现：wx.request enableChunked 逐块接收，
 * 解析 data: {...} 事件，事件类型与 Web 端 Layout.vue 保持一致
 * （delta/tool_call/tool_result/retry/resume/truncated/stop_hook/done）。
 */
const api = require('../../utils/api');
const icons = require('../../utils/icons');

const app = getApp();

/** 跨 chunk 安全的 UTF-8 解码器（逐字节缓冲，处理多字节截断） */
function makeUtf8Decoder() {
  let tail = [];
  return {
    decode(bytes) {
      const all = tail.concat(Array.prototype.slice.call(bytes));
      let out = '';
      let i = 0;
      while (i < all.length) {
        const b = all[i];
        let need = 0;
        if (b < 0x80) need = 0;
        else if ((b & 0xe0) === 0xc0) need = 1;
        else if ((b & 0xf0) === 0xe0) need = 2;
        else if ((b & 0xf8) === 0xf0) need = 3;
        else { i += 1; continue; }
        if (i + need >= all.length) break;
        let cp = b & (need === 0 ? 0x7f : need === 1 ? 0x1f : need === 2 ? 0x0f : 0x07);
        let ok = true;
        for (let k = 1; k <= need; k++) {
          const cb = all[i + k];
          if ((cb & 0xc0) !== 0x80) { ok = false; break; }
          cp = (cp << 6) | (cb & 0x3f);
        }
        if (!ok) { i += 1; continue; }
        i += need + 1;
        out += String.fromCodePoint(cp);
      }
      tail = all.slice(i);
      return out;
    }
  };
}

let msgSeq = 1;
function nextId() { return msgSeq++; }

/**
 * 流式输出两层架构（与 Web 端 Layout.vue 完全同构）：
 * ① Typewriter 匀速缓冲层：content 由 SSE 实时填充，shown 由 28ms 定时器渐进追平
 *    （Layout.vue「Typewriter 匀速缓冲——ChatGPT 手感的第一层」同款）；
 * ② Streamdown 渐显层：每次上屏的新文本按 sep:'word' 切词元，blurIn 450ms +
 *    词间阶梯延迟（animated:{animation:'blurIn',duration:450,easing:cubic-bezier(.25,.6,.3,1)}）。
 * 词元动画挂在 <view>（inline-block）上——<text> 子节点的 CSS 动画开发者工具不执行；
 * 另有保险丝：老词元强制摘除动画类，任何渲染器下文字最终必然可见。
 */
const REVEAL = { interval: 28, divisor: 9 };
const SD_ANIM = { duration: 450, stagger: 40, maxSpread: 500, keepTokens: 160 };

/**
 * Streamdown 风格分词（对齐桌面端 sep:'word'）：
 * 西文按空白切词，CJK 无词边界、按 2 字一组保证中文也有渐显粒度，
 * 空白并入前一个词元。返回 [string] 词元数组。
 */
function splitStreamTokens(delta) {
  const out = [];
  let buf = '';
  let cjk = '';
  const flushASCII = () => { if (buf) { out.push(buf); buf = ''; } };
  const flushCJK = () => { if (cjk) { out.push(cjk); cjk = ''; } };
  const isCJK = (ch) => /[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef\u3000-\u303f]/.test(ch);
  for (const ch of delta) {
    if (/\s/.test(ch)) {
      flushCJK();
      flushASCII();
      if (out.length) out[out.length - 1] += ch;
      else out.push(ch);
      continue;
    }
    if (isCJK(ch)) {
      flushASCII();
      cjk += ch;
      if (cjk.length >= 2) { out.push(cjk); cjk = ''; }
    } else {
      flushCJK();
      buf += ch;
    }
  }
  flushCJK();
  flushASCII();
  return out;
}

Page({
  data: {
    online: false,
    messages: [],
    draft: '',
    streaming: false,
    scrollTo: 'scroll-pad',
    sessions: [],
    showSessions: false,
    quickQuestions: ['病害防治建议', '农资价格查询', '最新农业政策', '种植技术指导'],
    icons: {
      avatar: icons.make('robot', '#FFFFFF', 1.7),
      send: icons.make('send', '#FFFFFF', 4),
      arrow: icons.make('arrow', '#C4CDD0', 2)
    }
  },

  onLoad() {
    this.history = [];       // [{role, content}] 最近上下文
    this.sessionId = app.globalData.chatSessionId || '';
    this.task = null;
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
    this.checkOnline();
    this.fetchSessions();
  },

  onHide() {
    // TabBar 页不会 unload，切走时保存会话 id 供下次进入恢复
    app.globalData.chatSessionId = this.sessionId;
  },

  onUnload() {
    if (this.task) {
      try { this.task.abort(); } catch (e) { /* noop */ }
      this.task = null;
    }
    if (this.revealTimer) {
      clearTimeout(this.revealTimer);
      this.revealTimer = null;
    }
    app.globalData.chatSessionId = this.sessionId;
  },

  /* ---------------- 在线状态与历史会话 ---------------- */

  checkOnline() {
    this.setData({ online: false });
    api.sessionList(1)
      .then(() => this.setData({ online: true }))
      .catch(() => this.setData({ online: false }));
  },

  fetchSessions() {
    api.sessionList(8)
      .then((d) => {
        const sessions = (d.sessions || []).slice(0, 8);
        this.setData({ sessions });
      })
      .catch(() => this.setData({ sessions: [] }));
  },

  toggleSessions() {
    this.setData({ showSessions: !this.data.showSessions });
  },

  closeSessions() {
    this.setData({ showSessions: false });
  },

  openSession(e) {
    const sid = e.currentTarget.dataset.sid;
    this.setData({ showSessions: false });
    this.restoreSession(sid);
  },

  /** 开始新对话（流式进行中需先停止） */
  newChat() {
    if (this.data.streaming) {
      wx.showModal({
        title: '正在生成回答',
        content: '要先停止当前回答并开始新对话吗？',
        confirmText: '停止并新建',
        success: (res) => {
          if (res.confirm) {
            this.stopGen();
            this.resetConversation();
          }
        }
      });
      return;
    }
    this.resetConversation();
  },

  resetConversation() {
    this.sessionId = '';
    this.history = [];
    app.globalData.chatSessionId = '';
    this.setData({ messages: [], showSessions: false, scrollTo: 'scroll-pad' });
  },

  /* ---------------- 会话恢复（后端 JSONL transcript） ---------------- */

  restoreSession(sid) {
    if (this.data.streaming) {
      wx.showToast({ title: '请先停止当前回答', icon: 'none' });
      return;
    }
    this.sessionId = sid;
    app.globalData.chatSessionId = sid;
    wx.showLoading({ title: '恢复会话…' });
    api.sessionDetail(sid)
      .then((d) => {
        wx.hideLoading();
        const messages = (d.messages || []).map((m) => ({
          id: nextId(),
          role: m.role === 'user' ? 'user' : 'ai',
          // 后端会话详情字段是 text（兼容 content），直读 content 会得到空消息
          content: m.text || m.content || '',
          status: '',
          error: '',
          cursor: false,
          queries: m.searchQuery ? [m.searchQuery] : [],
          shown: (m.text || m.content || '').length,
          prefix: '',
          tokens: [],
          tokLen: 0,
          tokN: 0
        }));
        this.setData({ messages });
        this.rebuildHistory(messages);
        this.scrollToBottom();
      })
      .catch((err) => {
        wx.hideLoading();
        wx.showToast({ title: '会话恢复失败：' + err.message, icon: 'none' });
      });
  },

  rebuildHistory(messages) {
    const h = [];
    messages.filter((m) => !m.error).forEach((m) => {
      h.push({ role: m.role === 'user' ? 'user' : 'assistant', content: m.content });
    });
    this.history = h.slice(-6);
  },

  /* ---------------- 消息流 ---------------- */

  pushUser(content) {
    const messages = this.data.messages.concat([{ id: nextId(), role: 'user', content, status: '', error: '', cursor: false, queries: [] }]);
    this.setData({ messages });
    this.scrollToBottom();
  },

  pushAiMessage(content, error) {
    const text = content || '';
    const messages = this.data.messages.concat([{ id: nextId(), role: 'ai', content: text, status: '', error: error || '', cursor: false, queries: [], shown: text.length, prefix: '', tokens: [], tokLen: 0, tokN: 0 }]);
    this.setData({ messages });
    this.scrollToBottom();
    return messages[messages.length - 1].id;
  },

  updateAi(id, patch) {
    const messages = this.data.messages.map((m) => (m.id === id ? { ...m, ...patch } : m));
    this.setData({ messages });
  },

  scrollToBottom() {
    wx.nextTick(() => this.setData({ scrollTo: 'scroll-pad' }));
  },

  onInput(e) {
    this.setData({ draft: e.detail.value });
  },

  /** 空操作（浮层内容区阻止冒泡） */
  noop() {},

  send() {
    if (this.data.streaming) return;
    const msg = (this.data.draft || '').trim();
    if (!msg) return;
    this.setData({ draft: '' });
    this.pushUser(msg);
    this.startStream(msg);
  },

  /** 快捷问题：直接以该问题发起提问 */
  askQuick(e) {
    if (this.data.streaming) return;
    const q = e.currentTarget.dataset.q;
    this.pushUser(q);
    this.startStream(q);
  },

  retryLast() {
    if (this.data.streaming) return;
    // 找到最近一条用户消息重发
    const users = this.data.messages.filter((m) => m.role === 'user');
    if (!users.length) return;
    const last = users[users.length - 1];
    // 移除最后一条 AI 错误消息
    const messages = this.data.messages.slice(0, -1);
    this.setData({ messages });
    this.startStream(last.content);
  },

  stopGen() {
    if (this.task) {
      try { this.task.abort(); } catch (e) { /* noop */ }
    }
  },

  /* ---------------- 流式吐字：① 匀速打字机 ② 逐词 blurIn 渐显 ---------------- */

  /** 启动/续跑打字机：把 shown 渐进追平到 content；每步上屏的新文本交给 revealTokens 做渐显 */
  ensureReveal(aiId) {
    if (this.revealTimer) return;
    const tick = () => {
      const m = this.data.messages.find((x) => x.id === aiId);
      if (!m) { this.revealTimer = null; return; }
      const target = m.content.length;
      const shown = m.shown || 0;
      if (shown < target) {
        // 剩余越多步进越大 → 视觉上近似匀速吐字，突发大段也能平滑追上
        const step = Math.max(1, Math.ceil((target - shown) / REVEAL.divisor));
        const next = Math.min(target, shown + step);
        this.revealTokens(aiId, m, next);
        this.revealTimer = setTimeout(tick, REVEAL.interval);
        return;
      }
      if (this.revealDone) {
        // 追平且流结束：让尾批词元的渐显播完，再熄灭光标、清词元切回纯文本（可选中复制）
        this.revealTimer = null;
        setTimeout(() => {
          this.updateAi(aiId, { cursor: false, prefix: '', tokens: [], tokLen: 0, tokN: 0 });
        }, SD_ANIM.duration + SD_ANIM.maxSpread + 200);
        return;
      }
      // 已追平但流未结束：停下等下一段 delta 触发 ensureReveal 再继续
      this.revealTimer = null;
    };
    this.revealTimer = setTimeout(tick, REVEAL.interval);
  },

  /** 把已上屏但未分词的文本切成动画词元（blurIn + 阶梯延迟，桌面端 Streamdown 同款） */
  revealTokens(aiId, m, next) {
    const full = m.content.slice(0, next);
    const delta = full.slice(m.tokLen || 0);
    if (!delta) { this.updateAi(aiId, { shown: next }); return; }
    const words = splitStreamTokens(delta);
    const n = words.length;
    const tokens = (m.tokens || []).slice();
    const tokN = m.tokN || 0;
    // 阶梯延迟：底速 40ms/词（桌面端同值），单批过多时压缩总铺开时长（≤500ms）防止越追越慢
    const stagger = n > 1 ? Math.min(SD_ANIM.stagger, Math.round(SD_ANIM.maxSpread / (n - 1))) : 0;
    for (let i = 0; i < n; i++) tokens.push({ k: tokN + i, w: words[i], a: 1, d: i * stagger });
    let prefix = m.prefix || '';
    // 动画词元只保留滑动窗口，更早的文本沉淀为 prefix 纯文本，控制 setData 体积
    if (tokens.length > SD_ANIM.keepTokens) {
      const drop = tokens.slice(0, tokens.length - SD_ANIM.keepTokens);
      prefix += drop.map((t) => t.w).join('');
      tokens.splice(0, tokens.length - SD_ANIM.keepTokens);
    }
    // 保险丝：约 80 个词元（>1.1s）之前的批次强制摘除动画类——
    // 若渲染器不执行该动画，文字也只是晚 ~1s 变可见，绝不会永远隐藏
    const newTokN = tokN + n;
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].a && tokens[i].k < newTokN - 80) tokens[i] = { k: tokens[i].k, w: tokens[i].w, a: 0, d: 0 };
    }
    this.updateAi(aiId, { shown: next, prefix, tokens, tokLen: full.length, tokN: newTokN });
  },

  buildContext() {
    const r = app.globalData.lastResult;
    if (!r || r.rejected) return null;
    return {
      diseaseName: r.class_name_cn || r.diseaseName,
      severity: r.severity,
      damageRate: r.damageRate,
      prescription: r.prescription
    };
  },

  /* ---------------- SSE 流式请求 ---------------- */

  startStream(message) {
    if (!this.sessionId) {
      this.sessionId = 'mp_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      app.globalData.chatSessionId = this.sessionId;
    }

    const aiId = this.pushAiMessage('');
    this.revealDone = false; // 流结束后由 finish 置 true，打字机追平时据此熄灭光标
    this.updateAi(aiId, { status: '正在思考…', cursor: true });
    this.setData({ streaming: true });

    // SSE 块缓冲
    let sseBuf = '';
    const decoder = makeUtf8Decoder();
    let flushTimer = null;
    const pending = { content: '', status: '', queries: null };

    const flush = () => {
      flushTimer = null;
      const patch = {};
      let needReveal = false;
      if (pending.content) {
        const cur = this.data.messages.find((m) => m.id === aiId);
        const full = (cur ? cur.content : '') + pending.content;
        patch.content = full;
        pending.content = '';
        needReveal = true;
      }
      if (pending.status) { patch.status = pending.status; pending.status = ''; }
      if (pending.queries) { patch.queries = pending.queries; pending.queries = null; }
      if (Object.keys(patch).length) {
        this.updateAi(aiId, patch);
        this.scrollToBottom();
      }
      if (needReveal) this.ensureReveal(aiId);
    };
    const scheduleFlush = () => {
      if (!flushTimer) flushTimer = setTimeout(flush, 90);
    };

    const noteQuery = (id, q) => {
      const cur = this.data.messages.find((m) => m.id === id);
      const queries = cur ? cur.queries.slice() : [];
      if (q && queries.indexOf(q) < 0) queries.push(q);
      this.updateAi(id, { queries });
    };
    this.noteQuery = noteQuery;

    const handleEvent = (ev) => {
      switch (ev.type) {
        case 'delta':
          pending.content += ev.content || '';
          scheduleFlush();
          break;
        case 'tool_call':
          pending.status = '正在联网检索：' + (ev.query || '');
          scheduleFlush();
          this.noteQuery(aiId, ev.query);
          break;
        case 'tool_result':
          pending.status = ev.message || '检索完成，正在组织回答…';
          scheduleFlush();
          break;
        case 'retry':
          pending.status = '网络抖动，正在重试(' + (ev.attempt || 1) + '/' + (ev.max || 2) + ')';
          scheduleFlush();
          break;
        case 'resume':
          pending.status = ev.action === 'restored' ? '已恢复上下文，继续回答…' : '';
          scheduleFlush();
          break;
        case 'truncated':
          pending.status = ev.action === 'resume' ? '回答较长，正在继续生成…' : '';
          scheduleFlush();
          break;
        case 'stop_hook':
          if (ev.action === 'block') {
            pending.status = '质量门禁打回重答中…';
          } else {
            pending.status = '';
          }
          scheduleFlush();
          break;
        case 'done':
          break;
        default:
          break;
      }
    };

    const finish = (errMsg) => {
      if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
      flush(); // 兜底：把 90ms 缓冲窗口里未上屏的尾部内容冲出来，避免丢字
      const cur = this.data.messages.find((m) => m.id === aiId) || {};
      const content = cur.content || '';
      // 记入上下文历史
      const users = this.data.messages.filter((m) => m.role === 'user');
      const lastUser = users.length ? users[users.length - 1].content : message;
      this.history.push({ role: 'user', content: lastUser });
      if (content) this.history.push({ role: 'assistant', content });
      this.history = this.history.slice(-6);

      // 统一友好报错：连接失败/重试耗尽/未收到回答 → 「AI助手暂时不可用，请稍后重试」
      const AI_UNAVAILABLE = 'AI助手暂时不可用，请稍后重试';
      let error = '';
      if (errMsg) {
        if (errMsg.indexOf('已停止') >= 0) {
          error = content ? '' : '已停止生成';
        } else {
          error = AI_UNAVAILABLE;
        }
      } else if (!content) {
        error = AI_UNAVAILABLE;
      }
      this.updateAi(aiId, {
        status: '',
        error: error,
        queries: this.queriesOf(aiId)
      });
      this.setData({ streaming: false });
      this.task = null;
      this.scrollToBottom();
      // 打字机继续把尾部缓冲追平，追平后自动熄灭光标（不丢任何已接收内容）
      this.revealDone = true;
      this.ensureReveal(aiId);
      // 会话标题已生成，刷新历史列表
      this.fetchSessions();
    };

    this.queriesOf = (id) => {
      const cur = this.data.messages.find((m) => m.id === id);
      return cur ? cur.queries : [];
    };

    this.task = wx.request({
      url: api.buildUrl ? api.buildUrl('/screen/chat/stream') : (api.BASE_URL + '/screen/chat/stream'),
      method: 'POST',
      data: {
        message: message,
        context: this.buildContext(),
        history: this.history.length ? this.history : null,
        session_id: this.sessionId
      },
      timeout: 180000,
      enableChunked: true,
      responseType: 'arraybuffer',
      header: api.authHeader
        ? Object.assign({ 'Content-Type': 'application/json' }, api.authHeader())
        : { 'Content-Type': 'application/json' },
      success: () => finish(''),
      fail: (err) => {
        if (err && err.errMsg && err.errMsg.indexOf('abort') >= 0) {
          finish('已停止生成');
        } else {
          if (api.notifyDebugGuidanceIfNeeded) api.notifyDebugGuidanceIfNeeded();
          const msg = (err && err.errMsg) || '';
          let hint = '';
          if (msg.indexOf('url not in domain list') >= 0 || msg.indexOf('CLEARTEXT') >= 0) {
            hint = '（体验版请在右上角菜单开启「开发调试」）';
          }
          finish('连接失败：' + msg + hint);
        }
      }
    });

    this.task.onChunkReceived((res) => {
      try {
        const bytes = new Uint8Array(res.data);
        const text = decoder.decode(bytes);
        sseBuf += text;
        let idx;
        while ((idx = sseBuf.indexOf('\n\n')) >= 0) {
          const block = sseBuf.slice(0, idx);
          sseBuf = sseBuf.slice(idx + 2);
          const lines = block.split('\n');
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.indexOf('data:') !== 0) continue;
            const payload = line.slice(5).trim();
            if (!payload) continue;
            try {
              handleEvent(JSON.parse(payload));
            } catch (e) {
              // 忽略无法解析的行
            }
          }
        }
      } catch (e) {
        // ignore decode errors
      }
    });
  }
});
