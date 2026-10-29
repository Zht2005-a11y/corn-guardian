const api = require('../../utils/api');
const icons = require('../../utils/icons');
const util = require('../../utils/util');

Page({
  data: {
    statusBarHeight: 20,
    icons: {
      location: icons.make('location', '#FFFFFF'),
      drone: icons.make('drone', '#FFFFFF', 1.6),
      droneBlue: icons.make('drone', '#2E7CE6'),
      leaf: icons.make('leaf', '#0BA77B'),
      robot: icons.make('robot', '#8E6BF1'),
      history: icons.make('history', '#FF984F'),
      sun: icons.make('sun', '#F9AD19'),
      humidity: icons.make('humidity', '#4FC3F7'),
      wind: icons.make('wind', '#8C999C')
    },
    weather: { temp: '', desc: '', humidity: '', wind: '' },
    recent: null
  },

  onLoad() {
    const win = wx.getWindowInfo();
    this.setData({ statusBarHeight: win.statusBarHeight || 20 });
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
    this.fetchWeather();
    this.fetchRecent();
  },

  fetchWeather() {
    // 数据来自后端 /screen/telemetry（后端当前为示范田演示数据，接入真实传感器后自动更新）
    api.telemetry()
      .then((d) => {
        const c = d.climate || {};
        this.setData({
          weather: {
            temp: c.currentTemp !== undefined ? c.currentTemp + '°C' : '',
            desc: '田间实测',
            humidity: c.currentHumidity !== undefined ? Math.round(c.currentHumidity) : '--',
            wind: c.windSpeed !== undefined ? c.windSpeed : '--'
          }
        });
      })
      .catch(() => {
        this.setData({ weather: { temp: '', desc: '未连接', humidity: '--', wind: '--' } });
      });
  },

  fetchRecent() {
    api.historyList(1, 0)
      .then((d) => {
        const item = d.items && d.items[0];
        if (!item) { this.setData({ recent: null }); return; }
        const tag = util.severityTag(item.severity);
        this.setData({
          recent: { ...item, tagCls: tag.cls, tagText: tag.text }
        });
      })
      .catch(() => this.setData({ recent: null }));
  },

  go(e) {
    wx.navigateTo({ url: e.currentTarget.dataset.url });
  },
  goMonitor() {
    wx.navigateTo({ url: '/pages/monitor/monitor' });
  },
  goHistory() {
    wx.navigateTo({ url: '/pages/history/history' });
  }
});
