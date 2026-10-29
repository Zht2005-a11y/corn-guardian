/**
 * 图标库（iconpark 官方线性风格，24×24 stroke 线性图标）
 * 以 base64 SVG data-uri 输出，供 <image> 标签直接使用。
 * 用法：icons.make('home', '#0BA77B') 返回 data:image/svg+xml;base64,...
 */
function make(name, color, strokeWidth) {
  const paths = ICON_PATHS[name];
  if (!paths) return '';
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="' +
    color + '" stroke-width="' + (strokeWidth || 1.8) +
    '" stroke-linecap="round" stroke-linejoin="round">' + paths + '</svg>';
  // 图标内容均为 ASCII（标签名 + hex 颜色），逐字符取码点构造 ArrayBuffer
  const buf = new ArrayBuffer(svg.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < svg.length; i++) view[i] = svg.charCodeAt(i) & 0xff;
  return 'data:image/svg+xml;base64,' + wx.arrayBufferToBase64(buf);
}

const ICON_PATHS = {
  // ---- 底部导航 ----
  home: '<path d="M4 11.5 12 4.5l8 7"/><path d="M6 10.5V20h12v-9.5"/><path d="M10 20v-5h4v5"/>',
  scan: '<path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8"/><path d="M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8"/><path d="M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16"/><path d="M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16"/><rect x="7.5" y="9.5" width="9" height="5" rx="1"/>',
  chat: '<path d="M12 4c-4.6 0-8 3-8 6.8 0 2.1 1.1 4 2.9 5.2L6 20l3.6-1.6c.8.2 1.6.3 2.4.3 4.6 0 8-3 8-6.9S16.6 4 12 4z"/><path d="M8.5 10.5h7M8.5 13.5h4.5"/>',
  user: '<circle cx="12" cy="8" r="3.6"/><path d="M5 20c.8-3.4 3.6-5.2 7-5.2s6.2 1.8 7 5.2"/>',
  // ---- 功能/业务 ----
  leaf: '<path d="M5 19C5 10 11 5 20 5c0 9-5 14-13 14"/><path d="M5 19c2.5-5 6-8.5 10-10.5"/>',
  drone: '<rect x="9" y="9" width="6" height="5" rx="1.4"/><path d="M7.5 5.5h3M13.5 5.5h3"/><path d="M9 5.5A2.4 2.4 0 0 0 6.6 7.9 2.4 2.4 0 0 0 9 10.3M15 5.5a2.4 2.4 0 0 1 2.4 2.4 2.4 2.4 0 0 1-2.4 2.4"/><path d="M7.5 18.5h3M13.5 18.5h3"/><path d="M9 18.5a2.4 2.4 0 0 1-2.4-2.4A2.4 2.4 0 0 1 9 13.7M15 18.5a2.4 2.4 0 0 0 2.4-2.4 2.4 2.4 0 0 0-2.4-2.4"/><path d="M12 14v2.2"/>',
  robot: '<rect x="5" y="8" width="14" height="10" rx="2.5"/><circle cx="9.5" cy="12.5" r="1.2" fill="currentColor" stroke="none"/><circle cx="14.5" cy="12.5" r="1.2" fill="currentColor" stroke="none"/><path d="M12 8V5.5"/><circle cx="12" cy="4.5" r="1"/><path d="M9 15.5h6"/>',
  history: '<circle cx="12" cy="12" r="8"/><path d="M12 8v4.4l3 1.8"/>',
  camera: '<path d="M8.5 6.5 10 4.5h4l1.5 2H19A1.5 1.5 0 0 1 20.5 8v9.5A1.5 1.5 0 0 1 19 19H5a1.5 1.5 0 0 1-1.5-1.5V8A1.5 1.5 0 0 1 5 6.5h3.5z"/><circle cx="12" cy="12.4" r="3.4"/>',
  photo: '<rect x="4" y="5" width="16" height="14" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="M4.5 16.5 9.5 12l3.5 3 3-2.5 3.5 3"/>',
  send: '<g transform="scale(0.5)" stroke-width="4"><path d="M43 5L29.7 43L22.1 25.9L5 18.3L43 5Z"/><path d="M43.0001 5L22.1001 25.9"/></g>',
  arrow: '<path d="M9 5.5 15.5 12 9 18.5"/>',
  back: '<path d="M14.5 5.5 8 12l6.5 6.5"/>',
  location: '<path d="M12 21s6.5-5.4 6.5-10.5a6.5 6.5 0 1 0-13 0C5.5 15.6 12 21 12 21z"/><circle cx="12" cy="10.5" r="2.4"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/>',
  humidity: '<path d="M12 3.5s5.5 6 5.5 9.8A5.5 5.5 0 0 1 12 19a5.5 5.5 0 0 1-5.5-5.7C6.5 9.5 12 3.5 12 3.5z"/>',
  wind: '<path d="M3.5 8.5h10a2.8 2.8 0 1 0-2.8-2.8"/><path d="M3.5 12.5h14a2.8 2.8 0 1 1-2.8 2.8"/><path d="M3.5 16.5h6"/>',
  temp: '<path d="M10 4.5a2 2 0 1 1 4 0V13a4.5 4.5 0 1 1-4 0z"/><circle cx="12" cy="16.8" r="1.6" fill="currentColor" stroke="none"/><path d="M12 15.5V9"/>',
  chart: '<path d="M4 4v16h16"/><path d="M8 15.5 11.5 10l3 3L19 7"/>',
  trash: '<path d="M5 7h14"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7"/><path d="M7 7l.8 12h8.4L17 7"/><path d="M10.5 10.5v5M13.5 10.5v5"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  refresh: '<path d="M19 12a7 7 0 1 1-2.2-5.1"/><path d="M19 4v4h-4"/>',
  model: '<rect x="5" y="5" width="14" height="14" rx="2.5"/><path d="M9 9h6v6H9z"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5"/>',
  drop: '<path d="M10 3.5h4M12 3.5V8"/><path d="M9.5 8h5l1.5 4.5v7A1.5 1.5 0 0 1 14.5 21h-5A1.5 1.5 0 0 1 8 19.5v-7z"/>',
  height: '<path d="M12 3v18"/><path d="M9 6l3-3 3 3M9 18l3 3 3-3"/>',
  speed: '<path d="M4.5 15.5a8 8 0 1 1 15 0"/><path d="M12 14.5 16 9.5"/><circle cx="12" cy="15.5" r="1.4" fill="currentColor" stroke="none"/>',
  size: '<path d="M4 4h5M4 4v5M20 20h-5M20 20v-5"/><rect x="6.5" y="6.5" width="11" height="11" rx="1"/>',
  shield: '<path d="M12 3.5 19 6v5.5c0 4.5-3 7.6-7 9-4-1.4-7-4.5-7-9V6z"/><path d="M9 11.5l2.2 2.2L15.5 9.5"/>',
  file: '<path d="M6 3.5h8L19 8.5v12H6z"/><path d="M14 3.5v5h5"/><path d="M9 12h6M9 15.5h6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>'
};

module.exports = { make };
