const chart = require('../../utils/chart');
const icons = require('../../utils/icons');
const util = require('../../utils/util');

const app = getApp();

Page({
  data: {
    result: null,
    imagePath: '',
    icons: { leaf: icons.make('leaf', '#0BA77B'), gradcam: icons.make('model', '#FFFFFF', 1.6) },
    tagCls: 'tag-gray',
    tagText: '—',
    tagBg: '#E3F5EF',
    levelPercent: 0,
    probList: []
  },

  onShow() {
    const result = app.globalData.lastResult;
    if (!result) return;
    const tag = util.severityTag(result.severity);
    const probs = result.probabilities || {};
    const colorMap = {
      Blight: '#E28557',
      Common_Rust: '#D97706',
      Gray_Leaf_Spot: '#6366F1',
      Healthy: '#16A34A'
    };
    const probList = Object.keys(probs).map((k) => ({
      name: util.classNameOf(k),
      value: Math.round((probs[k] || 0) * 1000) / 10,
      color: colorMap[k] || '#0BA77B'
    })).sort((a, b) => b.value - a.value);

    this.setData({
      result,
      imagePath: app.globalData.lastImage,
      tagCls: tag.cls,
      tagText: tag.text,
      tagBg: tag.cls === 'tag-red' ? '#FDECEA' : tag.cls === 'tag-orange' ? '#FFF0E6' : '#E3F5EF',
      levelPercent: this.levelPercentOf(result.severity, result.damageRate),
      probList
    });
  },

  onReady() {
    if (this.data.result) {
      this.drawRing();
    }
  },

  levelPercentOf(severity, damageRate) {
    // 四级刻度：轻/中/重/危，结合受损率计算进度
    const s = String(severity || '');
    let base = 12.5;
    if (s.indexOf('I') === 0 || s.indexOf('轻') >= 0) base = 12.5;
    else if (s.indexOf('II') === 0 || s.indexOf('中') >= 0) base = 37.5;
    else if (s.indexOf('III') === 0 || s.indexOf('重') >= 0) base = 62.5;
    else if (s.indexOf('IV') === 0 || s.indexOf('危急') >= 0) base = 87.5;
    return Math.min(100, Math.max(base, Math.round(damageRate)));
  },

  drawRing() {
    const query = wx.createSelectorQuery().in(this);
    query.select('#ring').fields({ node: true, size: true }).exec((res) => {
      if (!res || !res[0] || !res[0].node) return;
      const canvas = res[0].node;
      const size = res[0].width;
      chart.drawRing(canvas, size, this.data.result.damageRate, '#FF984F');
    });
  },

  goSpray() {
    wx.navigateTo({ url: '/pages/spray/spray' });
  }
});
