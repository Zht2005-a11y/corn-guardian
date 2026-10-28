<template>
  <div class="dji-shop-backdrop" @click.self="$emit('close')">
    <div class="dji-shop-card" role="dialog" aria-label="DJI 商城">

      <!-- ════════ 1. 顶部导航栏（真实站内切换） ════════ -->
      <header class="ds-nav">
        <div class="ds-nav-left">
          <img src="/dji/dji-logo.png" alt="DJI" class="ds-logo" @click="switchTab('drones')" @error="imgFail($event, 60, 24)"/>
        </div>
        <nav class="ds-nav-mid">
          <a v-for="n in navItems" :key="n.id" href="javascript:void(0)"
             class="ds-nav-link" :class="{ active: activeTab === n.id }"
             @click="switchTab(n.id)">{{ n.label }}</a>
        </nav>
        <div class="ds-nav-right">
          <div class="ds-search-box" :class="{ open: searchOpen }">
            <input
              ref="searchInput"
              v-if="searchOpen"
              v-model="searchText"
              class="ds-search-input"
              placeholder="搜索商品…"
              @keyup.enter="doSearch"
            />
            <button class="ds-icon-btn" @click="toggleSearch" title="搜索">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <circle cx="11" cy="11" r="7"/><line x1="16.5" y1="16.5" x2="21" y2="21"/>
              </svg>
            </button>
          </div>
          <button class="ds-icon-btn ds-cart-btn" title="购物车（本地演示）">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="9" cy="20" r="1.6"/><circle cx="18" cy="20" r="1.6"/>
              <path d="M2 3h3l2.6 12.4a1.5 1.5 0 0 0 1.5 1.1h8.6a1.5 1.5 0 0 0 1.5-1.2L21 7H6"/>
            </svg>
            <span class="ds-cart-badge">{{ cartCount }}</span>
          </button>
          <button class="ds-icon-btn ds-close-btn" @click="$emit('close')" title="关闭">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="5" y1="5" x2="19" y2="19"/><line x1="19" y1="5" x2="5" y2="19"/>
            </svg>
          </button>
        </div>
      </header>

      <!-- ════════ 可滚动主体（按导航切换视图） ════════ -->
      <div class="ds-scroll" ref="scrollEl">

        <!-- ═════ 首页 ═════ -->
        <template v-if="activeTab === 'home'">
          <section class="ds-home-hero">
            <img src="/dji/poster-a.jpg" alt="" class="ds-hero-bg" @error="imgFail($event, 900, 380)"/>
            <div class="ds-hero-scrim"></div>
            <div class="ds-hero-inner">
              <p class="ds-hero-kicker">DJI 大疆商城 · 无人机推荐</p>
              <h2>飞起来，看见更大的世界</h2>
              <button class="ds-hero-cta" @click="switchTab('drones')">选购无人机 →</button>
            </div>
          </section>
          <div class="ds-container">
            <div class="ds-cat-grid">
              <button v-for="c in homeCats" :key="c.id" class="ds-cat-card" @click="switchTab(c.id)">
                <span class="ds-cat-icon" v-html="c.icon"></span>
                <div>
                  <h4>{{ c.label }}</h4>
                  <p>{{ c.desc }}</p>
                </div>
              </button>
            </div>

            <h3 class="ds-section-title">热门无人机</h3>
            <div class="ds-hot-grid">
              <button class="ds-hot-card" @click="switchTab('drones')">
                <div class="ds-hot-imgwrap"><img src="/dji/drone-main.png" alt="DJI Air 3" @error="imgFail($event, 150, 110)"/></div>
                <div class="ds-hot-name">DJI Air 3</div>
                <div class="ds-hot-desc">双摄旗舰 · 46分钟续航</div>
                <div class="ds-hot-price">¥7,999 <span class="ds-hot-tag">演示价</span></div>
                <div class="ds-hot-link">查看详情 →</div>
              </button>
              <a v-for="p in hotDrones" :key="p.name" class="ds-hot-card" href="javascript:void(0)"
                 @click="openOfficial(p.url, p.name)">
                <div class="ds-hot-imgwrap"><img :src="p.img" :alt="p.name" @error="imgFail($event, 150, 110)"/></div>
                <div class="ds-hot-name">{{ p.name }}</div>
                <div class="ds-hot-desc">{{ p.desc }}</div>
                <div class="ds-hot-price ds-hot-price--dim">官方商城在售</div>
                <div class="ds-hot-link">前往官方商城 →</div>
              </a>
            </div>
            <p class="ds-price-note" style="margin: 12px 0 22px;">本页为无人机推荐的演示导购，价格以大疆官方商城实际显示为准</p>
          </div>
        </template>

        <!-- ═════ 运动相机 ═════ -->
        <template v-else-if="activeTab === 'cameras'">
          <div class="ds-container" style="padding-top: 28px;">
            <h3 class="ds-section-title">运动相机与口袋影像</h3>
            <div class="ds-cam-grid">
              <a v-for="p in cameras" :key="p.name" class="ds-cam-card" href="javascript:void(0)"
                 :title="'前往大疆官网：' + p.name" @click="openOfficial(p.url, p.name)">
                <div class="ds-cam-imgwrap"><img :src="p.img" :alt="p.name" @error="imgFail($event, 160, 160)"/></div>
                <div class="ds-cam-name">{{ p.name }}</div>
                <div class="ds-cam-desc">{{ p.desc }}</div>
                <div class="ds-cam-link">官方介绍页 →</div>
              </a>
            </div>
            <p class="ds-price-note" style="margin: 4px 0 24px;">
              以上为大疆官网产品介绍入口；商城购买页请以 store.dji.com 实际在售信息为准
            </p>
          </div>
        </template>

        <!-- ═════ 无人机（商品详情） ═════ -->
        <template v-else-if="activeTab === 'drones'">
          <!-- 2. 主视觉 Banner -->
          <section class="ds-banner">
            <img src="/dji/poster-a.jpg" alt="" class="ds-banner-bg" @error="imgFail($event, 900, 450)"/>
            <div class="ds-banner-scrim"></div>
            <div class="ds-banner-inner">
              <div class="ds-banner-text">
                <h1>DJI AIR 3</h1>
                <p class="ds-banner-sub">双摄旗舰 视界更大</p>
                <p class="ds-banner-spec">双主摄 ｜ 4K/60fps ｜ 46分钟续航</p>
                <button class="ds-banner-buy" @click="buyNow">立即购买 →</button>
              </div>
              <div class="ds-banner-drone">
                <img src="/dji/drone-640.png" alt="DJI Air 3" @error="imgFail($event, 420, 300)"/>
              </div>
            </div>
            <span class="ds-banner-index">1/6</span>
          </section>

          <div class="ds-container">
            <!-- 3. 核心参数展示区 -->
            <section class="ds-params">
              <div class="ds-param-col" v-for="(p, i) in coreParams" :key="i">
                <span class="ds-param-icon" v-html="p.icon"></span>
                <h4>{{ p.title }}</h4>
                <p>{{ p.desc }}</p>
              </div>
            </section>

            <!-- 4. 商品信息与价格评价区 -->
            <section class="ds-info">
              <div class="ds-info-left">
                <h2 class="ds-name">DJI Air 3 双摄旗舰无人机</h2>
                <p class="ds-attrs">双主摄 · 4K/60fps · 46分钟续航 · 全向避障</p>
                <div class="ds-price-row">
                  <span class="ds-price">¥{{ selectedVersion.price.toLocaleString() }}</span>
                  <span class="ds-tag-new">新品</span>
                </div>
                <div class="ds-rating">
                  <span class="ds-stars">★★★★★</span>
                  <span class="ds-score">4.9</span>
                  <span class="ds-divider">｜</span>
                  <span class="ds-count">1.2万+ 评价</span>
                </div>
                <p class="ds-price-note">价格为设计演示数据，实际以大疆官方商城页面为准</p>
              </div>
              <div class="ds-info-right">
                <div class="ds-scene-card">
                  <h5>双摄视界 记录更多可能</h5>
                  <div class="ds-scene-imgs">
                    <figure>
                      <img src="/dji/poster-e.jpg" alt="广角效果" @error="imgFail($event, 300, 180)"/>
                      <figcaption>24mm 广角 · 辽阔山河</figcaption>
                    </figure>
                    <figure>
                      <img src="/dji/poster-d.jpg" alt="中长焦效果" @error="imgFail($event, 300, 180)"/>
                      <figcaption>70mm 中长焦 · 空间压缩</figcaption>
                    </figure>
                  </div>
                </div>
              </div>
            </section>

            <!-- 5. 商品版本选择区 -->
            <section class="ds-versions">
              <h3 class="ds-section-title">选择版本</h3>
              <div class="ds-version-grid">
                <button
                  v-for="v in versions"
                  :key="v.id"
                  class="ds-version-card"
                  :class="{ selected: selectedId === v.id }"
                  @click="selectVersion(v)"
                >
                  <div class="ds-version-imgwrap" :class="{ photo: v.photo }">
                    <img :src="v.img" :alt="v.name" @error="imgFail($event, 160, 110)"/>
                  </div>
                  <div class="ds-version-name">{{ v.name }}</div>
                  <div class="ds-version-desc">{{ v.desc }}</div>
                  <div class="ds-version-price">¥{{ v.price.toLocaleString() }}</div>
                  <div class="ds-version-check" v-if="selectedId === v.id">✓ 已选</div>
                </button>
              </div>
              <p class="ds-version-note" v-if="!selectedVersion.verified">
                ⓘ 该版本的官方商城独立购买页暂不可用，点击「立即购买」将前往大疆官方商城无人机选购页
              </p>
            </section>

            <!-- 6. 配件推荐区 -->
            <section class="ds-accessories">
              <h3 class="ds-section-title">相关配件推荐</h3>
              <div class="ds-acc-grid">
                <a
                  v-for="a in accessories"
                  :key="a.name"
                  class="ds-acc-card"
                  href="javascript:void(0)"
                  :title="'前往大疆官方商城：' + a.name"
                  @click="openOfficial(a.url, a.name)"
                >
                  <div class="ds-acc-imgwrap">
                    <img :src="a.img" :alt="a.name" @error="imgFail($event, 140, 120)"/>
                  </div>
                  <div class="ds-acc-name">{{ a.name }}</div>
                  <div class="ds-acc-price">¥{{ a.price.toLocaleString() }}</div>
                </a>
              </div>
            </section>
          </div>

          <!-- 7. 底部固定购买栏（仅商品页） -->
          <footer class="ds-bottom-bar">
            <div class="ds-bar-left">
              <button class="ds-bar-svc" @click="toast('客服为演示入口，官方客服请访问 dji.com/cn/support')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 12a8 8 0 0 1 16 0"/><rect x="2.5" y="12" width="4" height="6" rx="1.6"/><rect x="17.5" y="12" width="4" height="6" rx="1.6"/>
                  <path d="M19.5 18a4 4 0 0 1-4 3h-2"/>
                </svg>
                <span>客服</span>
              </button>
              <button class="ds-bar-svc" @click="openOfficial('https://store.dji.com/cn', 'DJI 官方商城')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 9l1.6-5h12.8L20 9"/><path d="M4 9h16v10a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19V9Z"/><path d="M9.5 13.5h5"/>
                </svg>
                <span>店铺</span>
              </button>
              <button class="ds-bar-svc" :class="{ fav: favited }" @click="toggleFav">
                <svg viewBox="0 0 24 24" :fill="favited ? '#EB4335' : 'none'" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20.5S3.5 15.5 3.5 9.6C3.5 6.6 5.8 4.5 8.4 4.5c1.6 0 3 .8 3.6 2 .6-1.2 2-2 3.6-2 2.6 0 4.9 2.1 4.9 5.1 0 5.9-8.5 10.9-8.5 10.9Z"/>
                </svg>
                <span>收藏</span>
              </button>
            </div>
            <div class="ds-bar-right">
              <button class="ds-btn-cart" @click="addToCart">加入购物车</button>
              <button class="ds-btn-buy" @click="buyNow">立即购买</button>
            </div>
          </footer>
        </template>

        <!-- ═════ 配件 ═════ -->
        <template v-else-if="activeTab === 'accessories'">
          <div class="ds-container" style="padding-top: 28px;">
            <h3 class="ds-section-title">Air 3 系列配件</h3>
            <div class="ds-acc-grid" style="grid-template-columns: repeat(2, 1fr);">
              <a v-for="a in accessories" :key="'accp-' + a.name" class="ds-acc-card" href="javascript:void(0)"
                 :title="'前往大疆官方商城：' + a.name" @click="openOfficial(a.url, a.name)">
                <div class="ds-acc-imgwrap"><img :src="a.img" :alt="a.name" @error="imgFail($event, 160, 130)"/></div>
                <div class="ds-acc-name">{{ a.name }}</div>
                <div class="ds-acc-price">¥{{ a.price.toLocaleString() }}</div>
              </a>
            </div>
            <p class="ds-price-note" style="margin: 4px 0 24px;">配件价格为大疆官方商城页面价格，点击卡片直达对应官方商品页</p>
          </div>
        </template>

        <!-- ═════ 服务 ═════ -->
        <template v-else-if="activeTab === 'service'">
          <div class="ds-container" style="padding-top: 28px;">
            <h3 class="ds-section-title">服务与支持</h3>
            <div class="ds-svc-grid">
              <a v-for="s in services" :key="s.name" class="ds-svc-card" href="javascript:void(0)"
                 :title="'前往大疆官网：' + s.name" @click="openOfficial(s.url, s.name)">
                <span class="ds-svc-icon" v-html="s.icon"></span>
                <div class="ds-svc-name">{{ s.name }}</div>
                <div class="ds-svc-desc">{{ s.desc }}</div>
                <div class="ds-svc-link">前往官方页面 →</div>
              </a>
            </div>
          </div>
        </template>
      </div>

      <!-- 轻量 Toast -->
      <Transition name="ds-toast">
        <div v-if="toastMsg" class="ds-toast">{{ toastMsg }}</div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['close'])

/* ── 站内导航（真实页面切换） ── */
const navItems = [
  { id: 'home', label: '首页' },
  { id: 'cameras', label: '运动相机' },
  { id: 'drones', label: '无人机' },
  { id: 'accessories', label: '配件' },
  { id: 'service', label: '服务' },
]
const activeTab = ref('drones') // 打开弹窗默认落在无人机商品页
const scrollEl = ref(null)

function switchTab(id) {
  activeTab.value = id
  nextTick(() => { if (scrollEl.value) scrollEl.value.scrollTop = 0 })
}

/* ── 搜索 ── */
const searchOpen = ref(false)
const searchText = ref('')
const searchInput = ref(null)

function toggleSearch() {
  searchOpen.value = !searchOpen.value
  if (searchOpen.value) {
    setTimeout(() => searchInput.value && searchInput.value.focus(), 50)
  } else {
    searchText.value = ''
  }
}
function doSearch() {
  const kw = searchText.value.trim()
  if (!kw) return
  // 站内匹配：命中品类就切换过去，否则引导到官方商城搜索
  const kwMap = [
    { kw: ['air 3', 'air3', '无人机', '飞行'], tab: 'drones' },
    { kw: ['action', 'pocket', '相机', '云台', 'osmo'], tab: 'cameras' },
    { kw: ['电池', '滤镜', '包', '遥控', '配件', '充电'], tab: 'accessories' },
    { kw: ['维修', '保障', 'care', '服务', '支持'], tab: 'service' },
  ]
  const low = kw.toLowerCase()
  const hit = kwMap.find(m => m.kw.some(k => low.includes(k)))
  if (hit) {
    switchTab(hit.tab)
    toast(`已切换到「${navItems.find(n => n.id === hit.tab).label}」`)
  } else {
    openOfficial('https://store.dji.com/cn', 'DJI 官方商城')
  }
}

/* ── 首页数据 ── */
const homeCats = [
  { id: 'drones', label: '无人机', desc: '航拍旗舰与套装', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="5" cy="5" r="2.6"/><circle cx="19" cy="5" r="2.6"/><circle cx="5" cy="19" r="2.6"/><circle cx="19" cy="19" r="2.6"/><rect x="9" y="9" width="6" height="6" rx="1.5"/><path d="M7 7l2 2M17 7l-2 2M7 17l2-2M17 17l-2-2"/></svg>' },
  { id: 'cameras', label: '运动相机', desc: 'Action / Pocket 系列', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="13" height="12" rx="2.5"/><path d="M16 10.5l5-3v9l-5-3"/></svg>' },
  { id: 'accessories', label: '配件', desc: '电池 / 滤镜 / 遥控器', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="8" width="16" height="8" rx="2"/><path d="M18.5 10.5h2a1 1 0 0 1 1 1v1a1 1 0 0 1-1 1h-2"/><path d="M6 11v2M9.5 11v2M13 11v2"/></svg>' },
  { id: 'service', label: '服务', desc: '支持 / 维修 / 保障', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 16 0"/><rect x="2.5" y="12" width="4" height="6" rx="1.6"/><rect x="17.5" y="12" width="4" height="6" rx="1.6"/></svg>' },
]

/* 首页「热门无人机」：链接均为实测 200 的大疆官方商城页面；不编造价格 */
const hotDrones = [
  { name: 'DJI Air 3S', desc: '双摄旗舰 · 夜景航拍', img: '/dji/air3s.png', url: 'https://store.dji.com/cn/product/dji-air-3s' },
  { name: 'DJI Neo', desc: '掌上 Vlog 航拍机', img: '/dji/neo.png', url: 'https://store.dji.com/cn/product/dji-neo' },
  { name: 'DJI Avata 2', desc: '第一视角飞行体验', img: '/dji/avata2.png', url: 'https://store.dji.com/cn/product/dji-avata-2' },
]

/* ── 运动相机（官方介绍页实测 200） ── */
const cameras = [
  { name: 'Osmo Action 5 Pro', desc: '画质的下一代革命 · 运动相机', img: '/dji/action5pro.png', url: 'https://www.dji.com/cn/osmo-action-5-pro' },
  { name: 'Osmo Pocket 3', desc: '一英寸 CMOS · 口袋云台相机', img: '/dji/pocket3.png', url: 'https://www.dji.com/cn/osmo-pocket-3' },
]

/* ── 服务（链接均实测 200） ── */
const services = [
  {
    name: '官方支持与维修', desc: '产品支持、序列号查询、寄修服务', url: 'https://www.dji.com/cn/support',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.5-4.5"/></svg>',
  },
  {
    name: 'DJI Care 随心换', desc: '飞丢、进水、摔碰，低价换新', url: 'https://www.dji.com/cn/service/djicare-refresh',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 5-3.2 8.4-7 10-3.8-1.6-7-5-7-10V6l7-3Z"/><path d="M9 12l2 2 4-4.5"/></svg>',
  },
  {
    name: 'DJI 官方商城', desc: '官方直营 · 正品保障', url: 'https://store.dji.com/cn',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9l1.6-5h12.8L20 9"/><path d="M4 9h16v10a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19V9Z"/><path d="M9.5 13.5h5"/></svg>',
  },
  {
    name: '无人机选购页', desc: '全系航拍机对比选购', url: 'https://store.dji.com/cn/selection/camera-drones',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="5" cy="5" r="2.6"/><circle cx="19" cy="5" r="2.6"/><circle cx="5" cy="19" r="2.6"/><circle cx="19" cy="19" r="2.6"/><rect x="9" y="9" width="6" height="6" rx="1.5"/><path d="M7 7l2 2M17 7l-2 2M7 17l2-2M17 17l-2-2"/></svg>',
  },
]

/* ── 商品数据（价格为设计演示数据；链接均经过实际访问验证，属于大疆官方域名） ── */
const versions = [
  {
    id: 'standard',
    name: '标准版',
    desc: 'DJI Air 3 · 单电单充',
    price: 7999,
    img: '/dji/drone-main.png',
    url: 'https://store.dji.com/cn/product/dji-air-3',
    verified: true,
  },
  {
    id: 'flymore',
    name: '畅飞套装',
    desc: '三电池 · 充电管家 · 单肩包',
    price: 10999,
    img: '/dji/combo.png',
    url: 'https://store.dji.com/cn/product/dji-air-3-combo',
    verified: true,
  },
  {
    id: 'cinema',
    name: '影视套装',
    desc: '双电池 · RC 2 带屏遥控 · 充电管家',
    price: 12999,
    img: '/dji/poster-c.jpg',
    photo: true,
    // 大疆官方商城暂无该演示版本的独立购买页，不伪造链接，降级到官方选购页
    url: 'https://store.dji.com/cn/selection/camera-drones',
    verified: false,
  },
]

const selectedId = ref('standard')
const selectedVersion = computed(() => versions.find(v => v.id === selectedId.value))

function selectVersion(v) {
  selectedId.value = v.id
}

const accessories = [
  { name: 'ND 滤镜套装', price: 599, img: '/dji/nd-filters.png', url: 'https://store.dji.com/cn/product/dji-air-3-nd-filters-set-8-64' },
  { name: '智能飞行电池', price: 499, img: '/dji/battery.png', url: 'https://store.dji.com/cn/product/dji-air-3-intelligent-flight-battery' },
  { name: '便携包', price: 399, img: '/dji/bag.png', url: 'https://store.dji.com/cn/product/dji-convertible-carrying-bag' },
  { name: 'DJI RC 2 遥控器', price: 2999, img: '/dji/rc2.png', url: 'https://store.dji.com/cn/product/dji-rc-2' },
]

const coreParams = [
  {
    title: '双摄系统',
    desc: '广角 + 中长焦',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><rect x="2.5" y="7" width="12" height="10" rx="2"/><rect x="14" y="9" width="7.5" height="6" rx="1.5"/><circle cx="8.5" cy="12" r="2.4"/></svg>',
  },
  {
    title: '4K/60fps',
    desc: '高画质视频',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="13" height="12" rx="2.5"/><path d="M16 10.5l5-3v9l-5-3"/></svg>',
  },
  {
    title: '46分钟续航',
    desc: '更长飞行时间',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="8" width="16" height="8" rx="2"/><path d="M18.5 10.5h2a1 1 0 0 1 1 1v1a1 1 0 0 1-1 1h-2"/><path d="M6 11v2M9.5 11v2M13 11v2"/></svg>',
  },
  {
    title: '全向避障',
    desc: '安全飞行',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3.2"/><path d="M12 3.5v3M12 17.5v3M3.5 12h3M17.5 12h3"/></svg>',
  },
]

/* ── 交互 ── */
const cartCount = ref(2)
const favited = ref(false)
const toastMsg = ref('')
let toastTimer = null

function toast(msg) {
  toastMsg.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toastMsg.value = ''), 2600)
}

function toggleFav() {
  favited.value = !favited.value
  if (favited.value) toast('已加入收藏')
}

function addToCart() {
  cartCount.value++
  toast(`已将「${selectedVersion.value.name}」加入本地购物车（演示，不等于官网下单）`)
}

/**
 * 跳转大疆官方页面。
 * url 全部来自上方经过实际访问验证（HTTP 200、dji.com 官方域名）的配置，
 * 不做任何猜测或拼接；未验证版本降级到官方选购页并明确提示。
 */
function openOfficial(url, name) {
  toast(`即将前往大疆官方：${name}`)
  window.open(url, '_blank', 'noopener,noreferrer')
}

function buyNow() {
  const v = selectedVersion.value
  if (v.verified) {
    openOfficial(v.url, v.name)
  } else {
    toast('「影视套装」暂无官方独立购买页，已为你打开大疆官方商城选购页')
    window.open(v.url, '_blank', 'noopener,noreferrer')
  }
}

/* 图片加载失败 → 灰底占位，不留破图 */
function imgFail(e, w, h) {
  const el = e.target
  if (el.dataset.fallback) return
  el.dataset.fallback = '1'
  el.style.width = w + 'px'
  el.style.height = h + 'px'
  el.style.objectFit = 'contain'
  el.src =
    'data:image/svg+xml;charset=utf-8,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="100%" height="100%" fill="#F4F4F4"/><text x="50%" y="52%" dominant-baseline="middle" text-anchor="middle" fill="#A4A4A4" font-size="13">图片加载失败</text></svg>`
    )
}

/* Esc 关闭弹窗 */
function onKey(e) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
/*
 * 尺寸说明：本弹窗挂载在大屏 1194×834 缩放画板（.tanee-scalable-viewport）内部，
 * 所有尺寸使用画板坐标系下的 px（与其它 modal 一致），随画板整体等比缩放；
 * 禁用 vw/vh——在 transform 缩放容器里它们仍按真实视口计算，会导致溢出。
 */
.dji-shop-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
}
.dji-shop-card {
  position: relative;
  width: 1120px;
  height: 770px;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.22);
  display: flex;
  flex-direction: column;
  color: #333333;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ═══════════ 1. 顶部导航 ═══════════ */
.ds-nav {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 22px;
  height: 56px;
  background: rgba(255, 255, 255, 0.97);
  border-bottom: 1px solid #ECECEC;
  flex: none;
}
.ds-logo { height: 22px; width: auto; display: block; cursor: pointer; }
.ds-nav-mid { display: flex; gap: 26px; flex: 1; justify-content: center; }
.ds-nav-link {
  position: relative;
  font-size: 14px;
  color: #525866;
  text-decoration: none;
  padding: 18px 2px;
  line-height: 20px;
  white-space: nowrap;
  cursor: pointer;
}
.ds-nav-link:hover { color: #181B25; }
.ds-nav-link.active { color: #181B25; font-weight: 600; }
.ds-nav-link.active::after {
  content: '';
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: 0;
  width: 24px;
  height: 2px;
  background: #181B25;
  border-radius: 2px;
}
.ds-nav-right { display: flex; align-items: center; gap: 6px; }
.ds-search-box { display: flex; align-items: center; gap: 4px; }
.ds-search-input {
  width: 140px;
  height: 30px;
  border: 1px solid #DCDCDC;
  border-radius: 8px;
  padding: 0 10px;
  font-size: 13px;
  outline: none;
  color: #333;
}
.ds-search-input:focus { border-color: #181B25; }
.ds-icon-btn {
  position: relative;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: #333333;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ds-icon-btn:hover { background: #F4F4F4; }
.ds-icon-btn svg { width: 18px; height: 18px; }
.ds-cart-badge {
  position: absolute;
  top: 0;
  right: -1px;
  min-width: 15px;
  height: 15px;
  padding: 0 4px;
  border-radius: 99999px;
  background: #EB4335;
  color: #fff;
  font-size: 10px;
  line-height: 15px;
  text-align: center;
  font-weight: 600;
}
.ds-close-btn { color: #8D8D8D; }
.ds-close-btn:hover { color: #333; background: #ECECEC; }

/* ═══════════ 滚动主体 ═══════════ */
.ds-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}
.ds-scroll > .ds-container:last-child { flex: 1; }

/* ═══════════ 首页 ═══════════ */
.ds-home-hero {
  position: relative;
  height: 300px;
  flex: none;
  overflow: hidden;
  background: linear-gradient(120deg, #dbe7f3, #eef3f8);
}
.ds-hero-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.ds-hero-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 255, 255, 0.5) 42%, rgba(255, 255, 255, 0) 70%);
}
.ds-hero-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  padding: 0 44px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  gap: 12px;
}
.ds-hero-kicker { margin: 0; font-size: 13px; letter-spacing: 2px; color: #525866; font-weight: 600; }
.ds-hero-inner h2 { margin: 0; font-size: 36px; font-weight: 700; color: #181B25; letter-spacing: -0.02em; }
.ds-hero-cta {
  height: 40px;
  padding: 0 24px;
  border: none;
  border-radius: 99999px;
  background: #181B25;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.ds-hero-cta:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(24, 27, 37, 0.28); }
.ds-cat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 26px;
}
.ds-cat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  background: #F4F4F4;
  border: none;
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  font-family: inherit;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.ds-cat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); }
.ds-cat-icon { width: 34px; height: 34px; color: #181B25; flex: none; }
.ds-cat-icon :deep(svg) { width: 34px; height: 34px; }
.ds-cat-card h4 { margin: 0 0 2px; font-size: 14.5px; font-weight: 700; color: #181B25; }
.ds-cat-card p { margin: 0; font-size: 12px; color: #8D8D8D; }
.ds-hot-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.ds-hot-card {
  background: #F4F4F4;
  border: none;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
  cursor: pointer;
  font-family: inherit;
  color: inherit;
  text-decoration: none;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.ds-hot-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); }
.ds-hot-imgwrap { height: 104px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; }
.ds-hot-imgwrap img { max-width: 150px; max-height: 104px; object-fit: contain; }
.ds-hot-name { font-size: 14.5px; font-weight: 700; color: #181B25; margin-bottom: 3px; }
.ds-hot-desc { font-size: 12px; color: #8D8D8D; margin-bottom: 6px; }
.ds-hot-price { font-size: 15px; font-weight: 700; color: #EB4335; }
.ds-hot-price--dim { color: #17B26A; font-size: 13px; }
.ds-hot-tag {
  font-size: 10px;
  color: #A4A4A4;
  font-weight: 500;
  border: 1px solid #DCDCDC;
  border-radius: 4px;
  padding: 0 4px;
  vertical-align: 2px;
}
.ds-hot-link { margin-top: 6px; font-size: 12px; color: #525866; }

/* ═══════════ 运动相机 ═══════════ */
.ds-cam-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 10px;
}
.ds-cam-card {
  display: flex;
  align-items: center;
  gap: 18px;
  background: #F4F4F4;
  border-radius: 12px;
  padding: 20px;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.ds-cam-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); }
.ds-cam-imgwrap { width: 150px; height: 130px; flex: none; display: flex; align-items: center; justify-content: center; }
.ds-cam-imgwrap img { max-width: 150px; max-height: 130px; object-fit: contain; }
.ds-cam-name { font-size: 17px; font-weight: 700; color: #181B25; margin-bottom: 4px; }
.ds-cam-desc { font-size: 13px; color: #8D8D8D; margin-bottom: 8px; }
.ds-cam-link { font-size: 12.5px; color: #17B26A; font-weight: 600; }

/* ═══════════ 服务 ═══════════ */
.ds-svc-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding-bottom: 26px;
}
.ds-svc-card {
  background: #F4F4F4;
  border-radius: 12px;
  padding: 20px;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.ds-svc-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); }
.ds-svc-icon { display: inline-block; width: 30px; height: 30px; color: #181B25; margin-bottom: 8px; }
.ds-svc-icon :deep(svg) { width: 30px; height: 30px; }
.ds-svc-name { font-size: 15.5px; font-weight: 700; color: #181B25; margin-bottom: 4px; }
.ds-svc-desc { font-size: 12.5px; color: #8D8D8D; margin-bottom: 8px; }
.ds-svc-link { font-size: 12px; color: #17B26A; font-weight: 600; }

/* ═══════════ Banner（无人机页） ═══════════ */
.ds-banner {
  position: relative;
  height: 380px;
  flex: none;
  overflow: hidden;
  background: linear-gradient(120deg, #dbe7f3 0%, #eef3f8 60%, #e8eef4 100%);
}
.ds-banner-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
/* 左侧白色渐变，保证深色文字可读 */
.ds-banner-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.82) 0%, rgba(255, 255, 255, 0.45) 38%, rgba(255, 255, 255, 0) 68%);
}
.ds-banner-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  padding: 0 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.ds-banner-text h1 {
  margin: 0 0 10px;
  font-size: 44px;
  line-height: 1.15;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #181B25;
}
.ds-banner-sub {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #181B25;
}
.ds-banner-spec {
  margin: 0 0 22px;
  font-size: 14px;
  color: #525866;
}
.ds-banner-buy {
  height: 42px;
  padding: 0 26px;
  border: none;
  border-radius: 99999px;
  background: #181B25;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  font-family: inherit;
}
.ds-banner-buy:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(24, 27, 37, 0.28); }
.ds-banner-drone { flex: none; width: 42%; max-width: 440px; display: flex; justify-content: center; }
.ds-banner-drone img {
  width: 100%;
  height: auto;
  max-height: 300px;
  object-fit: contain;
  filter: drop-shadow(0 14px 20px rgba(0, 0, 0, 0.25));
}
.ds-banner-index {
  position: absolute;
  right: 22px;
  bottom: 14px;
  z-index: 1;
  font-size: 13px;
  color: #525866;
  background: rgba(255, 255, 255, 0.78);
  border-radius: 99999px;
  padding: 3px 12px;
  backdrop-filter: blur(8px);
}

/* ═══════════ 通用容器 / 标题 ═══════════ */
.ds-container {
  padding: 22px 44px 14px;
  flex: 1;
}
.ds-section-title {
  margin: 0 0 14px;
  font-size: 18px;
  font-weight: 700;
  color: #181B25;
}

/* ═══════════ 3. 核心参数 ═══════════ */
.ds-params {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: #F4F4F4;
  border-radius: 12px;
  padding: 20px 6px;
}
.ds-param-col {
  text-align: center;
  padding: 2px 14px;
  border-right: 1px solid #DCDCDC;
}
.ds-param-col:last-child { border-right: none; }
.ds-param-icon { display: inline-block; width: 28px; height: 28px; color: #181B25; }
.ds-param-icon :deep(svg) { width: 28px; height: 28px; }
.ds-param-col h4 { margin: 8px 0 4px; font-size: 15px; font-weight: 700; color: #181B25; }
.ds-param-col p { margin: 0; font-size: 12.5px; color: #8D8D8D; }

/* ═══════════ 4. 商品信息 ═══════════ */
.ds-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  align-items: center;
  padding: 26px 0;
}
.ds-name { margin: 0 0 8px; font-size: 24px; font-weight: 700; color: #181B25; }
.ds-attrs { margin: 0 0 14px; font-size: 13.5px; color: #8D8D8D; }
.ds-price-row { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px; }
.ds-price {
  font-size: 32px;
  font-weight: 700;
  color: #EB4335;
  letter-spacing: -0.02em;
}
.ds-tag-new {
  font-size: 12px;
  color: #fff;
  background: #EB4335;
  border-radius: 4px;
  padding: 2px 8px;
  font-weight: 600;
}
.ds-rating { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.ds-stars { color: #F9AD19; letter-spacing: 2px; }
.ds-score { font-weight: 700; color: #181B25; }
.ds-divider { color: #DCDCDC; }
.ds-count { color: #8D8D8D; }
.ds-price-note { margin: 12px 0 0; font-size: 12px; color: #A4A4A4; }
.ds-scene-card {
  background: #F4F4F4;
  border-radius: 12px;
  padding: 16px;
}
.ds-scene-card h5 { margin: 0 0 12px; font-size: 15px; font-weight: 700; color: #181B25; }
.ds-scene-imgs { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.ds-scene-imgs figure { margin: 0; }
.ds-scene-imgs img {
  width: 100%;
  height: 132px;
  object-fit: cover;
  border-radius: 8px;
  display: block;
  background: #ECECEC;
}
.ds-scene-imgs figcaption {
  margin-top: 6px;
  font-size: 12px;
  color: #525866;
  text-align: center;
}

/* ═══════════ 5. 版本选择 ═══════════ */
.ds-versions { padding-bottom: 6px; }
.ds-version-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.ds-version-card {
  position: relative;
  background: #F4F4F4;
  border: 2px solid transparent;
  border-radius: 12px;
  padding: 16px 14px 14px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
  font-family: inherit;
}
.ds-version-card:hover { transform: translateY(-2px); background: #EFEFEF; }
.ds-version-card.selected { border-color: #EB4335; background: #fff; box-shadow: 0 6px 18px rgba(235, 67, 53, 0.12); }
.ds-version-imgwrap { height: 104px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
.ds-version-imgwrap img { max-width: 150px; max-height: 104px; object-fit: contain; }
/* 影视套装为实拍图：固定比例圆角缩略图，与透明底商品图视觉统一 */
.ds-version-imgwrap.photo img {
  width: 200px;
  height: 104px;
  max-width: none;
  object-fit: cover;
  border-radius: 8px;
}
.ds-version-name { font-size: 15px; font-weight: 700; color: #181B25; margin-bottom: 4px; }
.ds-version-desc { font-size: 12.5px; color: #8D8D8D; margin-bottom: 8px; }
.ds-version-price { font-size: 17px; font-weight: 700; color: #EB4335; }
.ds-version-check {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 11px;
  color: #EB4335;
  font-weight: 600;
}
.ds-version-note { margin: 10px 0 0; font-size: 12.5px; color: #B45309; }

/* ═══════════ 6. 配件推荐 ═══════════ */
.ds-accessories { padding: 6px 0 22px; }
.ds-acc-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.ds-acc-card {
  background: #F4F4F4;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
  text-decoration: none;
  color: inherit;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  cursor: pointer;
}
.ds-acc-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); }
.ds-acc-imgwrap { height: 112px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
.ds-acc-imgwrap img { max-width: 130px; max-height: 112px; object-fit: contain; }
.ds-acc-name { font-size: 13.5px; color: #333; font-weight: 600; margin-bottom: 4px; }
.ds-acc-price { font-size: 15px; font-weight: 700; color: #EB4335; }

/* ═══════════ 7. 底部固定购买栏 ═══════════ */
.ds-bottom-bar {
  position: sticky;
  bottom: 0;
  z-index: 5;
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 24px;
  background: #ffffff;
  border-top: 1px solid #ECECEC;
  flex: none;
}
.ds-bar-left { display: flex; gap: 18px; }
.ds-bar-svc {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  border: none;
  background: transparent;
  color: #525866;
  font-size: 11.5px;
  cursor: pointer;
  font-family: inherit;
}
.ds-bar-svc svg { width: 20px; height: 20px; }
.ds-bar-svc:hover, .ds-bar-svc.fav { color: #EB4335; }
.ds-bar-right { display: flex; gap: 12px; }
.ds-btn-cart, .ds-btn-buy {
  height: 42px;
  padding: 0 28px;
  border: none;
  border-radius: 99999px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  transition: transform 0.15s ease, filter 0.15s ease;
}
.ds-btn-cart { background: #F9AD19; }
.ds-btn-buy { background: #EB4335; }
.ds-btn-cart:hover, .ds-btn-buy:hover { filter: brightness(1.06); transform: translateY(-1px); }

/* ═══════════ Toast ═══════════ */
.ds-toast {
  position: absolute;
  left: 50%;
  top: 68px;
  transform: translateX(-50%);
  z-index: 20;
  background: rgba(24, 27, 37, 0.92);
  color: #fff;
  font-size: 13px;
  padding: 9px 18px;
  border-radius: 8px;
  max-width: 78%;
  text-align: center;
  pointer-events: none;
}
.ds-toast-enter-active, .ds-toast-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.ds-toast-enter-from, .ds-toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(-6px); }
</style>
