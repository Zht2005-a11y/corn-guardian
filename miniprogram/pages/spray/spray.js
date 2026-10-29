const icons = require('../../utils/icons');
const util = require('../../utils/util');

const app = getApp();

Page({
  data: {
    hasResult: false,
    result: null,
    tagCls: 'tag-gray',
    tagText: '—',
    notes: [],
    showDetail: false,
    icons: {
      droneWhite: icons.make('drone', '#FFFFFF', 1.6),
      drone: icons.make('drone', '#0BA77B'),
      drop: icons.make('drop', '#4FC3F7'),
      size: icons.make('size', '#8E6BF1'),
      height: icons.make('height', '#FF984F'),
      speed: icons.make('speed', '#0BA77B')
    }
  },

  onShow() {
    const result = app.globalData.lastResult;
    if (!result || result.rejected) {
      this.setData({ hasResult: false, result: null });
      return;
    }
    const tag = util.severityTag(result.severity);
    this.setData({
      hasResult: true,
      result,
      tagCls: tag.cls,
      tagText: tag.text,
      notes: Array.isArray(result.prescriptionNotes) ? result.prescriptionNotes : []
    });
  },

  toggleDetail() {
    this.setData({ showDetail: !this.data.showDetail });
  },

  goIdentify() {
    wx.switchTab({ url: '/pages/identify/identify' });
  }
});
