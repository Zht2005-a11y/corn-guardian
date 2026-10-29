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

module.exports = { formatTime, severityTag, classNameOf, CLASS_NAMES };
