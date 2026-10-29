const icons = require('../utils/icons');

Component({
  data: {
    selected: 0,
    list: [
      { pagePath: 'pages/home/home', text: '首页', icon: '', iconActive: '' },
      { pagePath: 'pages/identify/identify', text: '识别', icon: '', iconActive: '' },
      { pagePath: 'pages/assistant/assistant', text: '问答', icon: '', iconActive: '' },
      { pagePath: 'pages/mine/mine', text: '我的', icon: '', iconActive: '' }
    ]
  },
  lifetimes: {
    attached() {
      const GRAY = '#8C999C';
      const GREEN = '#0BA77B';
      const names = ['home', 'scan', 'chat', 'user'];
      const list = this.data.list.map((item, i) => ({
        ...item,
        icon: icons.make(names[i], GRAY, 1.7),
        iconActive: icons.make(names[i], GREEN, 1.7)
      }));
      this.setData({ list });
    }
  },
  methods: {
    switchTab(e) {
      const { path, index } = e.currentTarget.dataset;
      wx.switchTab({ url: '/' + path });
      this.setData({ selected: index });
    }
  }
});
