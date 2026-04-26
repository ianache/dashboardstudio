<template>
  <div class="db-card" @click="$emit('open')">
    <!-- Header gradient -->
    <div class="db-card-header" :style="{ background: gradients[colorIndex % gradients.length] }">
      <div class="db-card-header-overlay" />
      <MIcon icon="grid_view" :size="72" class="db-header-icon" />
      <span v-if="badge" class="db-badge" :class="`db-badge-${badge.variant}`">
        {{ badge.text }}
      </span>
    </div>

    <!-- Body -->
    <div class="db-card-body">
      <div class="db-card-title-row">
        <div class="db-card-title-block">
          <h4 class="db-card-title">{{ name }}</h4>
          <p class="db-card-desc">{{ description || 'Sin descripción' }}</p>
        </div>
        <button class="db-more-btn" @click.stop="$emit('menu')">
          <MIcon icon="more_vert" :size="20" />
        </button>
      </div>

      <div class="db-card-meta">
        <span class="db-meta-item">
          <MIcon icon="widgets" :size="16" class="db-meta-icon" />
          {{ widgetCount }} widgets
        </span>
        <span class="db-meta-item">
          <MIcon icon="schedule" :size="16" class="db-meta-icon" />
          {{ updatedLabel }}
        </span>
      </div>

      <div class="db-card-actions">
        <button class="db-open-btn" @click.stop="$emit('open')">Abrir Dashboard</button>
        <button class="db-share-btn" @click.stop="$emit('share')" data-tooltip="Compartir">
          <MIcon icon="share" :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import MIcon from './MIcon.vue'

defineProps({
  name: { type: String, required: true },
  description: { type: String, default: '' },
  widgetCount: { type: Number, default: 0 },
  updatedLabel: { type: String, default: '' },
  colorIndex: { type: Number, default: 0 },
  badge: { type: Object, default: null },
  // badge shape: { text: string, variant: 'active' | 'priority' | 'public' }
})
defineEmits(['open', 'share', 'menu'])

const gradients = [
  'linear-gradient(135deg, #1e3a5f 0%, #2170e4 100%)',
  'linear-gradient(135deg, #2d1b69 0%, #6063ee 100%)',
  'linear-gradient(135deg, #064e3b 0%, #059669 100%)',
  'linear-gradient(135deg, #7c2d12 0%, #ea580c 100%)',
  'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
]
</script>

<style scoped>
.db-card {
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: box-shadow 0.3s ease;
}
.db-card:hover { box-shadow: var(--shadow-lg); }

/* Header */
.db-card-header {
  height: 160px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter 0.3s ease;
}
.db-card:hover .db-card-header { filter: brightness(1.08); }

.db-card-header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(2, 6, 23, 0.65) 0%, transparent 55%);
  z-index: 1;
}

.db-header-icon {
  color: rgba(255, 255, 255, 0.12);
  z-index: 1;
  font-size: 72px !important;
}

.db-badge {
  position: absolute;
  bottom: 12px;
  left: 12px;
  z-index: 2;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}
.db-badge-active   { background: var(--primary-container); color: #fff; }
.db-badge-priority { background: var(--tertiary-container); color: #fff; }
.db-badge-public   { background: #059669; color: #fff; }

/* Body */
.db-card-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.db-card-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.db-card-title-block { flex: 1; min-width: 0; }
.db-card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.db-card-desc {
  font-size: 13px;
  color: var(--on-surface-variant);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.db-more-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--on-surface-variant);
  padding: 4px;
  border-radius: 6px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  transition: background 0.2s;
}
.db-more-btn:hover { background: var(--surface-container); }

.db-card-meta {
  display: flex;
  align-items: center;
  gap: 20px;
}
.db-meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 500;
  color: var(--on-surface);
}
.db-meta-icon { color: var(--on-surface-variant); }

/* Actions */
.db-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--outline-variant);
}
.db-open-btn {
  flex: 1;
  padding: 8px 16px;
  background: var(--primary);
  color: var(--on-primary);
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.15s;
  font-family: inherit;
}
.db-open-btn:hover  { background: var(--primary-dark); }
.db-open-btn:active { transform: scale(0.98); }

.db-share-btn {
  padding: 8px;
  background: none;
  border: 1px solid var(--outline-variant);
  border-radius: 8px;
  cursor: pointer;
  color: var(--on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, color 0.2s;
}
.db-share-btn:hover { background: var(--surface-container); color: var(--on-surface); }
</style>
