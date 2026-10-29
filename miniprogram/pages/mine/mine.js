const api = require('../../utils/api');
const auth = require('../../utils/auth');
const icons = require('../../utils/icons');

Page({
  data: {
    stats: { total: 0, today: 0 },
    online: false,
    initial: '玉',
    user: {},
    loggedIn: false,
    icons: {
      chart: icons.make('chart', '#0BA77B'),
      history: icons.make('history', '#FF984F'),
      user: icons.make('user', '#8C999C'),
      arrow: icons.make('arrow', '#C4CDD0', 2)
    }
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 3 });
    }
    this.syncUser();

    api
      .historyList(1, 0)
      .then((d) => {
        this.setData({
          stats: d.stats || { total: 0, today: 0 },
          online: true
        });
      })
      .catch(() => this.setData({ online: false }));
  },

  /** 从本地会话同步当前账号 */
  syncUser() {
    const token = auth.getToken();
    const user = auth.getUser() || {};
    const name = user.display_name || user.username || '';
    this.setData({
      user: user,
      loggedIn: !!token,
      initial: name ? name.slice(0, 1).toUpperCase() : '玉'
    });
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  },

  doLogout() {
    wx.showModal({
      title: '退出登录',
      content: '退出后将回到未登录状态，部分接口无法访问，确定退出？',
      success: (res) => {
        if (!res.confirm) return;
        auth.logout().then(() => {
          this.syncUser();
          wx.showToast({ title: '已退出登录', icon: 'none' });
        });
      }
    });
  },

  goMonitor() {
    wx.navigateTo({ url: '/pages/monitor/monitor' });
  },
  goHistory() {
    wx.navigateTo({ url: '/pages/history/history' });
  }
});
