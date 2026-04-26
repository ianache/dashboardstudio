<template>
  <div class="dcard" @click="$emit('design')">
    <!-- Gradient header -->
    <div class="dcard-header" :style="{ background: gradients[colorIndex % gradients.length] }">
      <div class="dcard-header-overlay" />
      <div class="dcard-zoom-bg" />
      <!-- Category icon badge -->
      <div class="dcard-category-badge">
        <MIcon :icon="categoryIcon" :size="22" :fill="1" style="color: var(--primary)" />
      </div>
    </div>

    <!-- Body -->
    <div class="dcard-body">
      <div class="dcard-title-row">
        <h3 class="dcard-name">{{ name }}</h3>
        <span class="dcard-widget-chip">{{ widgetCount }} widgets</span>
      </div>
      <p class="dcard-desc">{{ description || 'Sin descripción' }}</p>

      <!-- Footer -->
      <div class="dcard-footer">
        <!-- Status -->
        <div class="dcard-status">
          <template v-if="assignedUsersCount > 0">
            <div class="dcard-users-pill">
              <MIcon icon="group" :size="14" />
              {{ assignedUsersCount }} usuario{{ assignedUsersCount !== 1 ? 's' : '' }}
            </div>
          </template>
          <template v-else-if="isPublic">
            <div class="dcard-status-pill dcard-status-pill--public">
              <MIcon icon="public" :size="13" />
              Público
            </div>
          </template>
          <template v-else>
            <div class="dcard-status-pill dcard-status-pill--private">
              <MIcon icon="lock" :size="13" />
              Privado
            </div>
          </template>
        </div>

        <!-- 5 action buttons -->
        <div class="dcard-actions" @click.stop>
          <button
            class="dcard-action"
            data-tooltip="Diseñar"
            @click.stop="$emit('design')"
          >
            <MIcon icon="design_services" :size="19" />
          </button>
          <button
            class="dcard-action"
            data-tooltip="Asignar usuarios"
            @click.stop="$emit('assign')"
          >
            <MIcon icon="group_add" :size="19" />
          </button>
          <button
            class="dcard-action"
            data-tooltip="Ver"
            @click.stop="$emit('view')"
          >
            <MIcon icon="visibility" :size="19" />
          </button>
          <button
            class="dcard-action"
            data-tooltip="Exportar"
            @click.stop="$emit('export')"
          >
            <MIcon icon="download" :size="19" />
          </button>
          <button
            class="dcard-action dcard-action--danger"
            data-tooltip="Eliminar"
            @click.stop="$emit('delete')"
          >
            <MIcon icon="delete" :size="19" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import MIcon from '@/components/common/MIcon.vue'

defineProps({
  name: { type: String, required: true },
  description: { type: String, default: '' },
  widgetCount: { type: Number, default: 0 },
  isPublic: { type: Boolean, default: false },
  assignedUsersCount: { type: Number, default: 0 },
  colorIndex: { type: Number, default: 0 },
  categoryIcon: { type: String, default: 'dashboard' },
})
defineEmits(['design', 'assign', 'view', 'export', 'delete'])

const gradients = [
  'linear-gradient(135deg, #1e3a5f 0%, #2170e4 100%)',
  'linear-gradient(135deg, #2d1b69 0%, #6063ee 100%)',
  'linear-gradient(135deg, #064e3b 0%, #059669 100%)',
  'linear-gradient(135deg, #7c2d12 0%, #ea580c 100%)',
  'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
  'linear-gradient(135deg, #4a044e 0%, #a21caf 100%)',
]
</script>

<style scoped>
.dcard {
  background: #fff;
  border: 1px solid var(--outline-variant);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: box-shadow 0.25s ease, transform 0.2s ease;
}
.dcard:hover {
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.1);
  transform: translateY(-2px);
}

/* ── Header ── */
.dcard-header {
  height: 160px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}
.dcard-header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(2, 6, 23, 0.55) 0%, transparent 50%);
  z-index: 1;
}
.dcard-zoom-bg {
  position: absolute;
  inset: 0;
  transition: transform 0.5s ease;
}
.dcard:hover .dcard-zoom-bg {
  transform: scale(1.04);
}

.dcard-category-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  border-radius: 8px;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 6px rgba(0,0,0,0.15);
}

/* ── Body ── */
.dcard-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dcard-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.dcard-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
  line-height: 1.3;
  font-family: 'Plus Jakarta Sans', sans-serif;
  flex: 1;
  min-width: 0;
}
.dcard-widget-chip {
  font-size: 12px;
  font-weight: 500;
  color: var(--secondary);
  background: var(--surface-container-low);
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.dcard-desc {
  font-size: 13px;
  color: var(--on-surface-variant);
  line-height: 1.5;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

/* ── Footer ── */
.dcard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
  margin-top: auto;
  gap: 8px;
}

.dcard-status { display: flex; align-items: center; }

.dcard-users-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--primary);
  background: rgba(0, 88, 190, 0.08);
  padding: 3px 8px;
  border-radius: 20px;
}

.dcard-status-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 20px;
}
.dcard-status-pill--public {
  color: #059669;
  background: rgba(5, 150, 105, 0.08);
}
.dcard-status-pill--private {
  color: #64748b;
  background: rgba(100, 116, 139, 0.08);
}

/* ── Actions ── */
.dcard-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.dcard-action {
  position: relative;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 7px;
  cursor: pointer;
  color: #94a3b8;
  transition: color 0.15s, background 0.15s;
}
.dcard-action:hover {
  color: var(--primary);
  background: rgba(0, 88, 190, 0.07);
}
.dcard-action--danger:hover {
  color: var(--error);
  background: rgba(186, 26, 26, 0.07);
}

/* Tooltips — appear above */
.dcard-action[data-tooltip] { position: relative; }
.dcard-action[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: #1e293b;
  color: #fff;
  font-size: 11px;
  padding: 3px 7px;
  border-radius: 5px;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 50;
}
.dcard-action[data-tooltip]:hover::after { opacity: 1; }
</style>
