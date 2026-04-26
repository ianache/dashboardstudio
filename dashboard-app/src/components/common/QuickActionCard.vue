<template>
  <button class="qac-btn" :class="`qac-${variant}`" @click="$emit('click')">
    <div class="qac-icon-wrap">
      <MIcon :icon="icon" :size="28" />
    </div>
    <span class="qac-title">{{ title }}</span>
    <span v-if="description" class="qac-desc">{{ description }}</span>
  </button>
</template>

<script setup>
import MIcon from './MIcon.vue'

defineProps({
  icon: { type: String, default: 'add' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  variant: { type: String, default: 'default' }, // 'primary' | 'default' | 'secondary'
})
defineEmits(['click'])
</script>

<style scoped>
.qac-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--stack-lg);
  border-radius: 12px;
  border: 1px solid transparent;
  cursor: pointer;
  text-align: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  width: 100%;
}
.qac-btn:hover  { transform: scale(1.02); box-shadow: var(--shadow-md); }
.qac-btn:active { transform: scale(0.98); }

/* Primary variant */
.qac-primary {
  background: var(--primary-container);
  color: var(--on-primary-container);
  box-shadow: var(--shadow-md);
}
.qac-primary .qac-icon-wrap { background: rgba(255, 255, 255, 0.2); }
.qac-primary:hover .qac-icon-wrap { background: rgba(255, 255, 255, 0.3); }

/* Default variant */
.qac-default {
  background: var(--surface-container-high);
  color: var(--on-surface);
  border-color: var(--outline-variant);
}
.qac-default .qac-icon-wrap { background: rgba(0, 88, 190, 0.1); color: var(--primary); }
.qac-default:hover { border-color: rgba(0, 88, 190, 0.35); }
.qac-default:hover .qac-icon-wrap { background: rgba(0, 88, 190, 0.18); }

/* Secondary variant */
.qac-secondary {
  background: var(--surface-container-high);
  color: var(--on-surface);
  border-color: var(--outline-variant);
}
.qac-secondary .qac-icon-wrap { background: rgba(86, 94, 116, 0.1); color: var(--secondary); }
.qac-secondary:hover { border-color: rgba(86, 94, 116, 0.35); }
.qac-secondary:hover .qac-icon-wrap { background: rgba(86, 94, 116, 0.18); }

.qac-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.qac-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.qac-desc {
  font-size: 13px;
  font-weight: 400;
  opacity: 0.72;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
