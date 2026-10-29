/**
 * 后端 API 封装
 * 后端：model/corn_disease_system_20261021（FastAPI，默认 127.0.0.1:8010）
 * 所有接口真实对接，后端未启动时抛出带提示的错误。
 */
const { BASE_URL } = require('./config');

function request(path, method, data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method: method || 'GET',
      data: data,
      timeout: 30000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300 && res.data && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          const detail = (res.data && (res.data.detail || res.data.message)) || ('HTTP ' + res.statusCode);
          reject(new Error(detail));
        }
      },
      fail(err) {
        reject(new Error('无法连接后端服务(' + BASE_URL + ')，请确认已运行 run_backend.bat：' + (err.errMsg || '')));
      }
    });
  });
}

// 文件转 base64（data-url 形式，后端可直接接受）
function fileToDataUrl(filePath) {
  return new Promise((resolve, reject) => {
    const fs = wx.getFileSystemManager();
    fs.readFile({
      filePath,
      encoding: 'base64',
      success(res) {
        resolve('data:image/jpeg;base64,' + res.data);
      },
      fail(e) {
        reject(new Error('读取图片失败: ' + (e.errMsg || '')));
      }
    });
  });
}

/** 压缩图片到 <=1080px 再转 base64，避免上传体积过大 */
function compressToDataUrl(filePath) {
  return new Promise((resolve) => {
    wx.getImageInfo({
      src: filePath,
      success(info) {
        const maxSide = 1080;
        const scale = Math.min(1, maxSide / Math.max(info.width, info.height));
        const w = Math.round(info.width * scale);
        const h = Math.round(info.height * scale);
        const off = wx.createOffscreenCanvas({ type: '2d', width: w, height: h });
        const ctx = off.getContext('2d');
        const img = off.createImage();
        img.onload = () => {
          ctx.drawImage(img, 0, 0, w, h);
          const data = off.toDataURL('image/jpeg', 0.85);
          resolve(data);
        };
        img.onerror = () => resolve(fileToDataUrl(filePath));
        img.src = filePath;
      },
      fail() {
        resolve(fileToDataUrl(filePath));
      }
    });
  });
}

const api = {
  /** 四类典型样本（含真实数据集 base64 图） */
  getSamples: () => request('/screen/samples'),

  /** 综合诊断：病害/置信度/Grad-CAM/病斑框/受损率/处方 */
  predict: (imageBase64, filename, model) =>
    request('/screen/predict', 'POST', {
      image_base64: imageBase64,
      filename: filename || 'upload.jpg',
      model: model || 'resnet50_cbam'
    }),

  /** 批量巡田识别 */
  predictBatch: (images, acreage) =>
    request('/screen/predict/batch', 'POST', {
      images: images,
      acreage_per_image: acreage || 1
    }),

  /** 诊断历史 */
  historyList: (limit, offset) => request('/screen/history?limit=' + (limit || 20) + '&offset=' + (offset || 0)),
  historyDetail: (id) => request('/screen/history/' + id),
  historyDelete: (id) => request('/screen/history/' + id, 'DELETE'),

  /** 遥测（微气候时序/病害分布/抗逆雷达） */
  telemetry: () => request('/screen/telemetry'),

  /** 病害图鉴知识库 */
  knowledge: () => request('/screen/knowledge'),

  /** 历史会话 */
  sessionList: (limit) => request('/screen/sessions?limit=' + (limit || 30)),
  sessionDetail: (sid) => request('/screen/sessions/' + sid),
  sessionDelete: (sid) => request('/screen/sessions/' + sid, 'DELETE'),

  compressToDataUrl,
  fileToDataUrl,
  BASE_URL
};

module.exports = api;
