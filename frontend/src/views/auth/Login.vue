<template>
  <div class="auth-page">
    <div class="auth-shell">
      <!-- ═══════════ 左：品牌 + 表单 ═══════════ -->
      <section class="auth-panel">
        <header class="auth-brand">
          <div class="brand-mark">
            <img src="/tanee/svg/dashboard/icon-9.svg" alt="玉米智诊" />
          </div>
          <div class="brand-text">
            <strong>玉米智诊</strong>
            <span>CORN GUARDIAN</span>
          </div>
        </header>

        <div class="auth-card" :class="{ shaking: shaking }">
          <transition name="auth-swap" mode="out-in">
            <!-- ─────── 登录 ─────── -->
            <div v-if="mode === 'login'" key="login" class="auth-view">
              <h1 class="auth-title">欢迎回来</h1>
              <p class="auth-subtitle">安全访问你的田块数据、设备与诊断洞察。</p>

              <transition name="notice-fade">
                <div v-if="notice.text" class="auth-notice" :class="notice.type">
                  <svg v-if="notice.type === 'error'" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">
                    <circle cx="8" cy="8" r="6.2" />
                    <path d="M8 5v3.6M8 11h.01" stroke-linecap="round" />
                  </svg>
                  <svg v-else viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">
                    <circle cx="8" cy="8" r="6.2" />
                    <path d="M5.4 8.2L7.2 10L10.7 6.4" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                  <span>{{ notice.text }}</span>
                </div>
              </transition>

              <form class="auth-form" @submit.prevent="submitLogin">
                <div class="field">
                  <label for="login-user">账号</label>
                  <div class="field-control">
                    <input
                      id="login-user"
                      ref="userInput"
                      v-model.trim="form.username"
                      type="text"
                      autocomplete="username"
                      placeholder="请输入账号"
                      :disabled="loading"
                    />
                  </div>
                </div>

                <div class="field">
                  <label for="login-pwd">密码</label>
                  <div class="field-control">
                    <input
                      id="login-pwd"
                      v-model="form.password"
                      class="with-suffix"
                      :type="showPassword ? 'text' : 'password'"
                      autocomplete="current-password"
                      placeholder="请输入密码"
                      :disabled="loading"
                    />
                    <button type="button" class="eye-btn" :title="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword">
                      <svg v-if="!showPassword" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M1.8 10S4.7 4.8 10 4.8 18.2 10 18.2 10 15.3 15.2 10 15.2 1.8 10 1.8 10Z" stroke-linejoin="round" />
                        <circle cx="10" cy="10" r="2.5" />
                      </svg>
                      <svg v-else viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M2.6 6.4C2 7.3 1.8 8.1 1.8 8.1s2.9 5.2 8.2 5.2c1 0 1.9-.2 2.7-.5M7.1 4.9c.9-.2 1.9-.4 2.9-.4 5.3 0 8.2 5.2 8.2 5.2s-.5.9-1.5 2" stroke-linecap="round" />
                        <path d="M8.2 8.2a2.5 2.5 0 003.5 3.5M3 3l14 14" stroke-linecap="round" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div class="auth-row">
                  <label class="remember">
                    <input v-model="remember" type="checkbox" />
                    <span class="remember-box">
                      <svg viewBox="0 0 12 9" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M1 4.6L4.2 7.6L11 1.4" />
                      </svg>
                    </span>
                    <span class="remember-text">记住我</span>
                  </label>
                  <button type="button" class="text-link" @click="showForgotTip">忘记密码？</button>
                </div>

                <button class="auth-submit" type="submit" :disabled="loading || !canSubmitLogin">
                  <span v-if="!loading">登 录</span>
                  <span v-else class="submit-loading"><i class="spinner" />正在验证…</span>
                </button>
              </form>

              <div v-if="demoAccounts.length" class="demo-hint">
                <span class="demo-label">演示账号</span>
                <button
                  v-for="d in demoAccounts"
                  :key="d.username"
                  type="button"
                  class="demo-chip"
                  @click="fillDemo(d)"
                >
                  {{ d.username }} / {{ d.password }}
                  <em>{{ d.role_label }}</em>
                </button>
              </div>

              <p v-if="allowRegister" class="auth-foot">
                还没有账号？
                <button type="button" class="text-link strong" @click="switchMode('register')">立即注册</button>
              </p>
            </div>

            <!-- ─────── 注册 ─────── -->
            <div v-else key="register" class="auth-view">
              <h1 class="auth-title">创建账号</h1>
              <p class="auth-subtitle">注册后即可进入大屏查看诊断结果与飞防建议。</p>

              <transition name="notice-fade">
                <div v-if="notice.text" class="auth-notice" :class="notice.type">
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">
                    <circle cx="8" cy="8" r="6.2" />
                    <path d="M8 5v3.6M8 11h.01" stroke-linecap="round" />
                  </svg>
                  <span>{{ notice.text }}</span>
                </div>
              </transition>

              <form class="auth-form" @submit.prevent="submitRegister">
                <div class="field">
                  <label for="reg-user">账号</label>
                  <div class="field-control">
                    <input id="reg-user" v-model.trim="form.username" type="text" autocomplete="username" placeholder="字母开头，3-32 位" :disabled="loading" />
                  </div>
                </div>

                <div class="field">
                  <label for="reg-name">显示名<span class="optional">选填</span></label>
                  <div class="field-control">
                    <input id="reg-name" v-model.trim="form.display_name" type="text" autocomplete="nickname" placeholder="例如：李工 · 巡田员" :disabled="loading" />
                  </div>
                </div>

                <div class="field">
                  <label for="reg-pwd">密码</label>
                  <div class="field-control">
                    <input
                      id="reg-pwd"
                      v-model="form.password"
                      class="with-suffix"
                      :type="showPassword ? 'text' : 'password'"
                      autocomplete="new-password"
                      placeholder="至少 8 位，含字母和数字"
                      :disabled="loading"
                    />
                    <button type="button" class="eye-btn" :title="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword">
                      <svg v-if="!showPassword" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M1.8 10S4.7 4.8 10 4.8 18.2 10 18.2 10 15.3 15.2 10 15.2 1.8 10 1.8 10Z" stroke-linejoin="round" />
                        <circle cx="10" cy="10" r="2.5" />
                      </svg>
                      <svg v-else viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M2.6 6.4C2 7.3 1.8 8.1 1.8 8.1s2.9 5.2 8.2 5.2c1 0 1.9-.2 2.7-.5M7.1 4.9c.9-.2 1.9-.4 2.9-.4 5.3 0 8.2 5.2 8.2 5.2s-.5.9-1.5 2" stroke-linecap="round" />
                        <path d="M8.2 8.2a2.5 2.5 0 003.5 3.5M3 3l14 14" stroke-linecap="round" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div class="field">
                  <label for="reg-confirm">确认密码</label>
                  <div class="field-control">
                    <input
                      id="reg-confirm"
                      v-model="form.confirm"
                      :type="showPassword ? 'text' : 'password'"
                      autocomplete="new-password"
                      placeholder="再次输入密码"
                      :disabled="loading"
                    />
                  </div>
                </div>

                <button class="auth-submit" type="submit" :disabled="loading">
                  <span v-if="!loading">注册并进入</span>
                  <span v-else class="submit-loading"><i class="spinner" />正在创建…</span>
                </button>
              </form>

              <p class="auth-foot">
                已有账号？
                <button type="button" class="text-link strong" @click="switchMode('login')">返回登录</button>
              </p>
            </div>
          </transition>
        </div>

        <footer class="auth-copyright">
          <span>© {{ year }} 玉米叶部病斑多尺度自适应感知与飞防决策系统</span>
          <span class="dot-sep">·</span>
          <span>v1.0</span>
        </footer>
      </section>

      <!-- ═══════════ 右：视觉 ═══════════ -->
      <aside class="auth-visual">
        <div class="visual-grid" aria-hidden="true"></div>
        <svg class="visual-art" viewBox="0 0 520 720" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
          <defs>
            <linearGradient id="leafA" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#7fe0a6" stop-opacity="0.92" />
              <stop offset="100%" stop-color="#2e9055" stop-opacity="0.45" />
            </linearGradient>
            <linearGradient id="leafB" x1="1" y1="1" x2="0" y2="0">
              <stop offset="0%" stop-color="#a9f0c6" stop-opacity="0.8" />
              <stop offset="100%" stop-color="#1f6b45" stop-opacity="0.35" />
            </linearGradient>
            <radialGradient id="glow" cx="50%" cy="62%" r="55%">
              <stop offset="0%" stop-color="#b6ffd2" stop-opacity="0.35" />
              <stop offset="100%" stop-color="#b6ffd2" stop-opacity="0" />
            </radialGradient>
          </defs>

          <circle cx="260" cy="400" r="260" fill="url(#glow)" />
          <g stroke="#ffffff" stroke-opacity="0.16" fill="none">
            <circle cx="260" cy="400" r="120" stroke-dasharray="3 7" />
            <circle cx="260" cy="400" r="196" stroke-dasharray="2 9" />
            <circle cx="260" cy="400" r="272" stroke-dasharray="1 10" />
            <path d="M260 90V640M40 400H480" stroke-opacity="0.08" />
          </g>

          <!-- 玉米植株 -->
          <g transform="translate(2,-18) scale(0.94)">
            <path d="M262 640C252 520 250 420 258 300C284 400 290 512 274 640Z" fill="url(#leafA)" />
            <path d="M258 618C214 566 178 522 132 492C186 486 232 524 260 574Z" fill="url(#leafB)" />
            <path d="M268 596C312 540 352 498 400 470C346 462 298 502 266 550Z" fill="url(#leafA)" />
            <path d="M256 566C204 528 160 508 108 500C158 468 214 490 260 528Z" fill="url(#leafB)" />
            <path d="M270 540C322 500 368 478 424 472C374 440 314 464 266 504Z" fill="url(#leafB)" />
            <path d="M262 512C214 466 176 430 138 392C192 400 236 434 264 474Z" fill="url(#leafA)" />
            <path d="M266 486C314 440 356 408 402 380C344 380 300 414 262 452Z" fill="url(#leafA)" />
            <!-- 叶脉 -->
            <g stroke="#0f3f28" stroke-opacity="0.35" stroke-width="1.4" fill="none">
              <path d="M262 622V322" />
              <path d="M260 578C224 552 192 528 158 508" />
              <path d="M266 552C302 518 336 490 388 474" />
              <path d="M258 522C218 496 182 476 132 494" />
              <path d="M268 508C308 474 352 452 414 476" />
            </g>
          </g>

          <!-- 感知节点 -->
          <g fill="#d7ffe8">
            <circle cx="150" cy="460" r="3.4" opacity="0.9" />
            <circle cx="383" cy="427" r="3.4" opacity="0.9" />
            <circle cx="126" cy="452" r="2.6" opacity="0.7" />
            <circle cx="404" cy="426" r="2.6" opacity="0.7" />
            <circle cx="248" cy="264" r="4" opacity="0.95" />
          </g>
          <g stroke="#d7ffe8" stroke-opacity="0.45" stroke-width="1" fill="none">
            <path d="M150 460L248 264L383 427" stroke-dasharray="4 6" />
          </g>
        </svg>

        <div class="visual-fade" aria-hidden="true"></div>
        <div class="visual-scan" aria-hidden="true"></div>

        <div class="visual-caption">
          <span class="visual-eyebrow">FIELD INTELLIGENCE</span>
          <h2>让农业更智能<br />让丰收更简单</h2>
          <p>多尺度感知每一片叶子，把病害诊断与飞防决策送到田间。</p>
          <div class="visual-dots" aria-hidden="true"><i class="on"></i><i></i><i></i></div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const mode = ref('login')
const form = reactive({ username: '', password: '', display_name: '', confirm: '' })
const remember = ref(false)
const showPassword = ref(false)
const shaking = ref(false)
const userInput = ref(null)
const notice = reactive({ type: 'error', text: '' })
const demoAccounts = ref([
  { username: 'admin', password: 'corn@2026', role_label: '系统管理员' },
])
const allowRegister = ref(true)
const year = new Date().getFullYear()

const loading = computed(() => auth.loading)
const canSubmitLogin = computed(() => Boolean(form.username && form.password))

function flash(text, type = 'error') {
  notice.type = type
  notice.text = text
  shaking.value = true
  window.setTimeout(() => (shaking.value = false), 420)
}

function clearNotice() {
  notice.text = ''
}

function switchMode(next) {
  mode.value = next
  clearNotice()
  showPassword.value = false
  form.confirm = ''
  window.setTimeout(() => userInput.value?.focus(), 60)
}

function fillDemo(account) {
  mode.value = 'login'
  form.username = account.username
  form.password = account.password
  clearNotice()
}

function showForgotTip() {
  flash('演示环境请使用下方演示账号登录，或联系系统管理员重置密码。', 'info')
}

function redirectTarget() {
  const target = route.query.redirect
  if (typeof target === 'string' && target.startsWith('/') && !target.startsWith('/login')) return target
  return '/bigScreen'
}

async function submitLogin() {
  clearNotice()
  if (!form.username || !form.password) {
    flash('请输入账号和密码')
    return
  }
  try {
    await auth.login({ username: form.username, password: form.password, remember: remember.value })
    router.replace(redirectTarget())
  } catch (err) {
    flash(err.message || '登录失败，请稍后重试')
  }
}

async function submitRegister() {
  clearNotice()
  if (!/^[A-Za-z][A-Za-z0-9_.-]{2,31}$/.test(form.username)) {
    flash('账号需以字母开头，长度 3-32 位，仅支持字母、数字、下划线')
    return
  }
  if (form.password.length < 8 || !/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
    flash('密码至少 8 位，且需同时包含字母和数字')
    return
  }
  if (form.password !== form.confirm) {
    flash('两次输入的密码不一致')
    return
  }
  try {
    await auth.register({
      username: form.username,
      password: form.password,
      display_name: form.display_name,
    })
    // 注册成功直接登录，少一次输入
    await auth.login({ username: form.username, password: form.password, remember: remember.value })
    router.replace(redirectTarget())
  } catch (err) {
    flash(err.message || '注册失败，请稍后重试')
  }
}

onMounted(async () => {
  if (route.query.reason) notice.text = String(route.query.reason)
  userInput.value?.focus()
  // 登录页配置（演示账号、注册开关）来自后端，后端不可达时用本地兜底文案
  try {
    const { data } = await axios.get('/api/auth/config')
    const cfg = data?.data || {}
    if (Array.isArray(cfg.demo_accounts) && cfg.demo_accounts.length) demoAccounts.value = cfg.demo_accounts
    if (typeof cfg.allow_register === 'boolean') allowRegister.value = cfg.allow_register
  } catch {
    // 后端未启动：保留本地演示账号提示，用户点登录时会有明确报错
  }
})
</script>

<style scoped lang="scss">
.auth-page {
  min-height: 100vh;
  background: #f4f4f4;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px 32px;
  font-family: var(--font-family);
  color: #333333;
}

.auth-shell {
  width: 100%;
  max-width: 1140px;
  display: grid;
  grid-template-columns: 452px minmax(0, 1fr);
  gap: 64px;
  align-items: stretch;
}

/* ═══════════ 左侧 ═══════════ */
.auth-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 26px;
  animation: panel-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 12px;

  .brand-mark {
    width: 42px;
    height: 42px;
    border-radius: 9999px;
    background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 6px 16px rgba(53, 197, 110, 0.32);

    img {
      width: 19px;
      height: 19px;
    }
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    line-height: 1.15;

    strong {
      font-size: 17px;
      font-weight: 700;
      color: #181b25;
      letter-spacing: -0.01em;
    }

    span {
      font-size: 10px;
      letter-spacing: 0.16em;
      color: #a4a4a4;
      font-weight: 600;
      margin-top: 2px;
    }
  }
}

.auth-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 30px 34px 32px;
  box-shadow: 0 12px 32px rgba(24, 27, 37, 0.06), 0 2px 6px rgba(24, 27, 37, 0.03);
  border: 1px solid rgba(24, 27, 37, 0.04);

  &.shaking {
    animation: card-shake 0.42s cubic-bezier(0.36, 0.07, 0.19, 0.97);
  }
}

.auth-view {
  display: flex;
  flex-direction: column;
}

.auth-title {
  font-size: 26px;
  line-height: 1.25;
  font-weight: 700;
  color: #181b25;
  text-align: center;
  letter-spacing: -0.02em;
}

.auth-subtitle {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #8d8d8d;
  text-align: center;
}

.auth-notice {
  margin-top: 16px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  font-size: 12.5px;
  line-height: 1.5;

  svg {
    width: 15px;
    height: 15px;
    flex-shrink: 0;
    margin-top: 1px;
  }

  &.error {
    background: #fef3f2;
    border: 1px solid #fbdad7;
    color: #c5301f;
  }

  &.info {
    background: #f2f8ff;
    border: 1px solid #dbe9fb;
    color: #2c5f9e;
  }
}

.auth-form {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;

  label {
    font-size: 13px;
    font-weight: 600;
    color: #333333;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .optional {
    font-size: 11px;
    font-weight: 400;
    color: #b5b5b5;
  }
}

.field-control {
  position: relative;
  display: flex;
  align-items: center;

  input {
    width: 100%;
    height: 44px;
    padding: 0 14px;
    border-radius: 8px;
    border: 1px solid #ececec;
    background: #fafafa;
    font-family: inherit;
    font-size: 13.5px;
    color: #181b25;
    outline: none;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;

    &::placeholder {
      color: #b8b8b8;
    }

    &:hover:not(:disabled) {
      border-color: #dcdcdc;
    }

    &:focus {
      background: #ffffff;
      border-color: #35c56e;
      box-shadow: 0 0 0 3px rgba(53, 197, 110, 0.14);
    }

    &:disabled {
      color: #a4a4a4;
      cursor: not-allowed;
    }
  }

  /* 带右侧眼睛按钮的输入框留出点击区 */
  input.with-suffix {
    padding-right: 42px;
  }

  .eye-btn {
    position: absolute;
    right: 8px;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    border-radius: 6px;
    color: #a4a4a4;
    cursor: pointer;
    transition: color 0.15s ease, background 0.15s ease;

    svg {
      width: 17px;
      height: 17px;
    }

    &:hover {
      color: #525866;
      background: #f0f0f0;
    }
  }
}

.auth-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: -2px;
}

.remember {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;

  input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
  }

  .remember-box {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1.5px solid #d5d5d5;
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.16s ease;

    svg {
      width: 10px;
      height: 8px;
      color: #ffffff;
      opacity: 0;
      transform: scale(0.7);
      transition: all 0.16s ease;
    }
  }

  input:checked + .remember-box {
    background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
    border-color: #2e9055;

    svg {
      opacity: 1;
      transform: scale(1);
    }
  }

  input:focus-visible + .remember-box {
    box-shadow: 0 0 0 3px rgba(53, 197, 110, 0.18);
  }

  .remember-text {
    font-size: 12.5px;
    color: #525866;
  }
}

.text-link {
  border: none;
  background: transparent;
  padding: 0;
  font-family: inherit;
  font-size: 12.5px;
  color: #2e9055;
  cursor: pointer;
  transition: color 0.15s ease;

  &:hover {
    color: #35c56e;
    text-decoration: underline;
  }

  &.strong {
    font-weight: 600;
  }
}

.auth-submit {
  margin-top: 6px;
  height: 46px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
  color: #ffffff;
  font-family: inherit;
  font-size: 14.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(46, 144, 85, 0.24);
  transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.16s ease;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(46, 144, 85, 0.3);
    filter: brightness(1.03);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 6px 14px rgba(46, 144, 85, 0.24);
  }

  &:disabled {
    background: #dcdcdc;
    color: #ffffff;
    box-shadow: none;
    cursor: not-allowed;
  }

  .submit-loading {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .spinner {
    width: 14px;
    height: 14px;
    border-radius: 999px;
    border: 2px solid rgba(255, 255, 255, 0.45);
    border-top-color: #ffffff;
    animation: spin 0.7s linear infinite;
  }
}

.demo-hint {
  margin-top: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f0faf4;
  border: 1px dashed #cdead9;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;

  .demo-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #2e9055;
  }

  .demo-chip {
    border: 1px solid #d4ecdf;
    background: #ffffff;
    border-radius: 6px;
    padding: 5px 9px;
    font-family: inherit;
    font-size: 11.5px;
    color: #525866;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    cursor: pointer;
    transition: all 0.15s ease;

    em {
      font-style: normal;
      color: #a4a4a4;
      flex-shrink: 0;
    }

    &:hover {
      border-color: #35c56e;
      color: #2e9055;
      box-shadow: 0 2px 8px rgba(46, 144, 85, 0.12);
    }
  }
}

.auth-foot {
  margin-top: 18px;
  text-align: center;
  font-size: 12.5px;
  color: #a4a4a4;
}

.auth-copyright {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11px;
  color: #b8b8b8;
  letter-spacing: 0.01em;

  .dot-sep {
    color: #d5d5d5;
  }
}

/* ═══════════ 右侧视觉 ═══════════ */
.auth-visual {
  position: relative;
  min-height: 620px;
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(160deg, #2e9055 0%, #1f6b45 48%, #123a26 100%);
  box-shadow: 0 20px 50px rgba(18, 58, 38, 0.24);
  animation: visual-in 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;

  .visual-grid {
    position: absolute;
    inset: 0;
    background-image: linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
    background-size: 46px 46px;
    mask-image: radial-gradient(circle at 50% 60%, #000 30%, transparent 78%);
    opacity: 0.75;
  }

  .visual-art {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }

  /* 底部渐隐：让文案压在叶丛上依然清晰，同时收住被画框裁到叶尖的硬边 */
  .visual-fade {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(120% 80% at 50% 8%, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0) 55%),
      linear-gradient(180deg, rgba(9, 38, 24, 0) 38%, rgba(9, 38, 24, 0.42) 68%, rgba(9, 38, 24, 0.84) 100%);
    pointer-events: none;
  }

  .visual-scan {
    position: absolute;
    left: 0;
    right: 0;
    height: 120px;
    top: -140px;
    background: linear-gradient(180deg, rgba(182, 255, 210, 0) 0%, rgba(182, 255, 210, 0.16) 60%, rgba(182, 255, 210, 0) 100%);
    animation: scan 5.2s cubic-bezier(0.45, 0, 0.55, 1) infinite;
  }

  .visual-caption {
    position: absolute;
    left: 44px;
    right: 44px;
    bottom: 44px;
    color: #ffffff;

    .visual-eyebrow {
      display: inline-block;
      font-size: 10.5px;
      letter-spacing: 0.22em;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.66);
      margin-bottom: 14px;
    }

    h2 {
      font-size: 34px;
      line-height: 1.28;
      font-weight: 700;
      letter-spacing: -0.02em;
      text-shadow: 0 4px 24px rgba(0, 0, 0, 0.18);
    }

    p {
      margin-top: 12px;
      font-size: 13px;
      line-height: 1.7;
      color: rgba(255, 255, 255, 0.78);
      max-width: 372px;
    }

    .visual-dots {
      margin-top: 22px;
      display: flex;
      gap: 7px;

      i {
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.36);
        transition: all 0.2s ease;

        &.on {
          width: 22px;
          background: #ffffff;
        }
      }
    }
  }
}

/* ═══════════ 动画 ═══════════ */
@keyframes panel-in {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes visual-in {
  from {
    opacity: 0;
    transform: scale(0.985);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes card-shake {
  10%,
  90% {
    transform: translateX(-2px);
  }
  20%,
  80% {
    transform: translateX(3px);
  }
  30%,
  50%,
  70% {
    transform: translateX(-4px);
  }
  40%,
  60% {
    transform: translateX(4px);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes scan {
  0% {
    top: -140px;
    opacity: 0;
  }
  12% {
    opacity: 1;
  }
  88% {
    opacity: 1;
  }
  100% {
    top: 100%;
    opacity: 0;
  }
}

.auth-swap-enter-active,
.auth-swap-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.auth-swap-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.auth-swap-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.notice-fade-enter-active,
.notice-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.notice-fade-enter-from,
.notice-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ═══════════ 响应式 ═══════════ */
@media (max-width: 1080px) {
  .auth-shell {
    grid-template-columns: 440px;
    justify-content: center;
    gap: 0;
  }

  .auth-visual {
    display: none;
  }
}

@media (max-width: 540px) {
  .auth-page {
    padding: 20px 16px;
    align-items: flex-start;
  }

  .auth-card {
    padding: 24px 20px 26px;
  }

  .auth-title {
    font-size: 23px;
  }

  .auth-copyright {
    flex-direction: column;
    gap: 2px;
  }
}

@media (max-height: 780px) and (min-width: 1081px) {
  .auth-visual {
    min-height: 560px;
  }

  .auth-card {
    padding: 24px 30px 26px;
  }

  .auth-form {
    gap: 12px;
  }

  .field-control input {
    height: 42px;
  }
}
</style>
