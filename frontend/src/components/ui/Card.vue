<template>
  <div class="shadcn-card" :class="[variant, className]">
    <div v-if="title || $slots.header || description" class="shadcn-card-header">
      <div class="header-main">
        <h3 v-if="title" class="shadcn-card-title">{{ title }}</h3>
        <p v-if="description" class="shadcn-card-description">{{ description }}</p>
        <slot name="header" />
      </div>
      <div v-if="$slots.action" class="header-action">
        <slot name="action" />
      </div>
    </div>
    <div class="shadcn-card-content">
      <slot />
    </div>
    <div v-if="$slots.footer" class="shadcn-card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  variant: {
    type: String,
    default: 'default' // 'default' | 'muted' | 'interactive'
  },
  className: {
    type: String,
    default: ''
  }
})
</script>

<style lang="scss" scoped>
.shadcn-card {
  background-color: var(--card);
  color: var(--card-foreground);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &.interactive:hover {
    border-color: #cbd5e1;
    box-shadow: 0 6px 16px -2px rgba(0, 0, 0, 0.08);
    transform: translateY(-1px);
  }

  &.muted {
    background-color: var(--secondary);
  }
}

.shadcn-card-header {
  padding: 16px 20px 12px 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid var(--border);

  .header-main {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .shadcn-card-title {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--foreground);
    line-height: 1.3;
  }

  .shadcn-card-description {
    margin: 0;
    font-size: 12px;
    color: var(--muted-foreground);
    line-height: 1.4;
  }
}

.shadcn-card-content {
  padding: 18px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.shadcn-card-footer {
  padding: 12px 20px 16px 20px;
  display: flex;
  align-items: center;
  border-top: 1px solid var(--border);
}
</style>
