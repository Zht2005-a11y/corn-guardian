import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/bigScreen',
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

export default router
