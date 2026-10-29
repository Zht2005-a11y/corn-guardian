import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/bigScreen',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { public: true, title: '登录 · 玉米智诊' },
    },
    {
      path: '/bigScreen',
      name: 'bigScreen',
      component: () => import('@/views/bigScreen/Layout.vue'),
    },
    {
      path: '/tanee',
      name: 'taneeFigma',
      component: () => import('@/views/bigScreen/TaneeFigmaView.vue'),
    }
  ]
})

/**
 * 全局登录守卫：除 meta.public 的页面外都要求已登录，
 * 未登录跳登录页并带上 redirect，登录成功后再回来。
 */
router.beforeEach((to) => {
  const auth = useAuthStore()
  const loggedIn = auth.isLoggedIn

  if (to.meta.public) {
    // 已登录还去登录页，直接回大屏
    if (to.path === '/login' && loggedIn) return { path: '/bigScreen' }
    return true
  }

  if (!loggedIn) {
    return {
      path: '/login',
      query: to.fullPath && to.fullPath !== '/' ? { redirect: to.fullPath } : {},
    }
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta?.title || '玉米叶部病斑多尺度自适应感知与飞防决策系统'
})

export default router
