const api = require('../../utils/api');
const icons = require('../../utils/icons');
const chart = require('../../utils/chart');

Page({
  data: {
    tab: 'climate',
    current: null,
    distribution: [],
    radar: [],
    dataMark: '',
    barMark: '',
    icons: {
      temp: icons.make('temp', '#7C6BF1'),
      humidity: icons.make('humidity', '#4FC3F7'),
      sun: icons.make('sun', '#F9AD19')
    }
  },

  onLoad() {
    this.climateData = null;
    this.fetchTelemetry();
  },

  switchTab(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ tab: key }, () => this.drawActive());
  },

  fetchTelemetry() {
    api.telemetry()
      .then((d) => {
        const c = d.climate || {};
        this.climateData = c;
        this.setData({
          current: {
            temp: c.currentTemp,
            humidity: Math.round(c.currentHumidity),
            light: c.currentLight
          },
          distribution: d.distribution || [],
          radar: d.radar || [],
          // 后端注明：当前遥测为示范田静态演示数据，接真实传感器后自动更新
          dataMark: '数据来源：后端 /screen/telemetry（示范区演示数据，接入真实传感器后自动更新）',
          barMark: '近 7 日趋势基于后端分布占比估算（演示数据，接口未提供逐日统计）'
        });
        this.drawActive();
      })
      .catch((err) => {
        this.setData({ dataMark: '加载失败：' + err.message });
      });
  },

  drawActive() {
    const tab = this.data.tab;
    if (tab === 'climate') this.drawLine();
    if (tab === 'disease') this.drawBar();
    if (tab === 'radar') this.drawRadar();
  },

  getCanvas(id, cb) {
    const query = wx.createSelectorQuery().in(this);
    query.select('#' + id).fields({ node: true, size: true }).exec((res) => {
      if (res && res[0] && res[0].node) cb(res[0].node, res[0].width, res[0].height);
    });
  },

  drawLine() {
    const c = this.climateData;
    if (!c) return;
    this.getCanvas('lineChart', (node, w, h) => {
      chart.drawLineChart(node, w, h, {
        labels: c.hours,
        series: [
          { name: '温度(℃)', color: '#7C6BF1', data: c.temperatures },
          { name: '湿度(%)', color: '#4FA8F7', data: c.humidities },
          { name: '光照(kLux)', color: '#F9AD19', data: c.lights }
        ]
      });
    });
  },

  drawBar() {
    const dist = this.data.distribution;
    if (!dist.length) return;
    // 后端只提供分布占比；按占比确定性估算近 7 日频次（演示用途，已在页面标注）
    const dates = [];
    const series = dist.map((d) => ({ name: d.name, color: d.color, data: [] }));
    const now = Date.now();
    for (let i = 6; i >= 0; i--) {
      const dt = new Date(now - i * 86400000);
      dates.push((dt.getMonth() + 1) + '.' + dt.getDate());
    }
    dates.forEach((_, gi) => {
      dist.forEach((d, si) => {
        const wave = 0.75 + 0.25 * Math.abs(Math.sin(gi * 1.7 + si));
        series[si].data.push(Math.round((d.value / 100) * 40 * wave));
      });
    });
    this.getCanvas('barChart', (node, w, h) => {
      chart.drawBarChart(node, w, h, { labels: dates, series });
    });
  },

  drawRadar() {
    const radar = this.data.radar;
    if (!radar.length) return;
    this.getCanvas('radarChart', (node, w, h) => {
      chart.drawRadar(node, w, h, {
        indicators: radar.map((r) => r.name),
        value: radar.map((r) => r.value),
        color: '#0BA77B'
      });
    });
  }
});
