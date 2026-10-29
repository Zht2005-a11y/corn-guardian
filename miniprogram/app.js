const { BASE_URL } = require('./utils/config');

App({
  globalData: {
    apiBase: BASE_URL,
    // 最近一次识别结果（identify -> result -> spray 之间传递）
    lastResult: null,
    lastImage: '',
    // 当前 AI 会话标识
    chatSessionId: '',
    userInfo: null
  },
  onLaunch() {
    // 预留：登录态获取、位置授权等
  }
});
