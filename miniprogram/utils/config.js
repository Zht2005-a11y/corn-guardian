/**
 * 全局 API 地址配置
 *
 * 【必须带 /api 前缀】服务器 nginx 的 /api/ 是反代到 FastAPI 的入口
 * （/api/screen/xxx -> 后端 /screen/xxx）。不带 /api 时请求会被 nginx 的
 * SPA 兜底规则返回 index.html（HTTP 200 但内容是 HTML），小程序拿不到
 * JSON，表现就是「接口全部连不上」。
 *
 * 【生产环境说明（微信小程序硬性规定）】：
 * 1. 小程序正式版、未开调试的体验版严禁使用 HTTP，必须 HTTPS。
 * 2. 微信后台「开发管理 -> 开发设置 -> 服务器域名」不支持纯 IP，必须是 ICP 备案域名，
 *    例如：https://api.yourdomain.com/api
 *
 * 【体验版/真机调试临时应急】：
 * 手机打开小程序 -> 右上角「…」->「开发调试」(vConsole) -> 杀掉重进。
 * 开调试后微信会放行 HTTP 与 IP 请求。
 *
 * 【本地后端】run_backend.bat 起的 FastAPI(8010) 没有 /api 前缀，
 * 真机调试改本地时用 http://192.168.1.100:8010
 */
const BASE_URL = 'http://101.34.247.39:8082/api';

module.exports = { BASE_URL };
