<template>
  <button
    class="shadcn-btn"
    :class="[variant, size, { 'is-loading': loading }]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="spinner"></span>
    <slot name="prefix" />
    <span class="btn-text">
      <slot />
    </span>
    <slot name="suffix" />
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default' // 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success'
  },
  size: {
    type: String,
    default: 'default' // 'default' | 'sm' | 'lg' | 'icon'
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style lang="scss" scoped>
.shadcn-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.25;
  cursor: pointer;
  outline: none;
  border: 1px solid transparent;
  transition: all 0.15s ease;
  user-select: none;
  white-space: nowrap;

  &:disabled {
    pointer-events: none;
    opacity: 0.5;
  }

  // Sizes
  &.default {
    height: 36px;
    padding: 0 14px;
  }

  &.sm {
    height: 30px;
    padding: 0 10px;
    font-size: 12px;
  }

  &.lg {
    height: 42px;
    padding: 0 18px;
    font-size: 14px;
  }

  &.icon {
    height: 36px;
    width: 36px;
    padding: 0;
  }

  // Variants
  &.default {
    background-color: var(--primary);
    color: #ffffff;

    &:hover:not(:disabled) {
      background-color: var(--primary-hover);
    }
  }

  &.secondary {
    background-color: #f1f5f9;
    color: #1e293b;
    border-color: #e2e8f0;

    &:hover:not(:disabled) {
      background-color: #e2e8f0;
    }
  }

  &.outline {
    background-color: #ffffff;
    color: #334155;
    border-color: #cbd5e1;

    &:hover:not(:disabled) {
      background-color: #f8fafc;
      color: #0f172a;
      border-color: #94a3b8;
    }
  }

  &.ghost {
    background-color: transparent;
    color: #64748b;

    &:hover:not(:disabled) {
      background-color: #f1f5f9;
      color: #0f172a;
    }
  }

  &.destructive {
    background-color: #ef4444;
    color: #ffffff;

    &:hover:not(:disabled) {
      background-color: #dc2626;
    }
  }

  &.success {
    background-color: #16a34a;
    color: #ffffff;

    &:hover:not(:disabled) {
      background-color: #15803d;
    }
  }

  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: btn-spin 0.6s linear infinite;
  }
}

@keyframes btn-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
