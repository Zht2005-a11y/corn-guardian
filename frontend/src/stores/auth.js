import { defineStore } from 'pinia'
import axios from 'axios'

const TOKEN_KEY = 'corn.auth.token'
const USER_KEY = 'corn.auth.user'
const EXP_KEY = 'corn.auth.expiresAt'

function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readUser(),
    // 服务端给的绝对过期时间（秒），只用于前端预判，真正校验在后端
    expiresAt: Number(localStorage.getItem(EXP_KEY) || 0),
    loading: false,
    lastError: '',
  }),

  getters: {
    isLoggedIn: (state) => {
      if (!state.token) return false
      if (state.expiresAt && state.expiresAt * 1000 <= Date.now()) return false
      return true
    },
    displayName: (state) => state.user?.display_name || state.user?.username || '未登录',
    roleLabel: (state) => state.user?.role_label || '',
    /** 头像里显示的 1-2 个字：中文取首字，英文取首字母 */
    initials: (state) => {
      const name = state.user?.display_name || state.user?.username || '?'
      const first = name.trim()[0] || '?'
      return /[a-zA-Z]/.test(first) ? first.toUpperCase() : first
    },
  },

  actions: {
    persist() {
      if (this.token) localStorage.setItem(TOKEN_KEY, this.token)
      else localStorage.removeItem(TOKEN_KEY)

      if (this.user) localStorage.setItem(USER_KEY, JSON.stringify(this.user))
      else localStorage.removeItem(USER_KEY)

      if (this.expiresAt) localStorage.setItem(EXP_KEY, String(this.expiresAt))
      else localStorage.removeItem(EXP_KEY)
    },

    clear() {
      this.token = ''
      this.user = null
      this.expiresAt = 0
      this.persist()
    },

    async login({ username, password, remember = false }) {
      this.loading = true
      this.lastError = ''
      try {
        const { data } = await axios.post('/api/auth/login', { username, password, remember })
        const payload = data?.data || {}
        this.token = payload.token || ''
        this.user = payload.user || null
        this.expiresAt = payload.expires_at || 0
        this.persist()
        return this.user
      } catch (err) {
        this.lastError = err?.response?.data?.message || '登录失败，请检查网络后重试'
        throw new Error(this.lastError)
      } finally {
        this.loading = false
      }
    },

    async register({ username, password, display_name }) {
      this.loading = true
      this.lastError = ''
      try {
        const { data } = await axios.post('/api/auth/register', { username, password, display_name })
        return data?.data?.user || null
      } catch (err) {
        this.lastError = err?.response?.data?.message || '注册失败，请稍后重试'
        throw new Error(this.lastError)
      } finally {
        this.loading = false
      }
    },

    /** 用本地令牌换一次最新的用户信息；令牌失效时由调用方处理 401 */
    async fetchMe() {
      if (!this.token) return null
      try {
        const { data } = await axios.get('/api/auth/me')
        this.user = data?.data?.user || this.user
        this.persist()
        return this.user
      } catch {
        return null
      }
    },

    async logout() {
      try {
        if (this.token) await axios.post('/api/auth/logout')
      } catch {
        // 令牌可能已过期，忽略；本地清理照做
      } finally {
        this.clear()
      }
    },
  },
})
