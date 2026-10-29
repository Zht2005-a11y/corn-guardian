/**
 * 兼容占位页：AI 问答已合并进 pages/assistant（单页对话设计）。
 * 本页面未注册进 app.json，仅用于兼容开发者工具缓存中残留的旧页面清单。
 */
Page({
  onLoad() {
    wx.switchTab({ url: '/pages/assistant/assistant' });
  }
});
