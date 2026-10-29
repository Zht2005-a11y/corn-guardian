/**
 * 轻量 Canvas 2D 图表（折线 / 分组柱状 / 雷达 / 环形进度）
 * 不依赖 ECharts，避免 npm 构建；视觉风格与参考图一致（浅色、细网格）。
 */
function setupCanvas(canvas, cssWidth, cssHeight) {
  const dpr = wx.getWindowInfo().pixelRatio || 2;
  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  return ctx;
}

/** 24h 微气候多折线图 */
function drawLineChart(canvas, width, height, opt) {
  const ctx = setupCanvas(canvas, width, height);
  const { labels, series, unitRight } = opt;
  const padL = 34, padR = unitRight ? 40 : 16, padT = 30, padB = 24;
  const W = width - padL - padR, H = height - padT - padB;

  ctx.clearRect(0, 0, width, height);

  // 所有系列归一到 0~100，各自标注真实范围
  const norm = (v, min, max) => ((v - min) / (max - min || 1)) * 100;

  // 网格与 y 轴（左轴）
  ctx.strokeStyle = '#E9EFF0';
  ctx.fillStyle = '#8C999C';
  ctx.lineWidth = 1;
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = padT + (H * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(padL + W, y);
    ctx.stroke();
    ctx.fillText(String(100 - (i * 100) / 4), padL - 6, y + 3);
  }

  // x 轴刻度
  ctx.textAlign = 'center';
  const step = Math.ceil(labels.length / 6);
  labels.forEach((lb, i) => {
    if (i % step !== 0 && i !== labels.length - 1) return;
    const x = padL + (W * i) / (labels.length - 1 || 1);
    ctx.fillText(lb, x, height - 8);
  });

  series.forEach((s) => {
    const vals = s.data;
    const min = Math.min.apply(null, vals);
    const max = Math.max.apply(null, vals);
    ctx.strokeStyle = s.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    vals.forEach((v, i) => {
      const x = padL + (W * i) / (vals.length - 1 || 1);
      const y = padT + H - (norm(v, min, max) / 100) * H;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });

  // 图例
  let lx = padL;
  ctx.textAlign = 'left';
  series.forEach((s) => {
    ctx.fillStyle = s.color;
    ctx.fillRect(lx, 8, 12, 3);
    ctx.fillStyle = '#4F5B5E';
    ctx.fillText(s.name, lx + 16, 13);
    lx += ctx.measureText(s.name).width + 34;
  });
}

/** 分组柱状图 */
function drawBarChart(canvas, width, height, opt) {
  const ctx = setupCanvas(canvas, width, height);
  const { labels, series } = opt;
  const padL = 30, padR = 12, padT = 30, padB = 24;
  const W = width - padL - padR, H = height - padT - padB;
  ctx.clearRect(0, 0, width, height);

  let maxV = 0;
  series.forEach((s) => s.data.forEach((v) => { if (v > maxV) maxV = v; }));
  maxV = Math.ceil(maxV / 10) * 10 || 10;

  ctx.strokeStyle = '#E9EFF0';
  ctx.fillStyle = '#8C999C';
  ctx.lineWidth = 1;
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = padT + (H * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(padL + W, y);
    ctx.stroke();
    ctx.fillText(String(Math.round(maxV - (i * maxV) / 4)), padL - 5, y + 3);
  }

  const groupW = W / labels.length;
  const barW = Math.min(10, (groupW * 0.7) / series.length);
  labels.forEach((lb, gi) => {
    const gx = padL + groupW * gi;
    series.forEach((s, si) => {
      const v = s.data[gi] || 0;
      const bh = (v / maxV) * H;
      const x = gx + groupW * 0.15 + si * (barW + 2);
      ctx.fillStyle = s.color;
      // 圆角柱
      const r = Math.min(3, barW / 2, bh);
      const y = padT + H - bh;
      ctx.beginPath();
      ctx.moveTo(x, padT + H);
      ctx.lineTo(x, y + r);
      ctx.arc(x + r, y + r, r, Math.PI, 0, true);
      ctx.lineTo(x + barW, padT + H);
      ctx.closePath();
      ctx.fill();
    });
    ctx.fillStyle = '#8C999C';
    ctx.textAlign = 'center';
    ctx.fillText(lb, gx + groupW / 2, height - 8);
    ctx.textAlign = 'right';
  });

  // 图例
  let lx = padL;
  ctx.textAlign = 'left';
  series.forEach((s) => {
    ctx.fillStyle = s.color;
    ctx.beginPath();
    ctx.arc(lx + 5, 10, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#4F5B5E';
    ctx.fillText(s.name, lx + 13, 13);
    lx += ctx.measureText(s.name).width + 30;
  });
}

/** 六维雷达图 */
function drawRadar(canvas, width, height, opt) {
  const ctx = setupCanvas(canvas, width, height);
  const { indicators, value: values, color } = opt;
  const cx = width / 2, cy = height / 2 + 6;
  const R = Math.min(width, height) / 2 - 34;
  const n = indicators.length;
  ctx.clearRect(0, 0, width, height);

  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2;

  // 网格
  ctx.strokeStyle = '#E9EFF0';
  for (let ring = 1; ring <= 4; ring++) {
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const a = angle(i % n);
      const r = (R * ring) / 4;
      const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  // 轴线
  for (let i = 0; i < n; i++) {
    const a = angle(i);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + R * Math.cos(a), cy + R * Math.sin(a));
    ctx.stroke();
  }
  // 数据区域
  ctx.beginPath();
  for (let i = 0; i <= n; i++) {
    const a = angle(i % n);
    const r = R * Math.min(1, (values[i % n] || 0) / 100);
    const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(11, 167, 123, 0.18)';
  ctx.fill();
  ctx.strokeStyle = color || '#0BA77B';
  ctx.lineWidth = 2;
  ctx.stroke();

  // 维度标签
  ctx.fillStyle = '#4F5B5E';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'center';
  indicators.forEach((lb, i) => {
    const a = angle(i);
    const x = cx + (R + 18) * Math.cos(a);
    const y = cy + (R + 16) * Math.sin(a);
    const text = lb.length > 7 ? lb.slice(0, 7) + '…' : lb;
    ctx.fillText(text, x, y + 3);
  });
}

/** 环形受损率进度 */
function drawRing(canvas, size, percent, color) {
  const ctx = setupCanvas(canvas, size, size);
  const cx = size / 2, cy = size / 2, R = size / 2 - 8, lw = 9;
  ctx.clearRect(0, 0, size, size);
  ctx.lineCap = 'round';
  // 底环
  ctx.strokeStyle = '#E9EFF0';
  ctx.lineWidth = lw;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.stroke();
  // 进度环
  const p = Math.max(0, Math.min(100, percent)) / 100;
  const grad = ctx.createLinearGradient(0, 0, size, size);
  grad.addColorStop(0, '#19C995');
  grad.addColorStop(1, color || '#FF984F');
  ctx.strokeStyle = grad;
  ctx.beginPath();
  ctx.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * p);
  ctx.stroke();
}

module.exports = { drawLineChart, drawBarChart, drawRadar, drawRing };
