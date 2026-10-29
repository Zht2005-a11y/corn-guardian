const api = require('../../utils/api');
const icons = require('../../utils/icons');
const util = require('../../utils/util');

const app = getApp();

const FILTER_MAP = {
  all: null,
  Blight: 'Blight',
  rust: 'Common_Rust',
  gray: 'Gray_Leaf_Spot',
  healthy: 'Healthy'
};

Page({
  data: {
    filters: [
      { key: 'all', label: '全部' },
      { key: 'Blight', label: '大斑病' },
      { key: 'rust', label: '锈病' },
      { key: 'gray', label: '灰斑病' },
      { key: 'healthy', label: '健康' }
    ],
    filter: 'all',
    allItems: [],
    showList: [],
    hasMore: false,
    loading: false,
    pageSize: 20,
    icons: {
      arrow: icons.make('arrow', '#C4CDD0', 2),
      trash: icons.make('trash', '#F16B5D', 1.6),
      leaf: icons.make('leaf', '#CBD5D6', 1.5)
    }
  },

  onLoad() {
    this.offset = 0;
    this.items = [];
  },

  onShow() {
    this.reload();
  },

  onPullDownRefresh() {
    this.reload(() => wx.stopPullDownRefresh());
  },

  reload(done) {
    this.offset = 0;
    this.items = [];
    this.fetchPage(done);
  },

  fetchPage(done) {
    this.setData({ loading: true });
    api.historyList(this.data.pageSize, this.offset)
      .then((d) => {
        const items = (d.items || []).map((it) => {
          const tag = util.severityTag(it.severity);
          return { ...it, tagCls: tag.cls, tagText: tag.text };
        });
        this.items = this.items.concat(items);
        this.offset += items.length;
        const hasMore = items.length >= this.data.pageSize;
        this.setData({ loading: false, hasMore });
        this.applyFilter();
        if (done) done();
      })
      .catch((err) => {
        this.setData({ loading: false });
        if (done) done();
        wx.showModal({ title: '加载失败', content: err.message, showCancel: false });
      });
  },

  loadMore() {
    if (this.data.loading) return;
    this.fetchPage();
  },

  switchFilter(e) {
    this.setData({ filter: e.currentTarget.dataset.key }, () => this.applyFilter());
  },

  applyFilter() {
    const key = FILTER_MAP[this.data.filter];
    const showList = key ? this.items.filter((it) => it.class_en === key) : this.items;
    this.setData({ showList });
  },

  openDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.showLoading({ title: '加载详情…' });
    api.historyDetail(id)
      .then((rec) => {
        wx.hideLoading();
        // 转换为识别结果页需要的结构
        app.globalData.lastResult = {
          class_name_cn: rec.class_name || util.classNameOf(rec.class_en),
          class_name_en: rec.class_en,
          confidence: rec.confidence,
          severity: rec.severity,
          damageRate: rec.damage_rate,
          boxes: rec.boxes || [],
          gradcam_base64: rec.gradcam_b64 || '',
          droneParams: rec.drone_params || {},
          prescription: rec.prescription || '',
          prescriptionLevel: rec.prescription_level || '',
          prescriptionDose: rec.prescription_dose || '',
          prescriptionNotes: rec.prescription_notes || [],
          model_used: rec.model_used,
          inference_ms: rec.inference_ms,
          pathogen: '',
          probabilities: {}
        };
        app.globalData.lastImage = rec.image_base64 || rec.thumb_small || '';
        if (!app.globalData.lastImage) {
          wx.showToast({ title: '该记录缺少原图', icon: 'none' });
        }
        wx.navigateTo({ url: '/pages/result/result' });
      })
      .catch((err) => {
        wx.hideLoading();
        wx.showModal({ title: '详情加载失败', content: err.message, showCancel: false });
      });
  },

  removeItem(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '删除确认',
      content: '确定删除这条识别记录吗？删除后不可恢复。',
      confirmColor: '#F16B5D',
      success: (res) => {
        if (!res.confirm) return;
        api.historyDelete(id)
          .then(() => {
            wx.showToast({ title: '已删除', icon: 'success' });
            this.reload();
          })
          .catch((err) => {
            wx.showModal({ title: '删除失败', content: err.message, showCancel: false });
          });
      }
    });
  },

  clearAll() {
    if (!this.items.length) return;
    wx.showModal({
      title: '清空确认',
      content: '将删除全部 ' + this.items.length + ' 条（当前已加载）识别记录，确定继续吗？',
      confirmColor: '#F16B5D',
      success: (res) => {
        if (!res.confirm) return;
        wx.showLoading({ title: '删除中…', mask: true });
        const ids = this.items.map((it) => it.id);
        Promise.all(ids.map((id) => api.historyDelete(id).catch(() => null)))
          .then(() => {
            wx.hideLoading();
            wx.showToast({ title: '已清空', icon: 'success' });
            this.reload();
          });
      }
    });
  },

  goIdentify() {
    wx.switchTab({ url: '/pages/identify/identify' });
  }
});
