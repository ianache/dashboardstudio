<!--
  FlowEditorCanvas — Reusable visual diagram editor.

  Props (config):
    diagramType  : String  — ID of the diagram type being designed (e.g. 'data-integration')
    tools        : Array   — Tool objects already filtered for this diagram type

  Prop (data):
    diagramData  : Object  — Initial diagram { nodes: [], connections: [], metadata: {} }

  Emits:
    save(diagramData) — full diagram state when user clicks Save
-->
<template>
  <div class="fec-root" @mousemove="onGlobalMousemove" @mouseup="onGlobalMouseup">

    <!-- ── Left Panel: Components Toolbar ─────────────────────────────────── -->
    <aside class="fec-left" :class="{ 'fec-left--collapsed': leftCollapsed }">
      <button class="fec-toggle fec-toggle--left" @click="leftCollapsed = !leftCollapsed" :title="leftCollapsed ? 'Expandir' : 'Contraer'">
        <span class="msi">{{ leftCollapsed ? 'chevron_right' : 'chevron_left' }}</span>
      </button>

      <div class="fec-left-inner">
        <div v-if="!leftCollapsed" class="fec-left-head">
          <span class="msi" style="font-size:15px;color:#2563eb">widgets</span>
          <span class="fec-panel-label">Componentes</span>
          <span class="fec-diagram-tag">{{ diagramTypeLabel }}</span>
        </div>

        <template v-for="cat in toolsByCategory" :key="cat.key">
          <div class="fec-cat">
            <div class="fec-cat-hdr" @click="!leftCollapsed && toggleCat(cat.key)" :title="cat.label">
              <div class="fec-cat-hdr-l">
                <div class="fec-cat-dot" :style="{ background: cat.color }"></div>
                <span v-if="!leftCollapsed" class="fec-cat-name">{{ cat.label }}</span>
              </div>
              <span v-if="!leftCollapsed" class="msi fec-cat-arr" :class="{ 'fec-cat-arr--open': openCats[cat.key] }" style="font-size:15px;color:#94a3b8">expand_more</span>
            </div>

            <!-- Expanded list -->
            <div v-if="!leftCollapsed && openCats[cat.key]" class="fec-comp-list">
              <div
                v-for="tool in cat.items" :key="tool.id"
                class="fec-comp-item"
                draggable="true"
                @dragstart="onCompDragStart($event, tool)"
                :title="tool.name">
                <div class="fec-comp-ico" :style="{ background: cat.bg, color: cat.color }">
                  <span class="msi" style="font-size:14px">{{ tool.icon }}</span>
                </div>
                <div class="fec-comp-text">
                  <span class="fec-comp-name">{{ tool.name }}</span>
                  <span class="fec-comp-sub">{{ tool.subtitle }}</span>
                </div>
              </div>
            </div>

            <!-- Collapsed: only icons -->
            <div v-if="leftCollapsed" class="fec-comp-icons">
              <div
                v-for="tool in cat.items" :key="tool.id"
                class="fec-comp-ico fec-comp-ico--sm"
                :style="{ background: cat.bg, color: cat.color }"
                draggable="true"
                @dragstart="onCompDragStart($event, tool)"
                :title="tool.name">
                <span class="msi" style="font-size:13px">{{ tool.icon }}</span>
              </div>
            </div>
          </div>
        </template>

        <div v-if="toolsByCategory.length === 0 && !leftCollapsed" class="fec-no-tools">
          <span class="msi" style="font-size:28px;color:#cbd5e1">construction</span>
          <span>Sin herramientas<br>para este diagrama</span>
        </div>
      </div>
    </aside>

    <!-- ── Canvas Area ─────────────────────────────────────────────────────── -->
    <main
      class="fec-canvas-area"
      ref="canvasAreaRef"
      @wheel.prevent="onWheel"
      @mousedown="onCanvasMousedown"
      @dragover.prevent="onDragOver"
      @dragleave="isDragOver = false"
      @drop.prevent="onDrop"
      @click="onCanvasClick">

      <!-- Floating Toolbar (draggable) -->
      <div
        class="fec-float-bar"
        :style="{ left: fbarPos.x + 'px', top: fbarPos.y + 'px' }"
        @mousedown.stop="onFbarMousedown">
        <span class="msi fec-fbar-handle" style="font-size:17px;color:#94a3b8;cursor:grab">drag_indicator</span>
        <div class="fec-fsep"></div>
        <button class="fec-tbtn" @click.stop="zoomIn" title="Zoom In"><span class="msi" style="font-size:18px">zoom_in</span></button>
        <span class="fec-zoom-pct">{{ Math.round(zoom * 100) }}%</span>
        <button class="fec-tbtn" @click.stop="zoomOut" title="Zoom Out"><span class="msi" style="font-size:18px">zoom_out</span></button>
        <div class="fec-fsep"></div>
        <button class="fec-tbtn" :class="{ 'fec-tbtn--on': snapToGrid }" @click.stop="snapToGrid = !snapToGrid" title="Snap to grid">
          <span class="msi" style="font-size:18px">grid_on</span>
        </button>
        <button class="fec-tbtn" @click.stop="centerView" title="Centrar vista">
          <span class="msi" style="font-size:18px">center_focus_strong</span>
        </button>
        <button class="fec-tbtn" @click.stop="fitView" title="Ajustar a pantalla">
          <span class="msi" style="font-size:18px">fit_screen</span>
        </button>
      </div>

      <!-- Drop hint overlay -->
      <div v-if="isDragOver" class="fec-drop-hint">
        <span class="msi" style="font-size:32px;color:#2563eb">add_circle</span>
        <span>Soltar herramienta aquí</span>
      </div>

      <!-- Canvas container (pan + zoom transform) -->
      <div
        class="fec-canvas"
        ref="canvasRef"
        :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})`, transformOrigin: '0 0', width: CANVAS_W + 'px', height: CANVAS_H + 'px' }">

        <!-- SVG layer: connections -->
        <svg :width="CANVAS_W" :height="CANVAS_H" style="position:absolute;top:0;left:0;overflow:visible">
          <defs>
            <marker id="fec-arr" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L0,8 L10,4 z" fill="#94a3b8" />
            </marker>
            <marker id="fec-arr-sel" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L0,8 L10,4 z" fill="#2563eb" />
            </marker>
          </defs>
          <!-- Connections -->
          <path
            v-for="conn in connections"
            :key="conn.id"
            :d="connPath(conn)"
            :stroke="selectedConn === conn.id || hoveredConn === conn.id ? '#2563eb' : '#94a3b8'"
            :stroke-width="selectedConn === conn.id ? 2.5 : 2"
            fill="none"
            :marker-end="selectedConn === conn.id || hoveredConn === conn.id ? 'url(#fec-arr-sel)' : 'url(#fec-arr)'"
            style="cursor:pointer"
            @mouseenter="hoveredConn = conn.id"
            @mouseleave="hoveredConn = null"
            @click.stop="selectedConn = selectedConn === conn.id ? null : conn.id"
          />
          <!-- Temp connection while drawing -->
          <path
            v-if="tempConn"
            :d="tempConn"
            stroke="#2563eb"
            stroke-width="2"
            stroke-dasharray="6 3"
            fill="none"
            pointer-events="none"
          />
        </svg>

        <!-- Nodes -->
        <div
          v-for="node in nodes" :key="node.id"
          class="fec-node"
          :class="[`fec-node--${node.category}`, { 'fec-node--sel': selectedNode?.id === node.id }]"
          :style="{ left: node.x + 'px', top: node.y + 'px', '--nc': getCatColor(node.category), '--nb': getCatBg(node.category) }"
          @mousedown.stop="onNodeMousedown($event, node)"
          @click.stop="selectNode(node)">

          <div v-if="node.category !== 'source'" class="fec-port fec-port--in"
            @mousedown.stop="onPortMousedown($event, node, 'in')"
            @mouseup="onPortMouseup($event, node, 'in')">
          </div>

          <div class="fec-node-hdr">
            <div class="fec-node-hdr-ico">
              <span class="msi" style="font-size:13px">{{ getToolByType(node.toolType)?.icon || 'circle' }}</span>
            </div>
            <span class="fec-node-lbl" :title="node.label">{{ node.label }}</span>
          </div>
          <div class="fec-node-bdy">
            <span class="fec-node-tag">{{ node.toolType }}</span>
            <span v-if="node.props?.table || node.props?.schema" class="fec-node-meta">
              {{ [node.props.schema, node.props.table].filter(Boolean).join('.') }}
            </span>
            <span v-else-if="node.props?.url" class="fec-node-meta">{{ node.props.url }}</span>
          </div>

          <div v-if="node.category !== 'destination' && node.category !== 'notification'" class="fec-port fec-port--out"
            @mousedown.stop="onPortMousedown($event, node, 'out')"
            @mouseup="onPortMouseup($event, node, 'out')">
          </div>
        </div>
      </div>

      <!-- Connection action bar -->
      <div v-if="selectedConn" class="fec-conn-bar">
        <span class="fec-conn-lbl">Conexión seleccionada</span>
        <button class="fec-conn-del" @click="deleteConn(selectedConn)">
          <span class="msi" style="font-size:15px">delete</span>Eliminar
        </button>
      </div>
    </main>

    <!-- ── Right Panel: Properties ─────────────────────────────────────────── -->
    <aside class="fec-right" :class="{ 'fec-right--collapsed': rightCollapsed }">
      <button class="fec-toggle fec-toggle--right" @click="rightCollapsed = !rightCollapsed" :title="rightCollapsed ? 'Expandir' : 'Contraer'">
        <span class="msi">{{ rightCollapsed ? 'chevron_left' : 'chevron_right' }}</span>
      </button>

      <div v-if="!rightCollapsed" class="fec-right-inner">

        <!-- ── Flow properties ── -->
        <template v-if="!selectedNode">
          <div class="fec-props-hdr">
            <span class="msi" style="font-size:20px;color:#2563eb">settings</span>
            <div>
              <p class="fec-props-title">Propiedades del Diagrama</p>
              <p class="fec-props-sub">{{ diagramTypeLabel }}</p>
            </div>
          </div>

          <div class="fec-prop-g">
            <label class="fec-prop-l">Nombre</label>
            <input v-model="metadata.name" class="fec-prop-i" />
          </div>
          <div class="fec-prop-g">
            <label class="fec-prop-l">Descripción</label>
            <textarea v-model="metadata.description" class="fec-prop-ta" rows="3"></textarea>
          </div>
          <div class="fec-prop-g">
            <label class="fec-prop-l">Estado</label>
            <div class="fec-sel-wrap">
              <select v-model="metadata.status" class="fec-prop-sel">
                <option value="active">Activo</option>
                <option value="scheduled">Programado</option>
                <option value="paused">Pausado</option>
                <option value="draft">Draft</option>
              </select>
              <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
            </div>
          </div>

          <template v-for="(def, key) in diagramMetaPropDefs" :key="key">
            <div class="fec-prop-g">
              <label class="fec-prop-l">{{ def.label }}</label>
              <div v-if="def.type === 'select'" class="fec-sel-wrap">
                <select v-model="metadata[key]" class="fec-prop-sel">
                  <option v-for="o in def.options" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
                <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
              </div>
              <input v-else v-model="metadata[key]" class="fec-prop-i" :placeholder="def.placeholder || ''" />
            </div>
          </template>

          <div class="fec-flow-stats">
            <div class="fec-stat-row"><span class="msi" style="font-size:15px;color:#64748b">hub</span><span>{{ nodes.length }} nodos</span></div>
            <div class="fec-stat-row"><span class="msi" style="font-size:15px;color:#64748b">device_hub</span><span>{{ connections.length }} conexiones</span></div>
          </div>
        </template>

        <!-- ── Node properties ── -->
        <template v-else>
          <div class="fec-props-hdr">
            <div class="fec-props-node-ico" :style="{ background: getCatBg(selectedNode.category), color: getCatColor(selectedNode.category) }">
              <span class="msi" style="font-size:18px">{{ getToolByType(selectedNode.toolType)?.icon || 'circle' }}</span>
            </div>
            <div style="flex:1;min-width:0">
              <p class="fec-props-title" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ selectedNode.label }}</p>
              <p class="fec-props-sub">{{ getToolByType(selectedNode.toolType)?.name || selectedNode.toolType }}</p>
            </div>
            <button class="fec-close-btn" @click="selectedNode = null"><span class="msi" style="font-size:15px">close</span></button>
          </div>

          <div class="fec-prop-g">
            <label class="fec-prop-l">Etiqueta</label>
            <input v-model="selectedNode.label" class="fec-prop-i" />
          </div>

          <div class="fec-divider"><span>Propiedades del componente</span></div>

          <template v-for="(def, key) in getNodePropDefs(selectedNode.toolType)" :key="key">
            <div class="fec-prop-g">
              <label class="fec-prop-l">{{ def.label }}</label>
              <textarea v-if="def.type === 'textarea'" v-model="selectedNode.props[key]" class="fec-prop-ta" :rows="def.rows || 3" :placeholder="def.placeholder || ''"></textarea>
              <div v-else-if="def.type === 'select'" class="fec-sel-wrap">
                <select v-model="selectedNode.props[key]" class="fec-prop-sel">
                  <option v-for="o in def.options" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
                <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
              </div>
              <input v-else v-model="selectedNode.props[key]" class="fec-prop-i" :placeholder="def.placeholder || ''" />
            </div>
          </template>

          <div class="fec-node-del-wrap">
            <button class="fec-node-del-btn" @click="deleteSelectedNode">
              <span class="msi" style="font-size:15px">delete</span>Eliminar nodo
            </button>
          </div>
        </template>

      </div>
    </aside>

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { CAT_META } from '@/stores/toolCatalog'

// ─── Props & Emits ────────────────────────────────────────────────────────────
const props = defineProps({
  diagramType: { type: String, required: true },
  tools:       { type: Array,  default: () => [] },
  diagramData: { type: Object, default: () => ({ nodes: [], connections: [], metadata: {} }) },
})
const emit = defineEmits(['save', 'dirty-change'])

// ─── Constants ────────────────────────────────────────────────────────────────
const CANVAS_W = 4000
const CANVAS_H = 3000
const NODE_W   = 210
const NODE_H   = 82
const GRID     = 20

// Extra metadata props per diagram type
const DIAGRAM_META_PROPS = {
  'data-integration': {
    type:     { label: 'Tipo',                  type: 'select', options: [{ value: 'Batch ETL', label: 'Batch ETL' }, { value: 'Real-time Stream', label: 'Real-time Stream' }, { value: 'CDC', label: 'CDC' }, { value: 'API Pull', label: 'API Pull' }] },
    schedule: { label: 'Programación (Cron)',    type: 'text',   placeholder: '0 6 * * *' },
    source:   { label: 'Sistema Origen',         type: 'text',   placeholder: 'ERP SAP' },
    target:   { label: 'Sistema Destino',        type: 'text',   placeholder: 'ODS PostgreSQL' },
  },
  'process-flow': {
    owner:    { label: 'Responsable',            type: 'text',   placeholder: 'Área / persona' },
    version:  { label: 'Versión',               type: 'text',   placeholder: '1.0' },
  },
  'data-quality': {
    severity: { label: 'Severidad por defecto',  type: 'select', options: [{ value: 'low', label: 'Baja' }, { value: 'medium', label: 'Media' }, { value: 'high', label: 'Alta' }, { value: 'critical', label: 'Crítica' }] },
    schedule: { label: 'Programación (Cron)',    type: 'text',   placeholder: '0 * * * *' },
  },
}

// ─── Diagram type helpers ─────────────────────────────────────────────────────
const diagramTypeLabel = computed(() => {
  const map = {
    'data-integration': 'Data Integration Flow',
    'process-flow':     'Process Flow',
    'data-quality':     'Data Quality',
  }
  return map[props.diagramType] || props.diagramType
})

const diagramMetaPropDefs = computed(() => DIAGRAM_META_PROPS[props.diagramType] || {})

// ─── Tool helpers ─────────────────────────────────────────────────────────────
function getToolByType(toolType) {
  return props.tools.find(t => t.type === toolType) || null
}
function getNodePropDefs(toolType) {
  return getToolByType(toolType)?.prop_defs || {}
}
function getCatColor(cat) { return CAT_META[cat]?.color || '#64748b' }
function getCatBg(cat)    { return CAT_META[cat]?.bg    || '#f8fafc' }

// Group tools by category for left panel
const toolsByCategory = computed(() => {
  const map = {}
  for (const tool of props.tools) {
    if (!map[tool.category]) map[tool.category] = []
    map[tool.category].push(tool)
  }
  return Object.entries(map).map(([cat, items]) => ({
    key: cat,
    label: CAT_META[cat]?.label || cat,
    color: CAT_META[cat]?.color || '#64748b',
    bg:    CAT_META[cat]?.bg    || '#f8fafc',
    icon:  CAT_META[cat]?.icon  || 'category',
    items,
  }))
})

// ─── Diagram state (owned by this component) ──────────────────────────────────
const nodes       = ref([])
const connections = ref([])
const metadata    = ref({})

// ─── Dirty tracking ───────────────────────────────────────────────────────────
let savedSnapshot      = ''
let initializingFromProp = false

function takeSnapshot() {
  return JSON.stringify({ nodes: nodes.value, connections: connections.value, metadata: metadata.value })
}

// Initialize from prop
watch(() => props.diagramData, (data) => {
  initializingFromProp = true
  nodes.value       = data?.nodes       ? JSON.parse(JSON.stringify(data.nodes))       : []
  connections.value = data?.connections ? JSON.parse(JSON.stringify(data.connections)) : []
  metadata.value    = data?.metadata    ? JSON.parse(JSON.stringify(data.metadata))    : {}
  nextTick(() => {
    savedSnapshot = takeSnapshot()
    initializingFromProp = false
    emit('dirty-change', false)
  })
}, { immediate: true })

watch([nodes, connections, metadata], () => {
  if (initializingFromProp) return
  const dirty = takeSnapshot() !== savedSnapshot
  emit('dirty-change', dirty)
}, { deep: true })

// ─── UI state ─────────────────────────────────────────────────────────────────
const leftCollapsed  = ref(false)
const rightCollapsed = ref(false)
const openCats       = ref(Object.fromEntries(Object.keys(CAT_META).map(k => [k, true])))
const selectedNode   = ref(null)
const selectedConn   = ref(null)
const hoveredConn    = ref(null)
const snapToGrid     = ref(true)
const isDragOver     = ref(false)
const zoom           = ref(1)
const panX           = ref(40)
const panY           = ref(40)
const fbarPos        = ref({ x: 16, y: 16 })
const tempConn       = ref(null)
const canvasAreaRef  = ref(null)

function toggleCat(key) { openCats.value[key] = !openCats.value[key] }

// ─── Drag state (non-reactive, performance-critical) ─────────────────────────
let isPanning       = false, panStart       = null
let isDraggingNode  = false, draggedNode    = null, nodeDragStart = null
let isDraggingFbar  = false, fbarDragStart  = null
let hasDragged      = false
let isConnecting    = false, connectFrom    = null
let dragTool        = null  // tool being dragged from left panel

// ─── Helpers ──────────────────────────────────────────────────────────────────
function snapPos(x, y) {
  if (!snapToGrid.value) return { x, y }
  return { x: Math.round(x / GRID) * GRID, y: Math.round(y / GRID) * GRID }
}
function getCanvasPos(clientX, clientY) {
  const r = canvasAreaRef.value.getBoundingClientRect()
  return {
    x: (clientX - r.left - panX.value) / zoom.value,
    y: (clientY - r.top  - panY.value) / zoom.value,
  }
}

// ─── Connection paths ─────────────────────────────────────────────────────────
function connPath(conn) {
  const f = nodes.value.find(n => n.id === conn.from)
  const t = nodes.value.find(n => n.id === conn.to)
  if (!f || !t) return ''
  const x1 = f.x + NODE_W, y1 = f.y + NODE_H / 2
  const x2 = t.x,          y2 = t.y + NODE_H / 2
  const dx = Math.max(60, Math.abs(x2 - x1) * 0.45)
  return `M ${x1} ${y1} C ${x1+dx} ${y1}, ${x2-dx} ${y2}, ${x2} ${y2}`
}
function tempConnPath(fromNode, mx, my) {
  const r  = canvasAreaRef.value.getBoundingClientRect()
  const tx = (mx - r.left - panX.value) / zoom.value
  const ty = (my - r.top  - panY.value) / zoom.value
  const x1 = fromNode.x + NODE_W, y1 = fromNode.y + NODE_H / 2
  const dx = Math.max(40, Math.abs(tx - x1) * 0.4)
  return `M ${x1} ${y1} C ${x1+dx} ${y1}, ${tx-dx} ${ty}, ${tx} ${ty}`
}

// ─── Zoom / Pan ───────────────────────────────────────────────────────────────
function zoomIn()  { setZoom(zoom.value * 1.15) }
function zoomOut() { setZoom(zoom.value * 0.87) }
function setZoom(v) { zoom.value = Math.min(2.5, Math.max(0.15, v)) }

function onWheel(e) {
  const r = canvasAreaRef.value.getBoundingClientRect()
  const mx = e.clientX - r.left, my = e.clientY - r.top
  const f  = e.deltaY < 0 ? 1.1 : 0.9
  const nz = Math.min(2.5, Math.max(0.15, zoom.value * f))
  panX.value = mx - (mx - panX.value) * (nz / zoom.value)
  panY.value = my - (my - panY.value) * (nz / zoom.value)
  zoom.value = nz
}
function centerView() {
  if (!canvasAreaRef.value || nodes.value.length === 0) return
  const r = canvasAreaRef.value.getBoundingClientRect()
  const xs = nodes.value.map(n => n.x), ys = nodes.value.map(n => n.y)
  panX.value = r.width  / 2 - ((Math.min(...xs) + Math.max(...xs) + NODE_W) / 2) * zoom.value
  panY.value = r.height / 2 - ((Math.min(...ys) + Math.max(...ys) + NODE_H) / 2) * zoom.value
}
function fitView() {
  if (!canvasAreaRef.value || nodes.value.length === 0) return
  const r    = canvasAreaRef.value.getBoundingClientRect()
  const xs   = nodes.value.map(n => n.x), ys = nodes.value.map(n => n.y)
  const minX = Math.min(...xs), minY = Math.min(...ys)
  const maxX = Math.max(...xs) + NODE_W, maxY = Math.max(...ys) + NODE_H
  const pad  = 60
  const nz   = Math.min(1.5, Math.max(0.15, Math.min((r.width - pad*2) / (maxX - minX), (r.height - pad*2) / (maxY - minY))))
  zoom.value = nz
  panX.value = pad - minX * nz
  panY.value = pad - minY * nz
}

// ─── Canvas events ────────────────────────────────────────────────────────────
function onCanvasMousedown(e) {
  if (e.button !== 0) return
  isPanning  = true
  hasDragged = false
  panStart   = { mx: e.clientX, my: e.clientY, px: panX.value, py: panY.value }
}
function onCanvasClick() {
  if (!hasDragged) { selectedNode.value = null; selectedConn.value = null }
  hasDragged = false
}

// ─── Global move / up (on root element) ──────────────────────────────────────
function onGlobalMousemove(e) {
  if (isDraggingNode && draggedNode) {
    hasDragged = true
    const pos = getCanvasPos(e.clientX, e.clientY)
    const { x, y } = snapPos(nodeDragStart.nx + pos.x - nodeDragStart.sx, nodeDragStart.ny + pos.y - nodeDragStart.sy)
    draggedNode.x = Math.max(0, x)
    draggedNode.y = Math.max(0, y)
    return
  }
  if (isPanning && panStart) {
    const dx = e.clientX - panStart.mx, dy = e.clientY - panStart.my
    if (Math.abs(dx) + Math.abs(dy) > 3) hasDragged = true
    panX.value = panStart.px + dx
    panY.value = panStart.py + dy
    return
  }
  if (isDraggingFbar && fbarDragStart) {
    fbarPos.value = { x: fbarDragStart.tx + e.clientX - fbarDragStart.mx, y: fbarDragStart.ty + e.clientY - fbarDragStart.my }
    return
  }
  if (isConnecting && connectFrom && canvasAreaRef.value) {
    tempConn.value = tempConnPath(connectFrom, e.clientX, e.clientY)
  }
}
function onGlobalMouseup() {
  isDraggingNode = false; draggedNode = null; nodeDragStart = null
  isPanning = false; panStart = null
  isDraggingFbar = false; fbarDragStart = null
  isConnecting = false; connectFrom = null; tempConn.value = null
}

// ─── Node events ──────────────────────────────────────────────────────────────
function onNodeMousedown(e, node) {
  if (e.button !== 0) return
  isDraggingNode = true; draggedNode = node; hasDragged = false
  const pos = getCanvasPos(e.clientX, e.clientY)
  nodeDragStart = { sx: pos.x, sy: pos.y, nx: node.x, ny: node.y }
}
function selectNode(node) {
  if (!hasDragged) { selectedNode.value = node; selectedConn.value = null; rightCollapsed.value = false }
  hasDragged = false
}
function deleteSelectedNode() {
  if (!selectedNode.value) return
  const id = selectedNode.value.id
  nodes.value = nodes.value.filter(n => n.id !== id)
  connections.value = connections.value.filter(c => c.from !== id && c.to !== id)
  selectedNode.value = null
}

// ─── Port events ──────────────────────────────────────────────────────────────
function onPortMousedown(e, node, portType) {
  if (portType !== 'out') return
  isConnecting = true; connectFrom = node
  tempConn.value = tempConnPath(node, e.clientX, e.clientY)
}
function onPortMouseup(e, node, portType) {
  if (portType !== 'in' || !isConnecting || !connectFrom || connectFrom.id === node.id) return
  if (!connections.value.find(c => c.from === connectFrom.id && c.to === node.id)) {
    connections.value.push({ id: `c${Date.now()}`, from: connectFrom.id, to: node.id })
  }
  // cleanup happens in onGlobalMouseup (event bubbles there)
}

// ─── Floating toolbar drag ────────────────────────────────────────────────────
function onFbarMousedown(e) {
  isDraggingFbar = true
  fbarDragStart = { mx: e.clientX, my: e.clientY, tx: fbarPos.value.x, ty: fbarPos.value.y }
}

// ─── Connections ──────────────────────────────────────────────────────────────
function deleteConn(id) { connections.value = connections.value.filter(c => c.id !== id); selectedConn.value = null }

// ─── Drag & drop from left panel ─────────────────────────────────────────────
function onCompDragStart(e, tool) {
  dragTool = tool
  e.dataTransfer.effectAllowed = 'copy'
}
function onDragOver() { isDragOver.value = true }
function onDrop(e) {
  isDragOver.value = false
  if (!dragTool || !canvasAreaRef.value) return
  const pos = getCanvasPos(e.clientX, e.clientY)
  const { x, y } = snapPos(pos.x - NODE_W / 2, pos.y - NODE_H / 2)
  nodes.value.push({
    id:       `n${Date.now()}`,
    toolType: dragTool.type,
    category: dragTool.category,
    label:    dragTool.name,
    x: Math.max(0, x),
    y: Math.max(0, y),
    props: Object.fromEntries(Object.keys(dragTool.prop_defs || {}).map(k => [k, dragTool.default_props?.[k] ?? ''])),
  })
  dragTool = null
}

// ─── Save ─────────────────────────────────────────────────────────────────────
function getCurrentDiagramData() {
  return {
    nodes:       JSON.parse(JSON.stringify(nodes.value)),
    connections: JSON.parse(JSON.stringify(connections.value)),
    metadata:    JSON.parse(JSON.stringify(metadata.value)),
  }
}

function markSaved() {
  savedSnapshot = takeSnapshot()
  emit('dirty-change', false)
}

function save() {
  const data = getCurrentDiagramData()
  emit('save', data)
  markSaved()
}

defineExpose({ save, getCurrentDiagramData, markSaved, fitView, centerView })

onMounted(() => { setTimeout(fitView, 80) })
</script>

<style scoped>
.msi {
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal; font-size: 20px; line-height: 1;
  letter-spacing: normal; text-transform: none; display: inline-flex;
  align-items: center; justify-content: center; white-space: nowrap;
  direction: ltr; -webkit-font-smoothing: antialiased; flex-shrink: 0;
}

/* Root */
.fec-root { display: flex; height: 100%; overflow: hidden; }

/* ── Left Panel ────────────────────────────────────────────────── */
.fec-left {
  width: 240px; background: #fff; border-right: 1px solid #e2e8f0;
  display: flex; flex-direction: column; flex-shrink: 0;
  transition: width 0.22s ease; position: relative; overflow: hidden;
}
.fec-left--collapsed { width: 52px; }

.fec-toggle {
  position: absolute; top: 12px; right: -12px; z-index: 10;
  width: 24px; height: 24px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: #64748b; box-shadow: 0 1px 4px rgba(15,23,42,0.1); transition: all 0.15s;
}
.fec-toggle:hover { background: #eff6ff; color: #2563eb; }
.fec-toggle .msi { font-size: 13px; }
.fec-toggle--right { right: auto; left: -12px; }

.fec-left-inner { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 4px 0 12px; }
.fec-left-inner::-webkit-scrollbar { width: 4px; }
.fec-left-inner::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }

.fec-left-head {
  display: flex; align-items: center; gap: 7px;
  padding: 10px 14px 8px;
}
.fec-panel-label { font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.07em; flex: 1; }
.fec-diagram-tag {
  font-size: 9px; font-weight: 600; color: #2563eb;
  background: #eff6ff; border-radius: 4px; padding: 2px 6px; white-space: nowrap;
}

.fec-cat { margin-bottom: 1px; }
.fec-cat-hdr {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 14px; cursor: pointer; transition: background 0.12s;
}
.fec-cat-hdr:hover { background: #f8fafc; }
.fec-cat-hdr-l { display: flex; align-items: center; gap: 8px; }
.fec-cat-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.fec-cat-name { font-size: 11px; font-weight: 600; color: #334155; }
.fec-cat-arr { transition: transform 0.2s; }
.fec-cat-arr--open { transform: rotate(180deg); }

.fec-comp-list { padding: 2px 8px 4px; }
.fec-comp-item {
  display: flex; align-items: center; gap: 8px; padding: 6px 8px;
  border-radius: 7px; cursor: grab; transition: background 0.12s; user-select: none;
}
.fec-comp-item:hover { background: #f1f5f9; }
.fec-comp-icons { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 4px 0; }
.fec-comp-ico {
  width: 28px; height: 28px; border-radius: 7px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.fec-comp-ico--sm { cursor: grab; }
.fec-comp-ico--sm:hover { filter: brightness(0.9); }
.fec-comp-name { display: block; font-size: 12px; font-weight: 500; color: #1e293b; line-height: 1.3; }
.fec-comp-sub  { display: block; font-size: 10px; color: #94a3b8; }
.fec-no-tools  { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 32px 16px; text-align: center; font-size: 12px; color: #94a3b8; }

/* ── Canvas Area ──────────────────────────────────────────────── */
.fec-canvas-area {
  flex: 1; position: relative; overflow: hidden;
  background-color: #f1f5f9;
  background-image: radial-gradient(circle, #cbd5e1 1.2px, transparent 1.2px);
  background-size: 20px 20px;
  cursor: default; user-select: none;
}
.fec-canvas { position: absolute; top: 0; left: 0; }

/* Floating bar */
.fec-float-bar {
  position: absolute; display: flex; align-items: center; gap: 2px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 4px 8px; box-shadow: 0 4px 16px rgba(15,23,42,0.1); z-index: 20;
}
.fec-fbar-handle { padding: 0 4px; }
.fec-fsep { width: 1px; height: 18px; background: #e2e8f0; margin: 0 4px; }
.fec-tbtn {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border: none; background: transparent; border-radius: 6px; cursor: pointer;
  color: #64748b; transition: all 0.12s;
}
.fec-tbtn:hover { background: #f1f5f9; color: #2563eb; }
.fec-tbtn--on { background: #eff6ff; color: #2563eb; }
.fec-zoom-pct { font-size: 11px; font-weight: 600; color: #475569; min-width: 34px; text-align: center; }

/* Drop hint */
.fec-drop-hint {
  position: absolute; inset: 0; z-index: 15; pointer-events: none;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
  background: rgba(37,99,235,0.05); border: 2px dashed #2563eb; border-radius: 12px; margin: 12px;
  font-size: 15px; font-weight: 600; color: #2563eb;
}

/* Nodes */
.fec-node {
  position: absolute; width: 210px; min-height: 82px;
  border: 1.5px solid #e2e8f0; border-radius: 10px;
  background: #fff; box-shadow: 0 2px 8px rgba(15,23,42,0.07);
  cursor: pointer; transition: box-shadow 0.15s, border-color 0.15s; overflow: visible;
}
.fec-node:hover { box-shadow: 0 4px 16px rgba(15,23,42,0.12); border-color: #cbd5e1; }
.fec-node--sel  { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }
.fec-node-hdr {
  display: flex; align-items: center; gap: 7px; padding: 8px 10px;
  background: var(--nb); border-radius: 8px 8px 0 0; border-bottom: 1px solid rgba(0,0,0,0.05);
}
.fec-node-hdr-ico {
  width: 22px; height: 22px; border-radius: 5px;
  background: var(--nc); color: #fff;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.fec-node-lbl { font-size: 12px; font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.fec-node-bdy  { padding: 8px 10px; display: flex; flex-direction: column; gap: 3px; }
.fec-node-tag  { font-size: 10px; font-weight: 500; color: #64748b; background: #f1f5f9; border-radius: 4px; padding: 1px 5px; display: inline-block; max-width: fit-content; }
.fec-node-meta { font-size: 10px; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Ports */
.fec-port {
  position: absolute; width: 12px; height: 12px; border-radius: 50%;
  background: #fff; border: 2px solid #94a3b8; top: 50%; transform: translateY(-50%);
  cursor: crosshair; transition: border-color 0.12s, transform 0.12s; z-index: 2;
}
.fec-port:hover { border-color: #2563eb; transform: translateY(-50%) scale(1.3); }
.fec-port--in  { left: -6px; }
.fec-port--out { right: -6px; }

/* Connection action bar */
.fec-conn-bar {
  position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 12px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 16px;
  box-shadow: 0 4px 16px rgba(15,23,42,0.1); z-index: 20;
}
.fec-conn-lbl { font-size: 12px; color: #64748b; }
.fec-conn-del {
  display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 500;
  background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; cursor: pointer; transition: all 0.12s;
}
.fec-conn-del:hover { background: #fee2e2; }

/* ── Right Panel ──────────────────────────────────────────────── */
.fec-right {
  width: 272px; background: #fff; border-left: 1px solid #e2e8f0;
  display: flex; flex-shrink: 0; transition: width 0.22s ease;
  position: relative; overflow: hidden;
}
.fec-right--collapsed { width: 24px; }

.fec-right-inner { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 16px; display: flex; flex-direction: column; }
.fec-right-inner::-webkit-scrollbar { width: 4px; }
.fec-right-inner::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }

/* Properties */
.fec-props-hdr { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 16px; }
.fec-props-title { font-size: 13px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; }
.fec-props-sub { font-size: 11px; color: #94a3b8; margin-top: 1px; }
.fec-props-node-ico { width: 34px; height: 34px; border-radius: 8px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.fec-close-btn {
  margin-left: auto; flex-shrink: 0; width: 22px; height: 22px;
  border: none; background: transparent; cursor: pointer; border-radius: 5px;
  color: #94a3b8; display: flex; align-items: center; justify-content: center; transition: all 0.12s;
}
.fec-close-btn:hover { background: #f1f5f9; color: #475569; }

/* Form fields */
.fec-prop-g  { margin-bottom: 12px; }
.fec-prop-l  { display: block; font-size: 10px; font-weight: 700; color: #475569; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.05em; }
.fec-prop-i, .fec-prop-ta, .fec-prop-sel {
  width: 100%; box-sizing: border-box; padding: 7px 10px; font-size: 12px;
  border: 1px solid #e2e8f0; border-radius: 7px; background: #fff; outline: none;
  transition: border-color 0.15s, box-shadow 0.15s; font-family: inherit;
}
.fec-prop-i::placeholder, .fec-prop-ta::placeholder { color: #cbd5e1; }
.fec-prop-i:focus, .fec-prop-ta:focus, .fec-prop-sel:focus {
  border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.fec-prop-ta { resize: vertical; min-height: 60px; }
.fec-sel-wrap { position: relative; }
.fec-prop-sel { padding-right: 28px; appearance: none; cursor: pointer; }
.fec-sel-arr  { position: absolute; right: 7px; top: 50%; transform: translateY(-50%); color: #64748b; pointer-events: none; }

.fec-divider {
  display: flex; align-items: center; gap: 8px; margin: 4px 0 12px;
  font-size: 9px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em;
}
.fec-divider::before, .fec-divider::after { content: ''; flex: 1; height: 1px; background: #f1f5f9; }

.fec-flow-stats { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 7px; }
.fec-stat-row  { display: flex; align-items: center; gap: 7px; font-size: 12px; color: #64748b; }

.fec-node-del-wrap { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f1f5f9; }
.fec-node-del-btn {
  display: flex; align-items: center; gap: 6px; width: 100%; padding: 7px 12px;
  background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; border-radius: 8px;
  font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.12s;
}
.fec-node-del-btn:hover { background: #fee2e2; }
</style>
