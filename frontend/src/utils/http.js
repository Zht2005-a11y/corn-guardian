/**
 * 全局 axios 装配：统一带令牌 + 统一处理 401。
 *
 * 大屏里各处都是直接 `import axios from 'axios'` 用的全局实例，
 * 所以这里给全局实例装拦截器，不必逐个改调用点。
 */
import axios from 'axios'

const TOKEN_KEY = 'corn.auth.token'
const USER_KEY = 'corn.auth.user'
const EXP_KEY = 'corn.auth.expiresAt'

let redirecting = false

export function authToken() {
  const token = localStorage.getItem(TOKEN_KEY) || ''
  const exp = Number(localStorage.getItem(EXP_KEY) || 0)
  if (token && exp && exp * 1000 <= Date.now()) return ''
  return token
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(EXP_KEY)
}

/**
 * 跳登录页。用 hash 直接跳而不是 router.push，避免 utils → router → store → utils 的循环依赖；
 * 整页刷新也让内存里的大屏状态（图片、会话、计时器）彻底清干净。
 */
export function redirectToLogin(reason = '') {
  if (redirecting) return
  const current = window.location.hash.replace(/^#/, '') || '/bigScreen'
  if (current.startsWith('/login')) return
  redirecting = true
  clearSession()
  const query = new URLSearchParams()
  if (current && current !== '/') query.set('redirect', current)
  if (reason) query.set('reason', reason)
  window.location.hash = `#/login${query.toString() ? `?${query}` : ''}`
  // 兜底：万一应用已卸载（比如刷新时），下一次请求还能正常处理
  window.setTimeout(() => {
    redirecting = false
  }, 1500)
}

axios.interceptors.request.use((config) => {
  const token = authToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const path = error?.config?.url || ''
    // 登录接口自己会提示「账号或密码不正确」，不要误伤成"登录已过期"
    if (status === 401 && !path.includes('/auth/login') && !path.includes('/auth/register')) {
      redirectToLogin('登录状态已失效，请重新登录')
    }
    return Promise.reject(error)
  },
)

export default axios
