<template>
  <div class="shadcn-badge" :class="[variant]">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default' // 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info'
  }
})
</script>

<style lang="scss" scoped>
.shadcn-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 1px solid transparent;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1;
  transition: all 0.15s ease;
  white-space: nowrap;

  &.default {
    background-color: var(--primary);
    color: var(--primary-foreground);
    border-color: transparent;
  }

  &.secondary {
    background-color: var(--secondary);
    color: var(--secondary-foreground);
    border-color: var(--border);
  }

  &.destructive {
    background-color: #fef2f2;
    color: #dc2626;
    border-color: #fecaca;
  }

  &.outline {
    background-color: #ffffff;
    color: var(--foreground);
    border-color: var(--border);
  }

  &.success {
    background-color: #f0fdf4;
    color: #16a34a;
    border-color: #bbf7d0;
  }

  &.warning {
    background-color: #fffbeb;
    color: #d97706;
    border-color: #fde68a;
  }

  &.info {
    background-color: #f0f9ff;
    color: #0284c7;
    border-color: #bae6fd;
  }
}
</style>
