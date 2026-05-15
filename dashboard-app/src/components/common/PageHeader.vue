<template>
  <header class="page-header">
    <div class="ph-content">
      <div class="ph-info">
        <h1 v-if="title" class="ph-title">{{ title }}</h1>
        <p v-if="description" class="ph-desc">{{ description }}</p>
        <slot name="info-extra"></slot>
      </div>
      
      <div class="ph-actions">
        <slot name="actions"></slot>
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.page-header {
  width: 100%;
  margin-bottom: 32px; /* Increased standard separation */
  padding-bottom: 8px; /* Extra breathing room */
  flex-shrink: 0;
}

.ph-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.ph-info {
  flex: 1;
  min-width: 0;
}

.ph-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 4px 0;
  line-height: 1.2;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.ph-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.ph-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  height: 32px; /* Aligns with ph-title height */
}
</style>
