const auth = require('../../utils/auth');
const api = require('../../utils/api');

Page({
  data: {
    mode: 'login',
    username: 'admin',
    password: 'corn@2026',
    displayName: '',
    remember: true,
    loading: false,
    error: '',
    allowRegister: true
  },

  onLoad() {
    // 后端登录页配置（注册开关 / 演示账号），失败不影响手动输入
    api
      .authConfig()
      .then((cfg) => {
        const patch = {};
        if (cfg && cfg.allow_register === false) patch.allowRegister = false;
        const acc = cfg && cfg.demo_accounts && cfg.demo_accounts[0];
        if (acc && acc.username) {
          patch.username = acc.username;
          patch.password = acc.password || this.data.password;
        }
        this.setData(patch);
      })
      .catch(() => {});
  },

  switchMode(e) {
    const mode = e.currentTarget.dataset.mode;
    if (mode === this.data.mode) return;
    this.setData({ mode: mode, error: '' });
  },

  onInput(e) {
    const key = e.currentTarget.dataset.key;
    const patch = { error: '' };
    patch[key] = e.detail.value;
    this.setData(patch);
  },

  toggleRemember() {
    this.setData({ remember: !this.data.remember });
  },

  useDemo() {
    this.setData({
      username: auth.TEST_ACCOUNT.username,
      password: auth.TEST_ACCOUNT.password,
      error: ''
    });
  },

  submit() {
    if (this.data.loading) return;
    const username = (this.data.username || '').trim();
    const password = this.data.password || '';
    if (!username) {
      this.setData({ error: '请填写账号' });
      return;
    }
    if (!password) {
      this.setData({ error: '请填写密码' });
      return;
    }

    this.setData({ loading: true, error: '' });
    const task =
      this.data.mode === 'register'
        ? auth.register(username, password, (this.data.displayName || '').trim() || username)
        : auth.login(username, password, this.data.remember);

    task
      .then(() => {
        this.setData({ loading: false });
        const pages = getCurrentPages();
        if (pages.length > 1) {
          wx.navigateBack();
        } else {
          wx.reLaunch({ url: '/pages/home/home' });
        }
      })
      .catch((e) => {
        this.setData({ loading: false, error: (e && e.message) || '登录失败，请稍后重试' });
      });
  }
});
