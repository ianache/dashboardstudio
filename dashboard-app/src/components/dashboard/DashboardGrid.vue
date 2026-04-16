<template>
  <div class="grid-outer">
    <div v-if="maximizedWidgetId" class="grid-maximize-overlay" @click="maximizedWidgetId = null"></div>
    <div
      class="grid-canvas"
      ref="canvasRef"
      :class="{ 'design-mode': isDesignMode }"
      :style="canvasStyle"
    >
      <!-- Background grid lines (design mode only) -->
      <div v-if="isDesignMode" class="grid-lines" :style="gridLinesStyle"></div>

      <!-- Widgets -->
      <div
        v-for="widget in widgets"
        :key="widget.id"
        class="grid-item"
        :style="getItemStyle(widget)"
      >
        <DashboardWidget
          :widget="widget"
          :isDesignMode="isDesignMode"
          :isSelected="selectedWidgetId === widget.id"
          :isMaximized="maximizedWidgetId === widget.id"
          :dashboardFilters="dashboardFilters"
          :dashboardPalette="dashboardPalette"
          @select="selectWidget(widget.id)"
          @toggle-maximize="maximizedWidgetId = maximizedWidgetId === widget.id ? null : widget.id"
          @configure="$emit('configure-widget', widget)"
          @remove="$emit('remove-widget', widget.id)"
          @drag-start="(e) => startDrag(e, widget)"
          @resize-start="(dir, e) => startResize(e, widget, dir)"
        />
      </div>

      <!-- Drop ghost indicator while dragging -->
      <div
        v-if="dragState.active"
        class="drag-ghost"
        :style="ghostStyle"
      ></div>

      <!-- Empty state for design mode -->
      <div v-if="isDesignMode && widgets.length === 0" class="grid-empty-design">
        <div class="grid-empty-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="#c0c0c0" stroke-width="2">
            <rect x="4" y="4" width="18" height="18" rx="3"/>
            <rect x="26" y="4" width="18" height="18" rx="3"/>
            <rect x="4" y="26" width="18" height="18" rx="3"/>
            <rect x="26" y="26" width="18" height="18" rx="3"/>
          </svg>
        </div>
        <p>Haz clic en <strong>+ Añadir widget</strong> para comenzar</p>
      </div>

      <!-- Empty state for view mode -->
      <div v-if="!isDesignMode && widgets.length === 0" class="grid-empty-view">
        <div class="empty-icon">📊</div>
        <h3>Dashboard vacío</h3>
        <p>Este dashboard no tiene widgets configurados aún.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import DashboardWidget from './DashboardWidget.vue'
import { useDashboardStore } from '@/stores/dashboard'

const props = defineProps({
  widgets: { type: Array, default: () => [] },
  isDesignMode: { type: Boolean, default: false },
  dashboardId: { type: String, required: true },
  dashboardFilters: { type: Array, default: () => [] },
  dashboardPalette: { type: String, default: null }
})

const emit = defineEmits(['configure-widget', 'remove-widget', 'widget-moved'])

const dashboardStore = useDashboardStore()

// Grid config
const COL_COUNT = 12
const ROW_HEIGHT = 90  // px per row unit
const GAP = 10         // px gap between cells

const canvasRef = ref(null)
const colWidth = ref(100)
const selectedWidgetId = ref(null)
const maximizedWidgetId = ref(null)

// ── Drag state ────────────────────────────────────────────────
const dragState = ref({
  active: false,
  widgetId: null,
  grabOffsetX: 0,   // px from widget left edge where user grabbed
  grabOffsetY: 0,   // px from widget top  edge where user grabbed
  pointerX: 0,      // current pointer position in canvas coords
  pointerY: 0
})

// ── Resize state ──────────────────────────────────────────────
const resizeState = ref({
  active: false,
  widgetId: null,
  direction: null,
  startMouseX: 0,
  startMouseY: 0,
  startW: 0,
  startH: 0,
  startX: 0
})

let resizeObserver = null

// ── Helpers ───────────────────────────────────────────────────
function updateColWidth() {
  if (!canvasRef.value) return
  colWidth.value = (canvasRef.value.offsetWidth - GAP * (COL_COUNT + 1)) / COL_COUNT
}

// Convert a clientX/Y into canvas-content coordinates (accounts for scroll)
function clientToCanvas(clientX, clientY) {
  if (!canvasRef.value) return { x: 0, y: 0 }
  const rect = canvasRef.value.getBoundingClientRect()
  return {
    x: clientX - rect.left + canvasRef.value.scrollLeft,
    y: clientY - rect.top  + canvasRef.value.scrollTop
  }
}

// Grid-unit snap functions — input is the desired pixel left/top of the widget
function snapCol(pxLeft) {
  return Math.round((pxLeft - GAP) / (colWidth.value + GAP))
}
function snapRow(pxTop) {
  return Math.round((pxTop - GAP) / (ROW_HEIGHT + GAP))
}

// Widget position (grid units) → absolute pixel style
function getItemStyle(widget) {
  const { x, y, w, h } = widget.position
  const colW = colWidth.value
  return {
    position: 'absolute',
    left:   `${GAP + x * (colW + GAP)}px`,
    top:    `${GAP + y * (ROW_HEIGHT + GAP)}px`,
    width:  `${w * colW + (w - 1) * GAP}px`,
    height: `${h * ROW_HEIGHT + (h - 1) * GAP}px`,
    transition: (dragState.value.widgetId === widget.id || resizeState.value.widgetId === widget.id)
      ? 'none' : 'left 0.15s ease, top 0.15s ease',
    zIndex: maximizedWidgetId.value === widget.id ? 100 : 10
  }
}

// ── Ghost (drop preview) ──────────────────────────────────────
const ghostStyle = computed(() => {
  const ds = dragState.value
  if (!ds.active) return {}
  const widget = props.widgets.find(w => w.id === ds.widgetId)
  if (!widget) return {}

  const colW = colWidth.value
  const targetLeft = ds.pointerX - ds.grabOffsetX
  const targetTop  = ds.pointerY - ds.grabOffsetY

  const snapX = Math.max(0, Math.min(COL_COUNT - widget.position.w, snapCol(targetLeft)))
  const snapY = Math.max(0, snapRow(targetTop))

  return {
    position: 'absolute',
    left:   `${GAP + snapX * (colW + GAP)}px`,
    top:    `${GAP + snapY * (ROW_HEIGHT + GAP)}px`,
    width:  `${widget.position.w * colW + (widget.position.w - 1) * GAP}px`,
    height: `${widget.position.h * ROW_HEIGHT + (widget.position.h - 1) * GAP}px`,
    background: 'rgba(24,144,255,0.12)',
    border: '2px dashed #1890ff',
    borderRadius: '8px',
    pointerEvents: 'none',
    zIndex: 50
  }
})

// ── Canvas size ───────────────────────────────────────────────
const canvasHeight = computed(() => {
  if (props.widgets.length === 0) return 400
  let maxRow = 0
  props.widgets.forEach(w => {
    const bottom = w.position.y + w.position.h
    if (bottom > maxRow) maxRow = bottom
  })
  return Math.max(400, maxRow * (ROW_HEIGHT + GAP) + GAP + 80)
})

const canvasStyle = computed(() => ({
  minHeight: `${canvasHeight.value}px`,
  position: 'relative'
}))

const gridLinesStyle = computed(() => ({
  backgroundSize: `calc(100% / ${COL_COUNT}) ${ROW_HEIGHT + GAP}px`,
  backgroundImage: `
    linear-gradient(to right, rgba(24,144,255,0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(24,144,255,0.06) 1px, transparent 1px)
  `,
  position: 'absolute',
  inset: 0,
  pointerEvents: 'none'
}))

// ── Drag ──────────────────────────────────────────────────────
function startDrag(e, widget) {
  if (!props.isDesignMode) return
  e.preventDefault()
  selectWidget(widget.id)

  const colW     = colWidth.value
  const canvasXY = clientToCanvas(e.clientX, e.clientY)

  // Where within the widget did the user grab?
  const widgetLeft = GAP + widget.position.x * (colW + GAP)
  const widgetTop  = GAP + widget.position.y * (ROW_HEIGHT + GAP)

  dragState.value = {
    active: true,
    widgetId: widget.id,
    grabOffsetX: canvasXY.x - widgetLeft,
    grabOffsetY: canvasXY.y - widgetTop,
    pointerX: canvasXY.x,
    pointerY: canvasXY.y
  }
}

// ── Resize ────────────────────────────────────────────────────
function startResize(e, widget, direction) {
  if (!props.isDesignMode) return
  e.preventDefault()
  selectWidget(widget.id)

  resizeState.value = {
    active: true,
    widgetId: widget.id,
    direction,
    startMouseX: e.clientX,
    startMouseY: e.clientY,
    startW: widget.position.w,
    startH: widget.position.h,
    startX: widget.position.x
  }
}

// ── Global mouse handlers (registered on document) ────────────
function onMouseMove(e) {
  if (dragState.value.active) {
    const pos = clientToCanvas(e.clientX, e.clientY)
    dragState.value.pointerX = pos.x
    dragState.value.pointerY = pos.y
  }

  if (resizeState.value.active) {
    const colW = colWidth.value
    const rs = resizeState.value
    const dxCols = Math.round((e.clientX - rs.startMouseX) / (colW + GAP))
    const dyRows = Math.round((e.clientY - rs.startMouseY) / (ROW_HEIGHT + GAP))

    const widget = props.widgets.find(w => w.id === rs.widgetId)
    if (!widget) return

    const newPos = { ...widget.position }
    if (rs.direction.includes('e')) {
      newPos.w = Math.max(1, Math.min(COL_COUNT - rs.startX, rs.startW + dxCols))
    }
    if (rs.direction.includes('s')) {
      newPos.h = Math.max(1, rs.startH + dyRows)
    }
    dashboardStore.updateWidgetPosition(props.dashboardId, rs.widgetId, newPos)
  }
}

function onMouseUp(e) {
  if (dragState.value.active) {
    const widget = props.widgets.find(w => w.id === dragState.value.widgetId)
    if (widget) {
      const pos = clientToCanvas(e.clientX, e.clientY)
      const targetLeft = pos.x - dragState.value.grabOffsetX
      const targetTop  = pos.y - dragState.value.grabOffsetY

      const newX = Math.max(0, Math.min(COL_COUNT - widget.position.w, snapCol(targetLeft)))
      const newY = Math.max(0, snapRow(targetTop))

      dashboardStore.updateWidgetPosition(props.dashboardId, dragState.value.widgetId, {
        ...widget.position,
        x: newX,
        y: newY
      })
    }
    dragState.value.active   = false
    dragState.value.widgetId = null
  }

  if (resizeState.value.active) {
    resizeState.value.active   = false
    resizeState.value.widgetId = null
  }
}

function selectWidget(id) {
  selectedWidgetId.value = id
}

onMounted(() => {
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup',   onMouseUp)

  if (canvasRef.value) {
    updateColWidth()
    resizeObserver = new ResizeObserver(() => {
      updateColWidth()
    })
    resizeObserver.observe(canvasRef.value)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup',   onMouseUp)
  
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<style scoped>
.grid-outer {
  width: 100%;
  height: 100%;
}

.grid-maximize-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 90;
}

.grid-canvas {
  width: 100%;
  user-select: none;
}

.grid-lines {
  z-index: 0;
}

.grid-item {
  z-index: 10;
}

.drag-ghost {
  z-index: 50;
}

.grid-empty-design {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 14px;
  pointer-events: none;
}

.grid-empty-view {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  text-align: center;
}
.grid-empty-view .empty-icon { font-size: 48px; opacity: 0.4; }
.grid-empty-view h3 { font-size: 16px; font-weight: 500; color: var(--text); }
.grid-empty-view p { font-size: 14px; max-width: 280px; }
</style>
