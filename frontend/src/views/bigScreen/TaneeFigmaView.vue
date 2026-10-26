<template>
  <div class="tanee-figma-page">
    <!-- Top Switch Bar to easily toggle between views in local dev -->
    <div class="dev-nav-bar">
      <div class="dev-nav-info">
        <span class="figma-tag">FIGMA 1:1 PIXEL-PERFECT</span>
        <span class="file-name">Freebie - Tanee: Smart Farming App UI Kit (by Nija Works)</span>
      </div>
      <router-link to="/bigScreen" class="back-link">
        ← 返回玉米病害诊断大屏系统
      </router-link>
    </div>

    <!-- Mobile Device Canvas Wrapper (393px x 852px iPhone 15/16 Pro Standard) -->
    <div class="mobile-viewport-frame">
      <!-- 1. System Status Bar -->
      <div class="status-bar">
        <span class="status-time">9:41</span>
        <div class="dynamic-island-notch"></div>
        <div class="status-icons">
          <!-- Signal Icon -->
          <svg class="s-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3c-4.97 0-9 4.03-9 9 0 2.12.74 4.07 1.97 5.61L4.35 19.4c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0l1.83-1.83C9.17 19.68 10.54 20 12 20c4.97 0 9-4.03 9-9s-4.03-9-9-9zm0 15c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6z"/>
          </svg>
          <!-- Wifi Icon -->
          <svg class="s-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 4C7.31 4 3.07 5.9 0 8.98L12 21 24 8.98C20.93 5.9 16.69 4 12 4zm0 3.5c3.67 0 7.02 1.39 9.58 3.68L12 18.5 2.42 11.18C4.98 8.89 8.33 7.5 12 7.5z"/>
          </svg>
          <!-- Battery Icon -->
          <div class="battery-pill">
            <div class="battery-fill"></div>
          </div>
        </div>
      </div>

      <!-- 2. App Header (Auto Layout: Horizontal, Space-Between) -->
      <header class="app-header">
        <div class="user-profile-cluster">
          <div class="avatar-ring">
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"
              alt="Alex Johnson"
              class="user-avatar"
            />
            <span class="active-badge"></span>
          </div>
          <div class="user-titles">
            <span class="greeting-text">Good Morning 👋</span>
            <h1 class="user-name">Alex Johnson</h1>
          </div>
        </div>

        <div class="header-actions">
          <div class="weather-chip">
            <span class="weather-icon">☀️</span>
            <span class="weather-temp">28°C</span>
          </div>
          <button class="icon-circle-btn" aria-label="Notifications">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-svg">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
            <span class="unread-dot"></span>
          </button>
        </div>
      </header>

      <!-- Scrollable Main Content Frame (Auto Layout: Vertical, Gap 20px) -->
      <main class="scroll-body">
        <!-- 3. Farm Location Switcher (Auto Layout Horizontal Pill) -->
        <section class="location-bar">
          <div class="loc-pill">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="loc-pin">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
            </svg>
            <span class="loc-text">Green Valley Farm · Sector 04</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="chevron-down">
              <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </div>
          <span class="total-fields-tag">8 Fields Active</span>
        </section>

        <!-- 4. Hero Active Field Banner (Auto Layout Vertical Card) -->
        <section class="hero-field-card">
          <div class="hero-card-head">
            <div class="sector-tag">
              <span class="leaf-dot">🌱</span>
              <span>Greenhouse #01 · Corn Zone</span>
            </div>
            <span class="status-pill-optimal">● Optimal Growth</span>
          </div>

          <div class="hero-crop-main">
            <div class="hero-left">
              <h2 class="crop-title">Corn & Maize Field</h2>
              <div class="growth-meta">
                <span class="growth-day">Day 48 of 90</span>
                <span class="growth-dot">•</span>
                <span class="growth-stage">Vegetative Tasseling Stage</span>
              </div>
            </div>
            <div class="progress-radial-box">
              <div class="radial-text">
                <span class="pct">53%</span>
                <span class="pct-sub">Cycle</span>
              </div>
            </div>
          </div>

          <!-- Progress Bar Line -->
          <div class="growth-progress-track">
            <div class="growth-progress-bar" style="width: 53%;"></div>
          </div>

          <!-- Hero Bottom Quick Stats (Auto Layout: 3 Columns) -->
          <div class="hero-stats-row">
            <div class="h-stat-item">
              <span class="h-stat-label">Soil Moisture</span>
              <span class="h-stat-val">68%</span>
            </div>
            <div class="h-stat-divider"></div>
            <div class="h-stat-item">
              <span class="h-stat-label">Air Temp</span>
              <span class="h-stat-val">28.5°C</span>
            </div>
            <div class="h-stat-divider"></div>
            <div class="h-stat-item">
              <span class="h-stat-label">Sunlight</span>
              <span class="h-stat-val">8.4 hrs</span>
            </div>
          </div>
        </section>

        <!-- 5. Real-Time Telemetry Metrics (Auto Layout Grid: 2 Columns) -->
        <section class="section-block">
          <div class="section-title-row">
            <h3 class="section-title">Field Sensors Telemetry</h3>
            <span class="view-link">Details →</span>
          </div>

          <div class="sensor-grid-2x2">
            <!-- Metric 1: Soil Moisture -->
            <div class="sensor-card">
              <div class="sc-head">
                <div class="sc-icon-wrap blue">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sc-icon">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75c-4.5 5.25-6.75 8.625-6.75 11.25a6.75 6.75 0 0013.5 0c0-2.625-2.25-6-6.75-11.25z" />
                  </svg>
                </div>
                <span class="badge-status-normal">Normal</span>
              </div>
              <div class="sc-body">
                <span class="sc-val">68<small>%</small></span>
                <span class="sc-label">Soil Moisture</span>
              </div>
              <div class="sc-foot">
                <div class="mini-bar-track">
                  <div class="mini-bar-fill blue" style="width: 68%;"></div>
                </div>
                <span class="sc-sub">Target: 60 - 70%</span>
              </div>
            </div>

            <!-- Metric 2: Canopy Temperature -->
            <div class="sensor-card">
              <div class="sc-head">
                <div class="sc-icon-wrap amber">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sc-icon">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
                  </svg>
                </div>
                <span class="badge-status-warn">High</span>
              </div>
              <div class="sc-body">
                <span class="sc-val warn">28.5<small>°C</small></span>
                <span class="sc-label">Canopy Temp</span>
              </div>
              <div class="sc-foot">
                <div class="mini-bar-track">
                  <div class="mini-bar-fill amber" style="width: 78%;"></div>
                </div>
                <span class="sc-sub">+1.8°C vs yesterday</span>
              </div>
            </div>

            <!-- Metric 3: Air Humidity -->
            <div class="sensor-card">
              <div class="sc-head">
                <div class="sc-icon-wrap green">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sc-icon">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                  </svg>
                </div>
                <span class="badge-status-normal">Optimal</span>
              </div>
              <div class="sc-body">
                <span class="sc-val">74<small>%</small></span>
                <span class="sc-label">Relative Humidity</span>
              </div>
              <div class="sc-foot">
                <div class="mini-bar-track">
                  <div class="mini-bar-fill green" style="width: 74%;"></div>
                </div>
                <span class="sc-sub">Spore Risk: Alert</span>
              </div>
            </div>

            <!-- Metric 4: NPK Fertility -->
            <div class="sensor-card">
              <div class="sc-head">
                <div class="sc-icon-wrap purple">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sc-icon">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L4.2 15.3" />
                  </svg>
                </div>
                <span class="badge-status-normal">Balanced</span>
              </div>
              <div class="sc-body">
                <span class="sc-val">142<small>ppm</small></span>
                <span class="sc-label">NPK Soil Nutrients</span>
              </div>
              <div class="sc-foot">
                <div class="mini-bar-track">
                  <div class="mini-bar-fill purple" style="width: 62%;"></div>
                </div>
                <span class="sc-sub">Fertilized Today</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 6. Automation & Drone Dispatch (Auto Layout Horizontal Cards) -->
        <section class="section-block">
          <div class="section-title-row">
            <h3 class="section-title">Automations & Machinery</h3>
            <span class="view-link">Manage →</span>
          </div>

          <div class="automations-list">
            <!-- Drone Spraying Task -->
            <div class="auto-item-card">
              <div class="auto-icon-cell drone">
                <span>🚁</span>
              </div>
              <div class="auto-info-cell">
                <h4 class="auto-name">Drone Precision Spraying</h4>
                <p class="auto-desc">DJI T50 · Fungicide Treatment for Northern Blight</p>
                <div class="auto-meta-tags">
                  <span class="meta-tag">Scheduled 17:30</span>
                  <span class="meta-tag">1.8 L/acre</span>
                </div>
              </div>
              <div class="auto-toggle-cell">
                <div class="switch-toggle is-on">
                  <div class="switch-handle"></div>
                </div>
              </div>
            </div>

            <!-- Smart Drip Irrigation -->
            <div class="auto-item-card">
              <div class="auto-icon-cell drip">
                <span>💧</span>
              </div>
              <div class="auto-info-cell">
                <h4 class="auto-name">Smart Drip Irrigation</h4>
                <p class="auto-desc">Automated Solenoid Valve #03 · Moisture trigger</p>
                <div class="auto-meta-tags">
                  <span class="meta-tag active">Running Now</span>
                  <span class="meta-tag">2.4 L/min</span>
                </div>
              </div>
              <div class="auto-toggle-cell">
                <div class="switch-toggle is-on">
                  <div class="switch-handle"></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 7. Crop Health & Disease Analytics (Visual Progress) -->
        <section class="section-block">
          <div class="section-title-row">
            <h3 class="section-title">Crop Health AI Analytics</h3>
            <span class="view-link">Full Report →</span>
          </div>

          <div class="health-summary-card">
            <div class="hs-main">
              <div class="hs-donut-visual">
                <svg viewBox="0 0 36 36" class="health-donut-chart">
                  <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path class="circle" stroke-dasharray="94, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="donut-center">
                  <span class="donut-num">94.2%</span>
                </div>
              </div>
              <div class="hs-text">
                <h4 class="hs-heading">Overall Crops in Good Health</h4>
                <p class="hs-p">CBAM Attention model detected low leaf spots risk. 2 clusters flagged for preventive drone spraying.</p>
              </div>
            </div>

            <div class="hs-breakdown-row">
              <div class="break-chip good">
                <span class="b-dot"></span>
                <span>Healthy: 94.2%</span>
              </div>
              <div class="break-chip warn">
                <span class="b-dot"></span>
                <span>Leaf Blight: 3.8%</span>
              </div>
              <div class="break-chip info">
                <span class="b-dot"></span>
                <span>Common Rust: 2.0%</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <!-- 8. Floating Bottom Navigation Dock (Auto Layout Horizontal Tab Bar) -->
      <nav class="bottom-tab-bar">
        <button class="tab-item active">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="tab-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
          </svg>
          <span class="tab-label">Home</span>
          <span class="tab-active-dot"></span>
        </button>

        <button class="tab-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tab-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
          </svg>
          <span class="tab-label">Fields</span>
        </button>

        <button class="tab-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tab-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
          </svg>
          <span class="tab-label">Analytics</span>
        </button>

        <button class="tab-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tab-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.42 15.17L17.25 21A2.67 2.67 0 0021 17.25l-5.87-5.83m0 0a6 6 0 10-8.49-8.49m8.49 8.49l3.18 3.18" />
          </svg>
          <span class="tab-label">Devices</span>
        </button>

        <button class="tab-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tab-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          <span class="tab-label">Profile</span>
        </button>
      </nav>
    </div>
  </div>
</template>

<script setup>
// Pure pixel-perfect static implementation directly reflecting Figma node design
</script>

<style scoped>
/* ==========================================================================
   Tanee Smart Farming App UI Kit (Freebie by Nija Works)
   1:1 Pixel-Perfect Auto Layout Architecture & Design Tokens
   ========================================================================== */

/* Outer Page Frame for Desktop Sandbox */
.tanee-figma-page {
  min-height: 100vh;
  background-color: #0c1410;
  background-image: 
    radial-gradient(circle at 50% 0%, rgba(10, 135, 84, 0.25) 0%, transparent 60%),
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 100% 100%, 32px 32px, 32px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px 48px;
  font-family: -apple-system, BlinkMacSystemFont, 'Plus Jakarta Sans', 'Inter', 'Segoe UI', sans-serif;
  box-sizing: border-box;
}

/* Dev Top Bar */
.dev-nav-bar {
  width: 100%;
  max-width: 440px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 0 4px;
}

.dev-nav-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.figma-tag {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #34d399;
  font-family: monospace;
}

.file-name {
  font-size: 12px;
  color: #94a3b8;
}

.back-link {
  font-size: 12px;
  color: #a7f3d0;
  text-decoration: none;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.3);
  padding: 6px 12px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
}

.back-link:hover {
  background: rgba(16, 185, 129, 0.3);
  color: #ffffff;
}

/* 393px × 852px Mobile Frame */
.mobile-viewport-frame {
  width: 100%;
  max-width: 412px;
  height: 890px;
  background-color: #f7faf8;
  border-radius: 44px;
  border: 8px solid #1a2620;
  box-shadow: 
    0 25px 60px -15px rgba(0, 0, 0, 0.7),
    0 0 0 1px rgba(255, 255, 255, 0.1),
    inset 0 0 0 1px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* ── 1. Status Bar ────────────────────────────────────────────────────── */
.status-bar {
  height: 48px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  flex-shrink: 0;
  z-index: 20;
}

.status-time {
  font-size: 14px;
  font-weight: 600;
  color: #19201d;
  letter-spacing: -0.02em;
}

.dynamic-island-notch {
  width: 96px;
  height: 24px;
  background-color: #000000;
  border-radius: 16px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: 10px;
}

.status-icons {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #19201d;
}

.s-icon {
  width: 16px;
  height: 16px;
}

.battery-pill {
  width: 22px;
  height: 11px;
  border: 1.5px solid #19201d;
  border-radius: 3px;
  padding: 1px;
  display: flex;
  align-items: center;
  position: relative;
}

.battery-pill::after {
  content: '';
  position: absolute;
  right: -3px;
  top: 2.5px;
  width: 1.5px;
  height: 4px;
  background-color: #19201d;
  border-radius: 0 1px 1px 0;
}

.battery-fill {
  width: 75%;
  height: 100%;
  background-color: #19201d;
  border-radius: 1px;
}

/* ── 2. App Header ────────────────────────────────────────────────────── */
.app-header {
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.user-profile-cluster {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-ring {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  position: relative;
  padding: 2px;
  border: 1.5px solid #0a8754;
}

.user-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.active-badge {
  width: 10px;
  height: 10px;
  background-color: #10b981;
  border: 2px solid #ffffff;
  border-radius: 50%;
  position: absolute;
  bottom: 0;
  right: 0;
}

.user-titles {
  display: flex;
  flex-direction: column;
}

.greeting-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.user-name {
  font-size: 16px;
  font-weight: 700;
  color: #19201d;
  margin: 0;
  letter-spacing: -0.01em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.weather-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: #ffffff;
  border: 1px solid #e8ece9;
  padding: 6px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: #19201d;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.weather-icon {
  font-size: 14px;
}

.icon-circle-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background-color: #ffffff;
  border: 1px solid #e8ece9;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  transition: all 0.15s;
}

.icon-circle-btn:hover {
  background-color: #f0fdf4;
  border-color: #bbf7d0;
}

.btn-svg {
  width: 18px;
  height: 18px;
  color: #19201d;
}

.unread-dot {
  width: 7px;
  height: 7px;
  background-color: #ef4444;
  border-radius: 50%;
  position: absolute;
  top: 9px;
  right: 10px;
}

/* ── Scrollable Body Frame ────────────────────────────────────────────── */
.scroll-body {
  flex: 1;
  overflow-y: auto;
  padding: 4px 20px 96px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  scrollbar-width: none;
}

.scroll-body::-webkit-scrollbar {
  display: none;
}

/* ── 3. Farm Location Switcher ────────────────────────────────────────── */
.location-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.loc-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: #ffffff;
  border: 1px solid #e8ece9;
  border-radius: 12px;
  padding: 6px 12px;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.loc-pin {
  width: 14px;
  height: 14px;
  color: #0a8754;
}

.loc-text {
  font-size: 12px;
  font-weight: 600;
  color: #19201d;
}

.chevron-down {
  width: 12px;
  height: 12px;
  color: #64748b;
}

.total-fields-tag {
  font-size: 11px;
  color: #0a8754;
  background-color: #e8f5e9;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
}

/* ── 4. Hero Active Field Banner ──────────────────────────────────────── */
.hero-field-card {
  background: linear-gradient(135deg, #0a8754 0%, #065f38 100%);
  border-radius: 24px;
  padding: 20px;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 10px 24px -4px rgba(10, 135, 84, 0.35);
  position: relative;
  overflow: hidden;
}

.hero-field-card::after {
  content: '';
  position: absolute;
  top: -20px;
  right: -20px;
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.12) 0%, transparent 70%);
  pointer-events: none;
}

.hero-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sector-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 500;
}

.status-pill-optimal {
  font-size: 11px;
  font-weight: 600;
  background-color: #ffffff;
  color: #0a8754;
  padding: 4px 10px;
  border-radius: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.hero-crop-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.crop-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px;
  letter-spacing: -0.01em;
}

.growth-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #d1fae5;
}

.growth-dot {
  opacity: 0.6;
}

.progress-radial-box {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.25);
  border-top-color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radial-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1;
}

.pct {
  font-size: 12px;
  font-weight: 700;
}

.pct-sub {
  font-size: 9px;
  opacity: 0.8;
  margin-top: 1px;
}

.growth-progress-track {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.growth-progress-bar {
  height: 100%;
  background: #ffffff;
  border-radius: 3px;
}

.hero-stats-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(0, 0, 0, 0.12);
  border-radius: 14px;
  padding: 10px 14px;
}

.h-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.h-stat-label {
  font-size: 10px;
  color: #d1fae5;
}

.h-stat-val {
  font-size: 14px;
  font-weight: 700;
  margin-top: 2px;
}

.h-stat-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.2);
}

/* ── 5. Section Blocks & Metric Cards ─────────────────────────────────── */
.section-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: #19201d;
  margin: 0;
  letter-spacing: -0.01em;
}

.view-link {
  font-size: 12px;
  font-weight: 600;
  color: #0a8754;
  cursor: pointer;
}

/* 2x2 Sensor Grid */
.sensor-grid-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.sensor-card {
  background-color: #ffffff;
  border: 1px solid #e8ece9;
  border-radius: 18px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
  min-height: 128px;
}

.sc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sc-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;

  &.blue { background-color: #e0f2fe; color: #0284c7; }
  &.amber { background-color: #fef3c7; color: #d97706; }
  &.green { background-color: #ecfdf5; color: #059669; }
  &.purple { background-color: #f3e8ff; color: #9333ea; }
}

.sc-icon {
  width: 16px;
  height: 16px;
}

.badge-status-normal {
  font-size: 10px;
  font-weight: 600;
  color: #059669;
  background-color: #ecfdf5;
  padding: 2px 6px;
  border-radius: 6px;
}

.badge-status-warn {
  font-size: 10px;
  font-weight: 600;
  color: #d97706;
  background-color: #fffbeb;
  padding: 2px 6px;
  border-radius: 6px;
}

.sc-body {
  margin: 8px 0 6px;
  display: flex;
  flex-direction: column;
}

.sc-val {
  font-size: 22px;
  font-weight: 700;
  color: #19201d;
  line-height: 1.1;

  &.warn { color: #d97706; }

  small {
    font-size: 12px;
    font-weight: 500;
    margin-left: 2px;
  }
}

.sc-label {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.sc-foot {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mini-bar-track {
  width: 100%;
  height: 4px;
  background-color: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
}

.mini-bar-fill {
  height: 100%;
  border-radius: 2px;

  &.blue { background-color: #0284c7; }
  &.amber { background-color: #d97706; }
  &.green { background-color: #059669; }
  &.purple { background-color: #9333ea; }
}

.sc-sub {
  font-size: 9px;
  color: #94a3b8;
}

/* ── 6. Automations List ──────────────────────────────────────────────── */
.automations-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.auto-item-card {
  background-color: #ffffff;
  border: 1px solid #e8ece9;
  border-radius: 16px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.auto-icon-cell {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;

  &.drone { background-color: #ecfdf5; }
  &.drip { background-color: #e0f2fe; }
}

.auto-info-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.auto-name {
  font-size: 13px;
  font-weight: 700;
  color: #19201d;
  margin: 0;
}

.auto-desc {
  font-size: 11px;
  color: #64748b;
  margin: 0;
}

.auto-meta-tags {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.meta-tag {
  font-size: 10px;
  font-weight: 500;
  color: #475569;
  background-color: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;

  &.active {
    color: #059669;
    background-color: #ecfdf5;
    font-weight: 600;
  }
}

.switch-toggle {
  width: 38px;
  height: 22px;
  border-radius: 11px;
  background-color: #cbd5e1;
  padding: 2px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;

  &.is-on {
    background-color: #0a8754;
    justify-content: flex-end;
  }

  .switch-handle {
    width: 18px;
    height: 18px;
    background-color: #ffffff;
    border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }
}

/* ── 7. Health Summary Card ───────────────────────────────────────────── */
.health-summary-card {
  background-color: #ffffff;
  border: 1px solid #e8ece9;
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.hs-main {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hs-donut-visual {
  width: 64px;
  height: 64px;
  position: relative;
  flex-shrink: 0;
}

.health-donut-chart {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);

  .circle-bg {
    fill: none;
    stroke: #e2e8f0;
    stroke-width: 3.8;
  }

  .circle {
    fill: none;
    stroke-width: 3.8;
    stroke-linecap: round;
    stroke: #0a8754;
  }
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.donut-num {
  font-size: 13px;
  font-weight: 700;
  color: #19201d;
}

.hs-text {
  display: flex;
  flex-direction: column;
}

.hs-heading {
  font-size: 14px;
  font-weight: 700;
  color: #19201d;
  margin: 0 0 4px;
}

.hs-p {
  font-size: 11px;
  color: #64748b;
  line-height: 1.45;
  margin: 0;
}

.hs-breakdown-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #f1f5f9;
  padding-top: 10px;
}

.break-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 500;
  color: #475569;

  .b-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  &.good .b-dot { background-color: #0a8754; }
  &.warn .b-dot { background-color: #d97706; }
  &.info .b-dot { background-color: #0284c7; }
}

/* ── 8. Bottom Navigation Dock ────────────────────────────────────────── */
.bottom-tab-bar {
  position: absolute;
  bottom: 12px;
  left: 16px;
  right: 16px;
  height: 64px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(232, 236, 233, 0.8);
  border-radius: 28px;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 10px;
  box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.08);
  z-index: 30;
}

.tab-item {
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 12px;
  position: relative;
  transition: all 0.15s;
}

.tab-icon {
  width: 20px;
  height: 20px;
  color: #8c9b92;
}

.tab-label {
  font-size: 10px;
  font-weight: 600;
  color: #8c9b92;
}

.tab-item.active .tab-icon {
  color: #0a8754;
}

.tab-item.active .tab-label {
  color: #0a8754;
}

.tab-active-dot {
  width: 4px;
  height: 4px;
  background-color: #0a8754;
  border-radius: 50%;
  position: absolute;
  bottom: 2px;
}
</style>
