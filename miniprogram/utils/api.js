/**
 * 后端 API 封装
 * 后端：model/corn_disease_system_20261021（FastAPI，默认 127.0.0.1:8010）
 * 所有接口真实对接，后端未启动时抛出带提示的错误。
 */
const { BASE_URL } = require('./config');

let hasAlertedDebug = false;

function notifyDebugGuidanceIfNeeded() {
  if (hasAlertedDebug) return;
  try {
    const accountInfo = wx.getAccountInfoSync && wx.getAccountInfoSync();
    const envVersion = accountInfo && accountInfo.miniProgram && accountInfo.miniProgram.envVersion;
    if (envVersion === 'trial' || envVersion === 'develop') {
      hasAlertedDebug = true;
      wx.showModal({
        title: '体验版网络连接提示',
        content: '当前后端使用测试服务器 IP。如出现无法连接，请点击右上角「...」菜单 -> 选择「打开调试」(vConsole) -> 重启小程序即可正常使用！',
        confirmText: '我知道了',
        showCancel: false
      });
    }
  } catch (e) {}
}

/**
 * 规范化 URL 拼接，避免 BASE_URL 末尾与 path 开头产生冗余双斜杠（如 /api//screen）
 */
function buildUrl(path) {
  const base = (BASE_URL || '').replace(/\/+$/, '');
  const sub = (path || '').replace(/^\/+/, '');
  return base ? `${base}/${sub}` : `/${sub}`;
}

const TOKEN_KEY = 'corn_token';

/**
 * 后端 /screen/* 需要 Bearer 令牌（auth.py 中间件），登录后把 token 存到
 * storage 的 corn_token 即可自动带上；未登录时后端会返回 401。
 */
function authHeader() {
  try {
    const token = wx.getStorageSync(TOKEN_KEY);
    return token ? { Authorization: 'Bearer ' + token } : {};
  } catch (e) {
    return {};
  }
}

function buildHttpError(res, body, cost, rid, url) {
  const detail = (body && (body.detail || body.message)) || ('HTTP ' + res.statusCode);
  let suffix = '（HTTP ' + res.statusCode + ' · ' + cost + 'ms' + (rid ? ' · ' + rid : '') + '）';
  if (res.statusCode === 401) {
    suffix = '（登录态失效，已尝试自动重新登录 · ' + cost + 'ms）';
  } else if (res.statusCode === 200 && typeof body === 'string') {
    suffix = '（返回的是 HTML 而不是 JSON，通常说明 nginx 没把接口反代到后端）';
  }
  const err = new Error(detail + suffix);
  err.statusCode = res.statusCode;
  err.body = body;
  err.url = url;
  return err;
}

function request(path, method, data, retried) {
  const url = buildUrl(path);
  const verb = method || 'GET';
  const t0 = Date.now();
  return new Promise((resolve, reject) => {
    wx.request({
      url: url,
      method: verb,
      data: data,
      header: Object.assign({ 'Content-Type': 'application/json' }, authHeader()),
      // 服务端实测较慢（单请求可达 20s+），30s 容易误判为不可达
      timeout: 45000,
      success(res) {
        const cost = Date.now() - t0;
        const body = res.data;
        const h = res.header || {};
        const rid = h['X-Request-Id'] || h['x-request-id'] || '';
        // 打印完整响应，体验版开调试后可在 vConsole 直接看到
        console.log('[api] ' + verb + ' ' + url + ' -> ' + res.statusCode + ' (' + cost + 'ms)'
          + (rid ? ' rid=' + rid : ''), body);
        if (res.statusCode >= 200 && res.statusCode < 300 && body && body.code === 0) {
          resolve(body.data);
          return;
        }
        const err = buildHttpError(res, body, cost, rid, url);
        // 401：令牌缺失或过期时，用内置测试账号静默重登并重试一次（/auth/* 自身不重试，避免死循环）
        if (res.statusCode === 401 && !retried && path.indexOf('/auth/') !== 0) {
          const auth = require('./auth');
          auth.relogin()
            .then(() => request(path, method, data, true))
            .then(resolve)
            .catch(() => reject(err));
          return;
        }
        reject(err);
      },
      fail(err) {
        const cost = Date.now() - t0;
        notifyDebugGuidanceIfNeeded();
        const msg = (err && err.errMsg) || '';
        let hint = '';
        if (msg.indexOf('url not in domain list') >= 0 || msg.indexOf('CLEARTEXT') >= 0) {
          hint = '（微信拦截了该域名：体验版请点右上角「···」→「开发调试」后彻底关闭再重开）';
        } else if (msg.toLowerCase().indexOf('timeout') >= 0) {
          hint = '（已等待 ' + cost + 'ms 无响应，服务端过慢或不可达）';
        } else {
          hint = '（无法建立连接：请确认后端 8082 端口从手机网络可达）';
        }
        console.error('[api] fail ' + verb + ' ' + url + ' (' + cost + 'ms) ' + msg);
        const e = new Error('请求失败 [' + url + ']：' + msg + hint);
        e.url = url;
        e.errMsg = msg;
        reject(e);
      }
    });
  });
}

// 文件转 base64（data-url 形式，后端可直接接受）
function fileToDataUrl(filePath) {
  return new Promise((resolve, reject) => {
    const fs = wx.getFileSystemManager();
    fs.readFile({
      filePath,
      encoding: 'base64',
      success(res) {
        resolve('data:image/jpeg;base64,' + res.data);
      },
      fail(e) {
        reject(new Error('读取图片失败: ' + (e.errMsg || '')));
      }
    });
  });
}

/** 压缩图片到 <=1080px 再转 base64，避免上传体积过大 */
function compressToDataUrl(filePath) {
  return new Promise((resolve) => {
    wx.getImageInfo({
      src: filePath,
      success(info) {
        const maxSide = 1080;
        const scale = Math.min(1, maxSide / Math.max(info.width, info.height));
        const w = Math.round(info.width * scale);
        const h = Math.round(info.height * scale);
        const off = wx.createOffscreenCanvas({ type: '2d', width: w, height: h });
        const ctx = off.getContext('2d');
        const img = off.createImage();
        img.onload = () => {
          ctx.drawImage(img, 0, 0, w, h);
          const data = off.toDataURL('image/jpeg', 0.85);
          resolve(data);
        };
        img.onerror = () => resolve(fileToDataUrl(filePath));
        img.src = filePath;
      },
      fail() {
        resolve(fileToDataUrl(filePath));
      }
    });
  });
}

const api = {
  buildUrl,
  authHeader,
  TOKEN_KEY,
  notifyDebugGuidanceIfNeeded,

  /** 四类典型样本（含真实数据集 base64 图） */
  getSamples: () => request('/screen/samples'),

  /** 综合诊断：病害/置信度/Grad-CAM/病斑框/受损率/处方 */
  predict: (imageBase64, filename, model) =>
    request('/screen/predict', 'POST', {
      image_base64: imageBase64,
      filename: filename || 'upload.jpg',
      model: model || 'resnet50_cbam'
    }),

  /** 批量巡田识别 */
  predictBatch: (images, acreage) =>
    request('/screen/predict/batch', 'POST', {
      images: images,
      acreage_per_image: acreage || 1
    }),

  /** 诊断历史 */
  historyList: (limit, offset) => request('/screen/history?limit=' + (limit || 20) + '&offset=' + (offset || 0)),
  historyDetail: (id) => request('/screen/history/' + id),
  historyDelete: (id) => request('/screen/history/' + id, 'DELETE'),

  /** 遥测（微气候时序/病害分布/抗逆雷达） */
  telemetry: () => request('/screen/telemetry'),

  /** 病害图鉴知识库 */
  knowledge: () => request('/screen/knowledge'),

  /** 历史会话 */
  sessionList: (limit) => request('/screen/sessions?limit=' + (limit || 30)),
  sessionDetail: (sid) => request('/screen/sessions/' + sid),
  sessionDelete: (sid) => request('/screen/sessions/' + sid, 'DELETE'),

  /** 账号认证（后端 /auth/*，登录成功返回 {token, user, expires_in}） */
  login: (username, password, remember) =>
    request('/auth/login', 'POST', {
      username: username,
      password: password,
      remember: !!remember
    }),
  register: (username, password, displayName) =>
    request('/auth/register', 'POST', {
      username: username,
      password: password,
      display_name: displayName || username
    }),
  me: () => request('/auth/me'),
  logout: () => request('/auth/logout', 'POST', {}),
  authConfig: () => request('/auth/config'),

  compressToDataUrl,
  fileToDataUrl,
  BASE_URL
};

module.exports = api;
