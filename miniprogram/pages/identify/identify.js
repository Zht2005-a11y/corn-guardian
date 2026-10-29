const api = require('../../utils/api');
const icons = require('../../utils/icons');
const util = require('../../utils/util');

const app = getApp();

Page({
  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
  },

  data: {
    modes: [
      { key: 'single', label: '单张识别' },
      { key: 'batch', label: '批量识别' },
      { key: 'compare', label: '多模型对比' },
      { key: 'base64', label: 'Base64' }
    ],
    mode: 'single',
    icons: { camera: icons.make('camera', '#0BA77B'), photo: icons.make('photo', '#0BA77B') },
    examples: [
      { name: '大斑病', img: '/assets/images/img_blight.jpg' },
      { name: '普通锈病', img: '/assets/images/img_rust.jpg' },
      { name: '灰斑病', img: '/assets/images/img_gray.jpg' },
      { name: '健康', img: '/assets/images/img_healthy.jpg' }
    ],
    imagePath: '',
    imageB64: '',
    base64Text: '',
    batchList: [],
    batchSummary: null,
    batchItems: [],
    loading: false,
    actionText: '选择图片'
  },

  switchMode(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ mode: key });
    this.updateActionText();
  },

  updateActionText() {
    const { mode, imagePath, batchList, base64Text } = this.data;
    let text = '选择图片';
    if (mode === 'single' && imagePath) text = '开始识别';
    if (mode === 'compare' && imagePath) text = '开始对比识别';
    if (mode === 'base64' && base64Text) text = '开始识别';
    if (mode === 'batch') text = batchList.length ? '开始批量识别' : '选择图片';
    this.setData({ actionText: text });
  },

  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath;
        this.setData({ imagePath: path, imageB64: '' });
        this.updateActionText();
      }
    });
  },

  clearImage() {
    this.setData({ imagePath: '', imageB64: '' });
    this.updateActionText();
  },

  chooseBatch() {
    wx.chooseMedia({
      count: 9,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const paths = res.tempFiles.map((f) => f.tempFilePath);
        this.setData({ batchList: paths, batchSummary: null, batchItems: [] });
        this.updateActionText();
      }
    });
  },

  clearBatch() {
    this.setData({ batchList: [], batchSummary: null, batchItems: [] });
    this.updateActionText();
  },

  onBase64Input(e) {
    this.setData({ base64Text: e.detail.value.trim() });
    this.updateActionText();
  },

  /** 点击示例图 → 作为待识别图片 */
  useExample(e) {
    const path = e.currentTarget.dataset.path;
    this.setData({ mode: 'single', imagePath: path, imageB64: '' });
    this.updateActionText();
    wx.showToast({ title: '已选示例图，可直接开始识别', icon: 'none', duration: 1200 });
  },

  onAction() {
    if (this.data.loading) return;
    const { mode } = this.data;
    if (mode === 'single' || mode === 'compare') {
      if (!this.data.imagePath) return this.chooseImage();
      this.runSingle(this.data.imagePath);
    } else if (mode === 'base64') {
      if (!this.data.base64Text) {
        wx.showToast({ title: '请先粘贴图片 Base64', icon: 'none' });
        return;
      }
      this.predictB64(this.data.base64Text, 'base64_upload.jpg');
    } else if (mode === 'batch') {
      if (!this.data.batchList.length) return this.chooseBatch();
      this.runBatch();
    }
  },

  runSingle(path) {
    this.setData({ loading: true });
    wx.showLoading({ title: 'AI 识别中…', mask: true });
    api.compressToDataUrl(path)
      .then((b64) => {
        this.setData({ imageB64: b64 });
        return api.predict(b64, 'miniprogram_upload.jpg');
      })
      .then((result) => {
        wx.hideLoading();
        this.setData({ loading: false });
        if (result.rejected) {
          wx.showModal({ title: '无法识别', content: result.reject_reason, showCancel: false });
          return;
        }
        app.globalData.lastResult = result;
        app.globalData.lastImage = this.data.imagePath;
        wx.navigateTo({ url: '/pages/result/result' });
      })
      .catch((err) => {
        wx.hideLoading();
        this.setData({ loading: false });
        wx.showModal({ title: '识别失败', content: err.message, showCancel: false });
      });
  },

  predictB64(raw, filename) {
    this.setData({ loading: true });
    wx.showLoading({ title: 'AI 识别中…', mask: true });
    const b64 = raw.indexOf('data:') === 0 ? raw : 'data:image/jpeg;base64,' + raw;
    api.predict(b64, filename)
      .then((result) => {
        wx.hideLoading();
        this.setData({ loading: false });
        if (result.rejected) {
          wx.showModal({ title: '无法识别', content: result.reject_reason, showCancel: false });
          return;
        }
        app.globalData.lastResult = result;
        app.globalData.lastImage = b64;
        wx.navigateTo({ url: '/pages/result/result' });
      })
      .catch((err) => {
        wx.hideLoading();
        this.setData({ loading: false });
        wx.showModal({ title: '识别失败', content: err.message, showCancel: false });
      });
  },

  runBatch() {
    const list = this.data.batchList;
    this.setData({ loading: true });
    wx.showLoading({ title: '批量识别中…', mask: true });
    Promise.all(list.map((p) => api.compressToDataUrl(p)))
      .then((b64s) =>
        api.predictBatch(
          b64s.map((b, i) => ({ image_base64: b, filename: 'batch_' + (i + 1) + '.jpg' })),
          1
        )
      )
      .then((d) => {
        wx.hideLoading();
        this.setData({ loading: false });
        const items = d.items.map((it) => {
          const tag = util.severityTag(it.severity);
          return { ...it, tagCls: tag.cls, tagText: tag.text };
        });
        this.setData({ batchSummary: d.summary, batchItems: items });
        if (d.errors && d.errors.length) {
          wx.showToast({ title: d.errors.length + ' 张失败', icon: 'none' });
        }
      })
      .catch((err) => {
        wx.hideLoading();
        this.setData({ loading: false });
        wx.showModal({ title: '批量识别失败', content: err.message, showCancel: false });
      });
  },

  onUnload() {
    // 释放批量预览临时文件由系统自动管理
  }
});
