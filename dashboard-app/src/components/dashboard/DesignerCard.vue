<template>
  <div class="mcard" @click="$emit('design')">
    <!-- Gradient header -->
    <div class="mcard-header" :style="{ background: gradients[colorIndex % gradients.length] }">
      <div class="mcard-header-overlay" />
      <div class="mcard-zoom-bg" />
      <!-- Category icon badge -->
      <div class="mcard-category-badge">
        <span class="material-symbols-outlined text-xl" style="color: var(--primary)">{{ categoryIcon }}</span>
      </div>
    </div>

    <!-- Body -->
    <div class="mcard-body">
      <div class="mcard-title-row">
        <h3 class="mcard-name">{{ name }}</h3>
        <span class="mcard-widget-chip">{{ widgetCount }} widgets</span>
      </div>
      <p class="mcard-desc">{{ description || 'Sin descripción' }}</p>

      <!-- Footer -->
      <div class="mcard-footer">
        <!-- Status -->
        <div class="mcard-status">
          <template v-if="assignedUsersCount > 0">
            <div class="mcard-users-pill">
              <span class="material-symbols-outlined text-xs">group</span>
              {{ assignedUsersCount }} usuario{{ assignedUsersCount !== 1 ? 's' : '' }}
            </div>
          </template>
          <template v-else-if="isPublic">
            <div class="mcard-status-pill mcard-status-pill--public">
              <span class="material-symbols-outlined text-xs">public</span>
              Público
            </div>
          </template>
          <template v-else>
            <div class="mcard-status-pill mcard-status-pill--private">
              <span class="material-symbols-outlined text-xs">lock</span>
              Privado
            </div>
          </template>
        </div>

        <!-- 5 action buttons -->
        <div class="mcard-actions" @click.stop>
          <button
            class="mcard-action"
            title="Diseñar"
            @click.stop="$emit('design')"
          >
            <span class="material-symbols-outlined text-lg">design_services</span>
          </button>
          <button
            class="mcard-action"
            title="Asignar usuarios"
            @click.stop="$emit('assign')"
          >
            <span class="material-symbols-outlined text-lg">group_add</span>
          </button>
          <button
            class="mcard-action"
            title="Ver"
            @click.stop="$emit('view')"
          >
            <span class="material-symbols-outlined text-lg">visibility</span>
          </button>
          <button
            class="mcard-action"
            title="Exportar"
            @click.stop="$emit('export')"
          >
            <span class="material-symbols-outlined text-lg">download</span>
          </button>
          <button
            class="mcard-action mcard-action--danger"
            title="Eliminar"
            @click.stop="$emit('delete')"
          >
            <span class="material-symbols-outlined text-lg">delete</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
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
/* Material Symbols font */
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

.text-xs { font-size: 12px; }
.text-lg { font-size: 20px; }
.text-xl { font-size: 22px; }

.mcard {
  background: #fff;
  border: 1px solid var(--outline-variant);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(15,23,42,0.06);
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: box-shadow 0.25s ease, transform 0.2s ease;
}
.mcard:hover {
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.1);
  transform: translateY(-2px);
}

/* ── Header ── */
.mcard-header {
  height: 160px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}
.mcard-header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(2, 6, 23, 0.55) 0%, transparent 50%);
  z-index: 1;
}
.mcard-zoom-bg {
  position: absolute;
  inset: 0;
  transition: transform 0.5s ease;
}
.mcard:hover .mcard-zoom-bg {
  transform: scale(1.04);
}

.mcard-category-badge {
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
.mcard-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mcard-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.mcard-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
  line-height: 1.3;
  font-family: 'Plus Jakarta Sans', sans-serif;
  flex: 1;
  min-width: 0;
}
.mcard-widget-chip {
  font-size: 12px;
  font-weight: 500;
  color: var(--secondary);
  background: var(--surface-container-low);
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.mcard-desc {
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
.mcard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
  margin-top: auto;
  gap: 8px;
}

.mcard-status { display: flex; align-items: center; }

.mcard-users-pill {
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

.mcard-status-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 20px;
}
.mcard-status-pill--public {
  color: #059669;
  background: rgba(5, 150, 105, 0.08);
}
.mcard-status-pill--private {
  color: #64748b;
  background: rgba(100, 116, 139, 0.08);
}

/* ── Actions ── */
.mcard-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.mcard-action {
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
.mcard-action:hover {
  color: var(--primary);
  background: rgba(0, 88, 190, 0.07);
}
.mcard-action--danger:hover {
  color: var(--error);
  background: rgba(186, 26, 26, 0.07);
}

/* Tooltips — appear above */
.mcard-action[title]:hover::after {
  content: attr(title);
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
  opacity: 1;
  z-index: 50;
}
</style>
