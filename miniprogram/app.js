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
    // 体验版与开发版自动开启调试模式（vConsole），以便放行 HTTP 请求与测试服务器 IP
    try {
      const accountInfo = wx.getAccountInfoSync && wx.getAccountInfoSync();
      const envVersion = accountInfo && accountInfo.miniProgram && accountInfo.miniProgram.envVersion;
      if (envVersion === 'develop' || envVersion === 'trial') {
        wx.setEnableDebug({
          enableDebug: true,
          success: () => console.log('[CornGuardian] 已自动为体验版/开发版启用调试模式'),
          fail: (e) => console.warn('[CornGuardian] 启用调试模式失败:', e)
        });
      }
    } catch (e) {
      console.warn('[CornGuardian] 环境检测异常:', e);
    }
  }
});
