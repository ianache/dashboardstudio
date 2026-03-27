<template>
  <div class="grid-outer">
    <!-- Grid canvas -->
    <div
      class="grid-canvas"
      ref="canvasRef"
      :class="{ 'design-mode': isDesignMode }"
      :style="canvasStyle"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
    >
      <!-- Background grid lines (design mode only) -->
      <div v-if="isDesignMode" class="grid-lines" :style="gridLinesStyle"></div>

      <!-- Widgets -->
      <div
        v-for="widget in widgets"
        :key="widget.id"
        class="grid-item"
        :style="getItemStyle(widget)"
        @mousedown.self="isDesignMode && startDrag($event, widget)"
      >
        <DashboardWidget
          :widget="widget"
          :isDesignMode="isDesignMode"
          :isSelected="selectedWidgetId === widget.id"
          @select="selectWidget(widget.id)"
          @configure="$emit('configure-widget', widget)"
          @remove="$emit('remove-widget', widget.id)"
          @resize-start="(dir, e) => startResize(e, widget, dir)"
        />
      </div>

      <!-- Drop ghost indicator while dragging -->
      <div
        v-if="dragState.active"
        class="drag-ghost"
        :style="getGhostStyle()"
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
import { ref, computed, onBeforeUnmount } from 'vue'
import DashboardWidget from './DashboardWidget.vue'
import { useDashboardStore } from '@/stores/dashboard'

const props = defineProps({
  widgets: { type: Array, default: () => [] },
  isDesignMode: { type: Boolean, default: false },
  dashboardId: { type: String, required: true }
})

const emit = defineEmits(['configure-widget', 'remove-widget', 'widget-moved'])

const dashboardStore = useDashboardStore()

// Grid config
const COL_COUNT = 12
const ROW_HEIGHT = 90 // px per row unit
const GAP = 10 // px

const canvasRef = ref(null)
const selectedWidgetId = ref(null)

// Drag state
const dragState = ref({
  active: false,
  widgetId: null,
  startMouseX: 0,
  startMouseY: 0,
  startX: 0,
  startY: 0,
  currentX: 0,
  currentY: 0
})

// Resize state
const resizeState = ref({
  active: false,
  widgetId: null,
  direction: null,
  startMouseX: 0,
  startMouseY: 0,
  startW: 0,
  startH: 0
})

// Computed canvas height (enough to fit all widgets + some extra)
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

function getColWidth() {
  if (!canvasRef.value) return 100
  const canvasW = canvasRef.value.offsetWidth
  return (canvasW - GAP * (COL_COUNT + 1)) / COL_COUNT
}

function getItemStyle(widget) {
  const { x, y, w, h } = widget.position
  const colW = getColWidth()

  const left = GAP + x * (colW + GAP)
  const top = GAP + y * (ROW_HEIGHT + GAP)
  const width = w * colW + (w - 1) * GAP
  const height = h * ROW_HEIGHT + (h - 1) * GAP

  return {
    position: 'absolute',
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`,
    transition: dragState.value.widgetId === widget.id || resizeState.value.widgetId === widget.id
      ? 'none'
      : 'all 0.15s ease'
  }
}

function getGhostStyle() {
  if (!dragState.value.active) return {}
  const widget = props.widgets.find(w => w.id === dragState.value.widgetId)
  if (!widget) return {}

  const colW = getColWidth()
  const snapX = Math.max(0, Math.min(COL_COUNT - widget.position.w, snapToGrid(dragState.value.currentX)))
  const snapY = Math.max(0, snapToRowGrid(dragState.value.currentY))

  return {
    position: 'absolute',
    left: `${GAP + snapX * (colW + GAP)}px`,
    top: `${GAP + snapY * (ROW_HEIGHT + GAP)}px`,
    width: `${widget.position.w * colW + (widget.position.w - 1) * GAP}px`,
    height: `${widget.position.h * ROW_HEIGHT + (widget.position.h - 1) * GAP}px`,
    background: 'rgba(24,144,255,0.12)',
    border: '2px dashed #1890ff',
    borderRadius: '8px',
    pointerEvents: 'none',
    zIndex: 50
  }
}

function snapToGrid(pixelX) {
  const colW = getColWidth()
  return Math.round(pixelX / (colW + GAP))
}

function snapToRowGrid(pixelY) {
  return Math.round(pixelY / (ROW_HEIGHT + GAP))
}

function getCanvasOffset() {
  const rect = canvasRef.value?.getBoundingClientRect()
  return rect ? { left: rect.left, top: rect.top } : { left: 0, top: 0 }
}

function startDrag(e, widget) {
  if (!props.isDesignMode) return
  e.preventDefault()
  selectWidget(widget.id)

  const offset = getCanvasOffset()
  dragState.value = {
    active: true,
    widgetId: widget.id,
    startMouseX: e.clientX,
    startMouseY: e.clientY,
    startX: widget.position.x,
    startY: widget.position.y,
    currentX: e.clientX - offset.left - GAP,
    currentY: e.clientY - offset.top - GAP
  }
}

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
    startH: widget.position.h
  }
}

function onMouseMove(e) {
  if (dragState.value.active) {
    const offset = getCanvasOffset()
    dragState.value.currentX = e.clientX - offset.left - GAP
    dragState.value.currentY = e.clientY - offset.top - GAP
  }

  if (resizeState.value.active) {
    const colW = getColWidth()
    const rs = resizeState.value
    const dxCols = Math.round((e.clientX - rs.startMouseX) / (colW + GAP))
    const dyRows = Math.round((e.clientY - rs.startMouseY) / (ROW_HEIGHT + GAP))

    const widget = props.widgets.find(w => w.id === rs.widgetId)
    if (!widget) return

    if (rs.direction.includes('e') || rs.direction === 'se') {
      const newW = Math.max(1, Math.min(COL_COUNT - widget.position.x, rs.startW + dxCols))
      dashboardStore.updateWidgetPosition(props.dashboardId, rs.widgetId, {
        ...widget.position,
        w: newW
      })
    }
    if (rs.direction.includes('s') || rs.direction === 'se') {
      const newH = Math.max(1, rs.startH + dyRows)
      dashboardStore.updateWidgetPosition(props.dashboardId, rs.widgetId, {
        ...widget.position,
        h: newH
      })
    }
  }
}

function onMouseUp(e) {
  if (dragState.value.active) {
    const widget = props.widgets.find(w => w.id === dragState.value.widgetId)
    if (widget) {
      const offset = getCanvasOffset()
      const mouseX = e.clientX - offset.left - GAP
      const mouseY = e.clientY - offset.top - GAP

      const newX = Math.max(0, Math.min(COL_COUNT - widget.position.w, snapToGrid(mouseX)))
      const newY = Math.max(0, snapToRowGrid(mouseY))

      dashboardStore.updateWidgetPosition(props.dashboardId, dragState.value.widgetId, {
        ...widget.position,
        x: newX,
        y: newY
      })
    }
    dragState.value.active = false
    dragState.value.widgetId = null
  }

  if (resizeState.value.active) {
    resizeState.value.active = false
    resizeState.value.widgetId = null
  }
}

function selectWidget(id) {
  selectedWidgetId.value = id
}

// Deselect on canvas click
function handleCanvasClick() {
  selectedWidgetId.value = null
}

onBeforeUnmount(() => {
  dragState.value.active = false
  resizeState.value.active = false
})
</script>

<style scoped>
.grid-outer {
  width: 100%;
  height: 100%;
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

.design-mode .grid-item {
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
