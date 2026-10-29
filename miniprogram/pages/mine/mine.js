const api = require('../../utils/api');
const icons = require('../../utils/icons');

const app = getApp();

Page({
  data: {
    stats: { total: 0, today: 0 },
    online: false,
    apiBase: api.BASE_URL,
    initial: '玉',
    icons: {
      chart: icons.make('chart', '#0BA77B'),
      history: icons.make('history', '#FF984F'),
      model: icons.make('model', '#8E6BF1'),
      arrow: icons.make('arrow', '#C4CDD0', 2)
    }
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 3 });
    }
    this.setData({ apiBase: app.globalData.apiBase });
    api.historyList(1, 0)
      .then((d) => {
        this.setData({
          stats: d.stats || { total: 0, today: 0 },
          online: true
        });
      })
      .catch(() => this.setData({ online: false }));
  },

  goMonitor() {
    wx.navigateTo({ url: '/pages/monitor/monitor' });
  },
  goHistory() {
    wx.navigateTo({ url: '/pages/history/history' });
  },
  showApi() {
    wx.showModal({
      title: '后端服务地址',
      content: this.data.apiBase + '\n\n在 utils/config.js 中修改 BASE_URL；真机调试请使用电脑局域网 IP。',
      showCancel: false
    });
  }
});
