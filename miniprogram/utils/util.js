/** 通用小工具 */
function formatTime(ts) {
  const d = ts ? new Date(ts) : new Date();
  const p = (n) => (n < 10 ? '0' + n : '' + n);
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' +
    p(d.getHours()) + ':' + p(d.getMinutes());
}

/** 病害等级 -> 标签样式 */
function severityTag(severity) {
  const s = String(severity || '');
  if (!s || s === '—') return { cls: 'tag-gray', text: '无' };
  if (s.indexOf('轻') >= 0 || s.indexOf('I') === 0) return { cls: 'tag-green', text: '轻度' };
  if (s.indexOf('中') >= 0 || s.indexOf('II') === 0) return { cls: 'tag-orange', text: '中度' };
  if (s.indexOf('重') >= 0 || s.indexOf('III') === 0) return { cls: 'tag-red', text: '重度' };
  if (s.indexOf('危急') >= 0 || s.indexOf('IV') === 0) return { cls: 'tag-red', text: '危急' };
  return { cls: 'tag-gray', text: s };
}

/** 病害类别中文名 */
const CLASS_NAMES = {
  Blight: '大斑病',
  Common_Rust: '普通锈病',
  Gray_Leaf_Spot: '灰斑病',
  Healthy: '健康'
};
function classNameOf(classEn) {
  return CLASS_NAMES[classEn] || classEn || '未知';
}

/**
 * tabBar 页面清单，必须与 app.json 的 tabBar.list 保持一致。
 * 微信规定 tabBar 页面只能用 wx.switchTab 打开，用 navigateTo 会静默失败
 * （控制台报 can not navigateTo a tabbar page），表现就是「点了没反应」。
 */
const TAB_PAGES = [
  '/pages/home/home',
  '/pages/identify/identify',
  '/pages/assistant/assistant',
  '/pages/mine/mine'
];

/** 统一跳转入口：自动判断目标是否为 tabBar 页面 */
function navigate(url) {
  if (!url) return;
  const target = url.charAt(0) === '/' ? url : '/' + url;
  if (TAB_PAGES.indexOf(target) >= 0) {
    wx.switchTab({ url: target });
    return;
  }
  wx.navigateTo({ url: target });
}

module.exports = { formatTime, severityTag, classNameOf, CLASS_NAMES, TAB_PAGES, navigate };
