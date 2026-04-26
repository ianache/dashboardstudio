<template>
  <div class="kpi-card">
    <div class="kpi-header">
      <div class="kpi-icon-wrap" :style="{ background: iconBg, color: iconColor }">
        <MIcon :icon="icon" :size="22" :fill="iconFill" />
      </div>
      <span class="kpi-trend">{{ trend }}</span>
    </div>
    <p class="kpi-label">{{ label }}</p>
    <p class="kpi-value">{{ value }}</p>
  </div>
</template>

<script setup>
import MIcon from './MIcon.vue'

defineProps({
  icon: { type: String, default: 'dashboard' },
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  trend: { type: String, default: '' },
  iconColor: { type: String, default: 'var(--primary)' },
  iconBg: { type: String, default: 'rgba(0,88,190,0.1)' },
  iconFill: { type: Number, default: 0 },
})
</script>

<style scoped>
.kpi-card {
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  border-radius: 12px;
  padding: var(--stack-md);
  box-shadow: var(--shadow);
  transition: box-shadow 0.3s ease;
}
.kpi-card:hover { box-shadow: var(--shadow-md); }

.kpi-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.kpi-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-trend {
  font-size: 12px;
  font-weight: 500;
  color: var(--on-surface-variant);
  text-align: right;
  line-height: 1.3;
}

.kpi-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--on-surface-variant);
  margin-bottom: 4px;
  letter-spacing: 0.01em;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--on-surface);
  line-height: 1;
}
</style>
