/**
 * 登录态管理
 *
 * 后端 /auth/* 采用 JWT：登录后把 token 存进 storage（corn_token），
 * utils/api.js 会自动给每个请求带上 Authorization: Bearer <token>。
 * 令牌过期（401）时由 api.js 调用 relogin() 静默重登一次。
 *
 * 体验账号：admin / corn@2026（后端 auth.py 的演示账号）
 */
const TOKEN_KEY = 'corn_token';
const USER_KEY = 'corn_user';

const TEST_ACCOUNT = { username: 'admin', password: 'corn@2026' };

let pendingLogin = null;
let pendingRelogin = null;

function getToken() {
  try {
    return wx.getStorageSync(TOKEN_KEY) || '';
  } catch (e) {
    return '';
  }
}

function getUser() {
  try {
    return wx.getStorageSync(USER_KEY) || null;
  } catch (e) {
    return null;
  }
}

function saveSession(token, user) {
  try {
    wx.setStorageSync(TOKEN_KEY, token || '');
    wx.setStorageSync(USER_KEY, user || null);
  } catch (e) {}
}

function clearSession() {
  try {
    wx.removeStorageSync(TOKEN_KEY);
    wx.removeStorageSync(USER_KEY);
  } catch (e) {}
}

/** 账号密码登录（成功后自动落盘） */
function login(username, password, remember) {
  const api = require('./api');
  return api.login(username, password, remember).then((data) => {
    saveSession(data.token, data.user);
    return data;
  });
}

/** 注册（后端密码要求：至少 8 位且包含字母与数字） */
function register(username, password, displayName) {
  const api = require('./api');
  return api.register(username, password, displayName).then((data) => {
    // 后端注册成功一般直接返回 token；没有则用注册的账号再登一次
    if (data && data.token) {
      saveSession(data.token, data.user);
      return data;
    }
    return login(username, password, true);
  });
}

/**
 * 静默登录：已有令牌直接返回；否则用体验账号登录。
 * 并发调用只会真正发出一笔登录请求。
 */
function ensureLogin(force) {
  if (!force && getToken()) {
    return Promise.resolve(getUser());
  }
  if (pendingLogin) return pendingLogin;
  const api = require('./api');
  pendingLogin = api
    .login(TEST_ACCOUNT.username, TEST_ACCOUNT.password, true)
    .then((data) => {
      saveSession(data.token, data.user);
      pendingLogin = null;
      return data.user;
    })
    .catch((e) => {
      pendingLogin = null;
      throw e;
    });
  return pendingLogin;
}

/** 令牌失效后重登：先清空旧令牌，再强制走一次登录（并发只发一笔） */
function relogin() {
  if (pendingRelogin) return pendingRelogin;
  clearSession();
  pendingRelogin = ensureLogin(true).then(
    (user) => {
      pendingRelogin = null;
      return user;
    },
    (e) => {
      pendingRelogin = null;
      throw e;
    }
  );
  return pendingRelogin;
}

function logout() {
  const api = require('./api');
  return api
    .logout()
    .catch(() => null)
    .then(() => {
      clearSession();
    });
}

module.exports = {
  TOKEN_KEY,
  USER_KEY,
  TEST_ACCOUNT,
  getToken,
  getUser,
  saveSession,
  clearSession,
  login,
  register,
  ensureLogin,
  relogin,
  logout
};
