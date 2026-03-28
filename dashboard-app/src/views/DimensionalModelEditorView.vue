<template>
  <div class="editor-view">
    <!-- Toolbar -->
    <div class="editor-toolbar card">
      <button class="btn btn-secondary btn-sm" @click="router.push('/models')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
        </svg>
        Volver
      </button>

      <div class="toolbar-title">
        <span v-if="!editingTitle" class="title-text" @dblclick="startEditTitle">
          {{ model?.name }}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="edit-hint">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </span>
        <input
          v-else
          ref="titleInput"
          v-model="editTitleValue"
          class="form-input title-edit-input"
          @blur="saveTitle"
          @keyup.enter="saveTitle"
          @keyup.escape="editingTitle = false"
        />
      </div>

      <div class="toolbar-actions">
        <!-- DDL / Import / Export -->
        <input ref="importInput" type="file" accept=".yaml,.yml" style="display:none" @change="handleImport" />
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Generar DDL/SQL" @click="handleGenerateDDL">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
        </button>
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Importar YAML" @click="importInput.click()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </button>
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Exportar YAML" @click="handleExport">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
        </button>

        <div class="toolbar-sep"></div>

        <button class="btn btn-secondary btn-sm" @click="addNode('fact')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Hecho
        </button>
        <button class="btn btn-secondary btn-sm" @click="addNode('dimension')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Dimensión
        </button>
      </div>
    </div>

    <!-- Canvas + Properties panel -->
    <div class="editor-body">
      <!-- Canvas -->
      <div
        ref="canvasEl"
        class="model-canvas"
        :class="{ 'dragging-field': !!dragField }"
        @click="onCanvasClick"
        @mousemove="onNodeDragMove"
      >
        <!-- SVG overlay for relationships + guide line -->
        <svg class="canvas-svg" :width="canvasSize.w" :height="canvasSize.h">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
            </marker>
            <marker id="arrowhead-key" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#52c41a"/>
            </marker>
          </defs>

          <!-- Relationships -->
          <g v-for="rel in model?.relationships" :key="rel.id">
            <line
              :x1="nodeCenter(rel.fromNodeId).x"
              :y1="nodeCenter(rel.fromNodeId).y"
              :x2="nodeCenter(rel.toNodeId).x"
              :y2="nodeCenter(rel.toNodeId).y"
              :stroke="selectedRel?.id === rel.id ? 'var(--primary)' : '#888'"
              stroke-width="2"
              marker-end="url(#arrowhead)"
              class="rel-line"
              @click.stop="selectRelationship(rel)"
            />
            <text
              :x="relMidpoint(rel).x"
              :y="relMidpoint(rel).y - 6"
              text-anchor="middle"
              class="rel-label"
              :fill="selectedRel?.id === rel.id ? 'var(--primary)' : '#555'"
              @click.stop="selectRelationship(rel)"
            >{{ rel.cardinality }}</text>
          </g>

          <!-- Field drag guide line -->
          <line
            v-if="dragField"
            :x1="dragField.startPos.x"
            :y1="dragField.startPos.y"
            :x2="mousePos.x"
            :y2="mousePos.y"
            stroke="#52c41a"
            stroke-width="2"
            stroke-dasharray="6 4"
            marker-end="url(#arrowhead-key)"
            pointer-events="none"
          />
        </svg>

        <!-- Nodes -->
        <div
          v-for="node in model?.nodes"
          :key="node.id"
          class="model-node"
          :class="[
            node.type,
            { selected: selectedNode?.id === node.id },
            { 'drop-target': dragField && node.type === 'fact' && node.id === dropTargetId }
          ]"
          :style="{ left: node.x + 'px', top: node.y + 'px' }"
          @click.stop="onNodeClick(node)"
          @mousedown.stop="startDrag(node, $event)"
        >
          <div class="node-header" :class="node.type">
            <span class="node-badge">{{ node.type === 'fact' ? 'HECHO' : 'DIM' }}</span>
            <span class="node-name">{{ node.name }}</span>
          </div>
          <div class="node-fields">
            <div
              v-for="f in node.fields"
              :key="f.id"
              class="node-field"
              :class="{ 'is-key': f.isKey, 'is-fk': f.isFk }"
            >
              <!-- Drag handle: only on key field of dimension nodes -->
              <span
                v-if="node.type === 'dimension' && f.isKey"
                class="key-drag-handle"
                title="Arrastrar para vincular con tabla de hechos"
                @mousedown.stop="startFieldDrag(node, f, $event)"
              >⠿</span>
              <span v-else class="field-icon-placeholder"></span>

              <span class="field-icon">
                <span v-if="f.isKey" class="key-icon" title="Llave primaria">🔑</span>
                <span v-else-if="f.isFk" class="fk-icon" title="Llave foránea">🔗</span>
                <span v-else>{{ fieldIcon(node.type, f.dataType) }}</span>
              </span>
              <span class="field-name">{{ f.name }}</span>
              <span class="field-type">{{ dtStore.getById(f.dataType)?.name ?? f.dataType }}</span>
            </div>

            <!-- Hint for dimensions without key -->
            <div v-if="node.type === 'dimension' && node.fields.length && !node.fields.some(f => f.isKey)" class="node-warn">
              ⚠ Sin llave definida
            </div>
            <div v-if="!node.fields.length" class="node-empty">Sin campos</div>
          </div>
        </div>

        <!-- Empty canvas hint -->
        <div v-if="!model?.nodes.length" class="canvas-hint">
          <p>Usa los botones de la barra para añadir tablas de <strong>Hecho</strong> o <strong>Dimensión</strong></p>
        </div>

        <!-- Field drag floating label -->
        <div
          v-if="dragField"
          class="drag-pill"
          :style="{ left: mousePos.x + 16 + 'px', top: mousePos.y - 12 + 'px' }"
        >
          🔑 {{ dragField.fieldName }}
          <span v-if="dropTargetId" class="drag-pill-hint">→ soltar para vincular</span>
        </div>
      </div>

      <!-- Properties panel -->
      <div v-if="selectedNode || selectedRel" class="props-panel card">
        <!-- Node properties -->
        <template v-if="selectedNode">
          <div class="props-header">
            <span class="props-type-badge" :class="selectedNode.type">
              {{ selectedNode.type === 'fact' ? 'Tabla de Hecho' : 'Dimensión' }}
            </span>
            <button class="btn-icon" @click="selectedNode = null; selectedRel = null">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="props-body">
            <div class="form-group">
              <label class="form-label">Nombre</label>
              <input
                :value="selectedNode.name"
                type="text"
                class="form-input"
                @change="updateNodeName($event.target.value)"
              />
            </div>

            <div class="props-section-title">Campos</div>
            <div class="fields-list">
              <div v-for="f in selectedNode.fields" :key="f.id" class="field-item">
                <!-- Key radio for dimension nodes -->
                <button
                  v-if="selectedNode.type === 'dimension'"
                  class="key-toggle"
                  :class="{ active: f.isKey }"
                  :title="f.isKey ? 'Llave primaria' : 'Marcar como llave'"
                  @click="setKeyField(f.id)"
                >🔑</button>
                <input
                  :value="f.name"
                  type="text"
                  class="form-input field-name-input"
                  placeholder="Nombre"
                  @change="updateField(f.id, 'name', $event.target.value)"
                />
                <select
                  :value="f.dataType"
                  class="form-input form-select field-type-select"
                  @change="updateField(f.id, 'dataType', $event.target.value)"
                >
                  <option v-for="dt in dtStore.allTypes" :key="dt.id" :value="dt.id">
                    {{ dt.name }}
                  </option>
                </select>
                <button class="btn-icon field-del-btn" @click="deleteField(f.id)">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="selectedNode.type === 'dimension' && !selectedNode.fields.some(f => f.isKey)" class="props-warn">
              ⚠ Marca un campo como llave (🔑) para poder arrastrar relaciones
            </div>

            <button class="btn btn-secondary btn-sm add-field-btn" @click="addField">
              + Añadir campo
            </button>

            <div class="props-divider"></div>
            <button class="btn btn-sm btn-danger-outline" @click="deleteNodeConfirm">
              Eliminar tabla
            </button>
          </div>
        </template>

        <!-- Relationship properties -->
        <template v-if="selectedRel">
          <div class="props-header">
            <span class="props-type-badge rel">Relación</span>
            <button class="btn-icon" @click="selectedRel = null">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="props-body">
            <div class="rel-nodes-info">
              <span class="rel-node-tag">{{ nodeName(selectedRel.fromNodeId) }}</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
              <span class="rel-node-tag">{{ nodeName(selectedRel.toNodeId) }}</span>
            </div>

            <div class="form-group">
              <label class="form-label">Cardinalidad</label>
              <select
                :value="selectedRel.cardinality"
                class="form-input form-select"
                @change="updateRelCardinality($event.target.value)"
              >
                <option value="1:1">1:1 — Uno a uno</option>
                <option value="1:N">1:N — Uno a muchos</option>
                <option value="N:N">N:N — Muchos a muchos</option>
              </select>
            </div>

            <div class="props-divider"></div>
            <button class="btn btn-sm btn-danger-outline" @click="deleteRelationship">
              Eliminar relación
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDimensionalModelStore } from '@/stores/dimensionalModel'
import { useDataTypeStore } from '@/stores/dataTypes'
import { useUIStore } from '@/stores/ui'
import yaml from 'js-yaml'

const router = useRouter()
const route = useRoute()
const modelStore = useDimensionalModelStore()
const dtStore = useDataTypeStore()
const uiStore = useUIStore()

const modelId = route.params.id
const model = computed(() => modelStore.getModel(modelId))

// ── Title editing ────────────────────────────────────────────
const editingTitle = ref(false)
const editTitleValue = ref('')
const titleInput = ref(null)

function startEditTitle() {
  editTitleValue.value = model.value?.name || ''
  editingTitle.value = true
  nextTick(() => titleInput.value?.focus())
}
function saveTitle() {
  if (editTitleValue.value.trim()) modelStore.updateModel(modelId, { name: editTitleValue.value.trim() })
  editingTitle.value = false
}

// ── Import / Export ──────────────────────────────────────────
const importInput = ref(null)

function handleExport() {
  if (!model.value) return
  const doc = {
    name: model.value.name,
    description: model.value.description,
    nodes: model.value.nodes.map(n => ({
      id: n.id, type: n.type, name: n.name, x: n.x, y: n.y,
      fields: n.fields.map(f => ({
        id: f.id, name: f.name, description: f.description,
        dataType: f.dataType, isKey: !!f.isKey, isFk: !!f.isFk
      }))
    })),
    relationships: model.value.relationships.map(r => ({
      id: r.id, fromNodeId: r.fromNodeId, toNodeId: r.toNodeId, cardinality: r.cardinality
    }))
  }
  const content = yaml.dump(doc, { indent: 2, lineWidth: 120 })
  const slug = model.value.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'modelo'
  const blob = new Blob([content], { type: 'text/yaml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${slug}.yaml`; a.click()
  URL.revokeObjectURL(url)
}

function handleImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const doc = yaml.load(ev.target.result)
      if (!doc || typeof doc !== 'object') throw new Error('Formato inválido')
      modelStore.updateModel(modelId, {
        name: doc.name || model.value.name,
        description: doc.description ?? model.value.description
      })
      const m = modelStore.getModel(modelId)
      if (!m) return
      m.nodes = Array.isArray(doc.nodes) ? doc.nodes : []
      m.relationships = Array.isArray(doc.relationships) ? doc.relationships : []
      modelStore.persist()
      selectedNode.value = null; selectedRel.value = null
    } catch (err) {
      alert(`Error al importar: ${err.message}`)
    } finally {
      e.target.value = ''
    }
  }
  reader.readAsText(file)
}

// ── DDL Generation ───────────────────────────────────────────
function toSqlName(s) {
  return s.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
}

// Normalize a raw type string to a valid uppercase PostgreSQL type
function normalizePgType(raw) {
  if (!raw) return 'VARCHAR(255)'
  const map = {
    'integer': 'INTEGER', 'int': 'INTEGER', 'int4': 'INTEGER',
    'bigint': 'BIGINT', 'int8': 'BIGINT', 'smallint': 'SMALLINT', 'int2': 'SMALLINT',
    'serial': 'SERIAL', 'bigserial': 'BIGSERIAL',
    'numeric': 'NUMERIC', 'decimal': 'DECIMAL', 'money': 'MONEY',
    'real': 'REAL', 'double precision': 'DOUBLE PRECISION', 'float8': 'DOUBLE PRECISION',
    'varchar': 'VARCHAR(255)', 'character varying': 'VARCHAR(255)',
    'char': 'CHAR(1)', 'character': 'CHAR(1)', 'text': 'TEXT',
    'boolean': 'BOOLEAN', 'bool': 'BOOLEAN',
    'date': 'DATE', 'time': 'TIME',
    'timestamp': 'TIMESTAMP', 'timestamp without time zone': 'TIMESTAMP',
    'timestamptz': 'TIMESTAMPTZ', 'timestamp with time zone': 'TIMESTAMPTZ',
    'uuid': 'UUID', 'jsonb': 'JSONB', 'json': 'JSON', 'bytea': 'BYTEA',
  }
  return map[raw.toLowerCase()] ?? raw.toUpperCase()
}

// Resolve PostgreSQL column type from a model field.
// SERIAL/BIGSERIAL are auto-increment sequences — invalid for FK columns.
function pgTypeForCol(field) {
  const dt = dtStore.getById(field.dataType)
  if (dt) {
    if (field.isFk) {
      if (dt.baseType === 'SERIAL')    return 'INTEGER'
      if (dt.baseType === 'BIGSERIAL') return 'BIGINT'
    }
    return dtStore.sqlOf(field.dataType)
  }
  // Fallback for legacy raw-string dataType values
  return normalizePgType(field.dataType)
}

function handleGenerateDDL() {
  if (!model.value) return
  const m = model.value
  const lines = []

  // Header
  lines.push(`-- ============================================================`)
  lines.push(`-- Modelo Dimensional: ${m.name}`)
  if (m.description) lines.push(`-- ${m.description}`)
  lines.push(`-- Generado: ${new Date().toISOString()}`)
  lines.push(`-- ============================================================`)
  lines.push('')

  // Separate dimensions and facts
  const dims  = m.nodes.filter(n => n.type === 'dimension')
  const facts = m.nodes.filter(n => n.type === 'fact')

  // Map nodeId → sql table name (needed for FK references)
  const tableOf = {}
  m.nodes.forEach(n => { tableOf[n.id] = toSqlName(n.name) })

  // Helper: build relationship lookup dim→fact
  // rel.fromNodeId = dim, rel.toNodeId = fact (as created by drag-drop)
  const relsByDim = {}
  m.relationships.forEach(r => {
    const fromNode = m.nodes.find(n => n.id === r.fromNodeId)
    if (fromNode?.type === 'dimension') {
      if (!relsByDim[r.fromNodeId]) relsByDim[r.fromNodeId] = []
      relsByDim[r.fromNodeId].push(r)
    }
  })

  // 1. DIMENSION tables
  if (dims.length) {
    lines.push('-- ------------------------------------------------------------')
    lines.push('-- TABLAS DE DIMENSIONES')
    lines.push('-- ------------------------------------------------------------')
    lines.push('')
  }

  dims.forEach(node => {
    const tbl = tableOf[node.id]
    const keyField = node.fields.find(f => f.isKey)
    lines.push(`CREATE TABLE ${tbl} (`)

    const colLines = node.fields.map(f => {
      const col  = toSqlName(f.name)
      const type = pgTypeForCol(f)
      const pk   = f.isKey ? ' PRIMARY KEY' : ''
      const cmt  = f.description ? `  -- ${f.description}` : ''
      return `    ${col.padEnd(30)} ${(type + pk).padEnd(30)}${cmt}`
    })

    if (!colLines.length) colLines.push('    -- (sin campos definidos)')
    lines.push(colLines.join(',\n'))
    lines.push(');')
    lines.push('')
  })

  // 2. FACT tables
  if (facts.length) {
    lines.push('-- ------------------------------------------------------------')
    lines.push('-- TABLAS DE HECHOS')
    lines.push('-- ------------------------------------------------------------')
    lines.push('')
  }

  facts.forEach(node => {
    const tbl = tableOf[node.id]
    lines.push(`CREATE TABLE ${tbl} (`)

    // Collect FK constraints to emit after columns
    const fkConstraints = []

    const colLines = node.fields.map(f => {
      const col  = toSqlName(f.name)
      const type = pgTypeForCol(f)
      const cmt  = f.description ? `  -- ${f.description}` : ''

      // If this is a FK field, resolve which dim table / key column it references
      if (f.isFk && f.description) {
        // description format: "FK → DimName.fieldName"
        const match = f.description.match(/FK → (.+)\.(.+)/)
        if (match) {
          const dimNode = m.nodes.find(n => n.name === match[1] && n.type === 'dimension')
          if (dimNode) {
            const refTbl = tableOf[dimNode.id]
            const refCol = toSqlName(match[2])
            fkConstraints.push(
              `    CONSTRAINT fk_${tbl}_${col} FOREIGN KEY (${col}) REFERENCES ${refTbl}(${refCol})`
            )
          }
        }
      }

      return `    ${col.padEnd(30)} ${type.padEnd(30)}${cmt}`
    })

    if (!colLines.length) colLines.push('    -- (sin campos definidos)')

    const allLines = [...colLines, ...fkConstraints]
    lines.push(allLines.join(',\n'))
    lines.push(');')
    lines.push('')
  })

  // 3. RELATIONSHIP comments (for N:N or non-FK rels)
  const nonFkRels = m.relationships.filter(r => {
    const from = m.nodes.find(n => n.id === r.fromNodeId)
    return r.cardinality === 'N:N' || !from || from.type !== 'dimension'
  })
  if (nonFkRels.length) {
    lines.push('-- ------------------------------------------------------------')
    lines.push('-- RELACIONES ADICIONALES')
    lines.push('-- ------------------------------------------------------------')
    nonFkRels.forEach(r => {
      lines.push(`-- ${tableOf[r.fromNodeId] || r.fromNodeId} [${r.cardinality}] ${tableOf[r.toNodeId] || r.toNodeId}`)
    })
    lines.push('')
  }

  const content = lines.join('\n')
  const slug = m.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'modelo'
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${slug}.ddl`; a.click()
  URL.revokeObjectURL(url)
}

// ── Canvas ───────────────────────────────────────────────────
const canvasEl = ref(null)

const canvasSize = computed(() => {
  const nodes = model.value?.nodes || []
  const maxX = Math.max(900, ...nodes.map(n => n.x + 240))
  const maxY = Math.max(600, ...nodes.map(n => n.y + nodeHeight(n) + 60))
  return { w: maxX, h: maxY }
})

function canvasPos(clientX, clientY) {
  const rect = canvasEl.value.getBoundingClientRect()
  return {
    x: clientX - rect.left + canvasEl.value.scrollLeft,
    y: clientY - rect.top + canvasEl.value.scrollTop
  }
}

// ── Selection ────────────────────────────────────────────────
const selectedNode = ref(null)
const selectedRel = ref(null)

// ── Node drag state ──────────────────────────────────────────
const dragging = ref(null)  // { nodeId, startX, startY, origX, origY }

// ── Field drag state ─────────────────────────────────────────
// Active when user drags the 🔑 handle from a dimension key field
const dragField = ref(null)  // { nodeId, nodeName, fieldId, fieldName, startPos:{x,y} }
const dropTargetId = ref(null)
const mousePos = ref({ x: 0, y: 0 })

// ── Lifecycle ────────────────────────────────────────────────
onMounted(() => {
  if (!model.value) { router.push('/models'); return }
  uiStore.setBreadcrumbs(['Modelos', model.value.name])
  // Global listeners capture mouse events even outside the component
  document.addEventListener('mousemove', onGlobalMouseMove)
  document.addEventListener('mouseup', onGlobalMouseUp)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onGlobalMouseMove)
  document.removeEventListener('mouseup', onGlobalMouseUp)
})

watch(() => model.value?.name, name => { if (name) uiStore.setBreadcrumbs(['Modelos', name]) })

// ── Geometry helpers ─────────────────────────────────────────
const NODE_WIDTH = 200

function nodeHeight(node) {
  const warn = node?.type === 'dimension' && node?.fields?.length > 0 && !node?.fields?.some(f => f.isKey)
  return 40 + (node?.fields?.length || 0) * 28 + 8 + (warn ? 24 : 0)
}

function nodeCenter(nodeId) {
  const node = model.value?.nodes.find(n => n.id === nodeId)
  if (!node) return { x: 0, y: 0 }
  return { x: node.x + NODE_WIDTH / 2, y: node.y + nodeHeight(node) / 2 }
}

function relMidpoint(rel) {
  const a = nodeCenter(rel.fromNodeId), b = nodeCenter(rel.toNodeId)
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }
}

function nodeName(nodeId) {
  return model.value?.nodes.find(n => n.id === nodeId)?.name || nodeId
}

function keyFieldStartPos(dimNode, field) {
  const idx = dimNode.fields.findIndex(f => f.id === field.id)
  return { x: dimNode.x + NODE_WIDTH, y: dimNode.y + 44 + idx * 28 }
}

function factNodeAt(pos) {
  return model.value?.nodes.find(n => {
    if (n.type !== 'fact') return false
    const h = nodeHeight(n)
    return pos.x >= n.x && pos.x <= n.x + NODE_WIDTH && pos.y >= n.y && pos.y <= n.y + h
  }) || null
}

function fieldIcon(nodeType, dataType) {
  if (nodeType === 'fact') return { integer: '#', decimal: '~', currency: '$', percentage: '%' }[dataType] || '#'
  return { string: 'A', date: '📅', boolean: '?', integer: '#' }[dataType] || 'A'
}

// ── Add node ─────────────────────────────────────────────────
let nodeCounter = 0
function addNode(type) {
  const offset = nodeCounter++ * 30
  const node = modelStore.addNode(modelId, {
    type,
    name: type === 'fact' ? 'Nueva tabla de hechos' : 'Nueva dimensión',
    x: 60 + offset, y: 60 + offset
  })
  selectedRel.value = null
  selectedNode.value = node
}

// ── Node drag ────────────────────────────────────────────────
function startDrag(node, e) {
  if (dragField.value) return
  e.preventDefault()
  dragging.value = { nodeId: node.id, startX: e.clientX, startY: e.clientY, origX: node.x, origY: node.y }
}

// Handles only node drag (called from canvas @mousemove to update node position)
function onNodeDragMove(e) {
  if (!dragging.value) return
  const dx = e.clientX - dragging.value.startX
  const dy = e.clientY - dragging.value.startY
  modelStore.updateNode(modelId, dragging.value.nodeId, {
    x: Math.max(0, dragging.value.origX + dx),
    y: Math.max(0, dragging.value.origY + dy)
  })
}

// ── Field drag start ─────────────────────────────────────────
function startFieldDrag(dimNode, field, e) {
  if (!field.isKey) return
  e.preventDefault()
  e.stopPropagation()   // prevent startDrag on parent node div
  dragging.value = null // clear any node drag

  if (!canvasEl.value) return
  const pos = canvasPos(e.clientX, e.clientY)
  dragField.value = {
    nodeId: dimNode.id,
    nodeName: dimNode.name,
    fieldId: field.id,
    fieldName: field.name,
    startPos: keyFieldStartPos(dimNode, field)
  }
  mousePos.value = pos
}

// ── Global mouse move (field drag tracking) ──────────────────
function onGlobalMouseMove(e) {
  if (!dragField.value || !canvasEl.value) return
  const pos = canvasPos(e.clientX, e.clientY)
  mousePos.value = pos
  // Highlight fact node under cursor
  const target = factNodeAt(pos)
  dropTargetId.value = target?.id || null
}

// ── Global mouse up ───────────────────────────────────────────
function onGlobalMouseUp(e) {
  if (dragField.value && canvasEl.value) {
    const pos = canvasPos(e.clientX, e.clientY)
    const factNode = factNodeAt(pos)
    if (factNode) handleFieldDrop(factNode)
  }
  dragField.value = null
  dropTargetId.value = null
  dragging.value = null
}

// ── Drop: link dim key → fact ─────────────────────────────────
function handleFieldDrop(factNode) {
  const dimNode = model.value?.nodes.find(n => n.id === dragField.value.nodeId)
  if (!dimNode) return

  const toSnake = s => s.toLowerCase().trim().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
  const fkName = `${toSnake(dimNode.name)}_${toSnake(dragField.value.fieldName)}`

  // Add FK field if not present
  if (!factNode.fields.find(f => f.name === fkName)) {
    // Match key field type but SERIAL→INTEGER and BIGSERIAL→BIGINT (FK cols can't be sequences)
    const dimKeyField = dimNode.fields.find(f => f.isKey)
    let fkDataType
    if (dimKeyField) {
      const keyDt = dtStore.getById(dimKeyField.dataType)
      if (keyDt?.baseType === 'SERIAL') {
        fkDataType = dtStore.allTypes.find(t => t.baseType === 'INTEGER')?.id ?? 'dt-int'
      } else if (keyDt?.baseType === 'BIGSERIAL') {
        fkDataType = dtStore.allTypes.find(t => t.baseType === 'BIGINT')?.id ?? 'dt-bigint'
      } else {
        fkDataType = dimKeyField.dataType
      }
    } else {
      fkDataType = dtStore.allTypes.find(t => t.id === 'dt-int')?.id
               ?? dtStore.allTypes.find(t => t.baseType === 'INTEGER')?.id
               ?? dtStore.allTypes[0]?.id
    }
    modelStore.addField(modelId, factNode.id, {
      name: fkName,
      description: `FK → ${dimNode.name}.${dragField.value.fieldName}`,
      dataType: fkDataType,
      isFk: true
    })
  }

  // Create relationship if not already exists
  const relExists = model.value?.relationships.some(
    r => (r.fromNodeId === dimNode.id && r.toNodeId === factNode.id) ||
         (r.fromNodeId === factNode.id && r.toNodeId === dimNode.id)
  )
  if (!relExists) {
    modelStore.addRelationship(modelId, {
      fromNodeId: dimNode.id,
      toNodeId: factNode.id,
      cardinality: '1:N'
    })
  }
}

// ── Node click / selection ────────────────────────────────────
function onNodeClick(node) {
  selectedNode.value = model.value?.nodes.find(n => n.id === node.id) || null
  selectedRel.value = null
}

function selectRelationship(rel) {
  selectedRel.value = model.value?.relationships.find(r => r.id === rel.id) || null
  selectedNode.value = null
}

function onCanvasClick() {
  selectedNode.value = null
  selectedRel.value = null
}

// ── Node property updates ─────────────────────────────────────
function refreshSelectedNode() {
  if (!selectedNode.value) return
  selectedNode.value = model.value?.nodes.find(n => n.id === selectedNode.value.id) || null
}

function updateNodeName(name) {
  if (!selectedNode.value) return
  modelStore.updateNode(modelId, selectedNode.value.id, { name })
  refreshSelectedNode()
}

function addField() {
  if (!selectedNode.value) return
  const isDim = selectedNode.value.type === 'dimension'
  const autoKey = isDim && selectedNode.value.fields.length === 0
  // Pick sensible default type IDs from store, fallback to first available
  const allTypes = dtStore.allTypes
  const defaultDimKey  = allTypes.find(t => t.id === 'dt-serial') ?? allTypes.find(t => t.baseType === 'SERIAL') ?? allTypes[0]
  const defaultDimText = allTypes.find(t => t.id === 'dt-varchar') ?? allTypes.find(t => t.baseType === 'VARCHAR') ?? allTypes[0]
  const defaultFact    = allTypes.find(t => t.id === 'dt-numeric') ?? allTypes.find(t => t.baseType === 'NUMERIC') ?? allTypes[0]
  const defaultType = autoKey ? defaultDimKey?.id : (isDim ? defaultDimText?.id : defaultFact?.id)
  modelStore.addField(modelId, selectedNode.value.id, {
    name: autoKey ? 'id' : 'nuevo_campo',
    description: '',
    dataType: defaultType ?? (allTypes[0]?.id ?? 'dt-int'),
    isKey: autoKey
  })
  refreshSelectedNode()
}

function setKeyField(fieldId) {
  if (!selectedNode.value) return
  modelStore.setKeyField(modelId, selectedNode.value.id, fieldId)
  refreshSelectedNode()
}

function updateField(fieldId, key, value) {
  if (!selectedNode.value) return
  modelStore.updateField(modelId, selectedNode.value.id, fieldId, { [key]: value })
  refreshSelectedNode()
}

function deleteField(fieldId) {
  if (!selectedNode.value) return
  modelStore.deleteField(modelId, selectedNode.value.id, fieldId)
  refreshSelectedNode()
}

function deleteNodeConfirm() {
  if (!selectedNode.value) return
  if (!confirm(`¿Eliminar "${selectedNode.value.name}" y todas sus relaciones?`)) return
  modelStore.deleteNode(modelId, selectedNode.value.id)
  selectedNode.value = null
}

// ── Relationship updates ──────────────────────────────────────
function updateRelCardinality(cardinality) {
  if (!selectedRel.value) return
  modelStore.updateRelationship(modelId, selectedRel.value.id, { cardinality })
  selectedRel.value = model.value?.relationships.find(r => r.id === selectedRel.value.id) || null
}

function deleteRelationship() {
  if (!selectedRel.value) return
  modelStore.deleteRelationship(modelId, selectedRel.value.id)
  selectedRel.value = null
}
</script>

<style scoped>
.editor-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0;
  user-select: none;
}

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  flex-shrink: 0;
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.toolbar-title { flex: 1; min-width: 0; display: flex; align-items: center; }
.title-text {
  font-size: 16px; font-weight: 600; color: var(--text);
  cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.edit-hint { color: var(--text-secondary); opacity: 0.5; }
.title-text:hover .edit-hint { opacity: 1; }
.title-edit-input { font-size: 15px; font-weight: 600; max-width: 300px; }
.toolbar-actions { display: flex; gap: 6px; flex-shrink: 0; flex-wrap: wrap; align-items: center; }
.btn-icon-only { width: 30px; padding: 0; justify-content: center; }
.toolbar-sep { width: 1px; height: 20px; background: var(--border); margin: 0 2px; flex-shrink: 0; }

/* Editor body */
.editor-body {
  display: flex; flex: 1; min-height: 0;
  background: #f5f5f5;
  border: 1px solid var(--border); border-top: none;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

/* Canvas */
.model-canvas {
  flex: 1;
  position: relative;
  overflow: auto;
  min-height: 500px;
}
.model-canvas.dragging-field { cursor: crosshair; }

.canvas-svg {
  position: absolute; top: 0; left: 0;
  pointer-events: none;
}
.canvas-svg .rel-line { pointer-events: stroke; cursor: pointer; }
.canvas-svg .rel-label { font-size: 12px; font-weight: 600; pointer-events: all; cursor: pointer; }

.canvas-hint {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  pointer-events: none;
}
.canvas-hint p {
  font-size: 14px; color: var(--text-secondary);
  text-align: center; max-width: 320px; line-height: 1.6;
  background: rgba(255,255,255,0.7); padding: 16px 24px; border-radius: 8px;
}

/* Floating drag pill */
.drag-pill {
  position: absolute;
  background: #52c41a;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  z-index: 10;
}
.drag-pill-hint { font-weight: 400; opacity: 0.85; margin-left: 4px; }

/* Nodes */
.model-node {
  position: absolute;
  width: 200px;
  background: #fff;
  border-radius: 8px;
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  cursor: move;
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
}
.model-node:hover { box-shadow: var(--shadow-md); }
.model-node.selected { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(24,144,255,0.2); }
.model-node.drop-target { border-color: #52c41a; box-shadow: 0 0 0 3px rgba(82,196,26,0.35); }

.node-header {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 10px;
  font-size: 13px; font-weight: 600; color: #fff;
  cursor: move;
}
.node-header.fact { background: var(--primary); }
.node-header.dimension { background: #52c41a; }

.node-badge {
  font-size: 10px; font-weight: 700;
  background: rgba(255,255,255,0.25);
  padding: 1px 5px; border-radius: 3px; letter-spacing: 0.5px; flex-shrink: 0;
}
.node-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.node-fields { padding: 6px 0; }

.node-field {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 8px 3px 4px;
  font-size: 12px; color: var(--text);
  border-bottom: 1px solid var(--border);
  min-height: 28px;
}
.node-field:last-child { border-bottom: none; }
.node-field.is-key { background: #f6ffed; }
.node-field.is-fk { background: #e6f7ff; }

/* Drag handle for key field */
.key-drag-handle {
  flex-shrink: 0;
  width: 18px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #52c41a;
  cursor: grab;
  border-radius: 3px;
  opacity: 0.5;
  transition: opacity 0.15s, background 0.15s;
  user-select: none;
}
.key-drag-handle:hover { opacity: 1; background: rgba(82,196,26,0.12); }
.key-drag-handle:active { cursor: grabbing; opacity: 1; }
.field-icon-placeholder { flex-shrink: 0; width: 18px; }

.field-icon { flex-shrink: 0; width: 16px; text-align: center; font-size: 11px; }
.key-icon, .fk-icon { font-size: 11px; }
.field-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.field-type { font-size: 10px; color: var(--text-secondary); flex-shrink: 0; }

.node-empty { padding: 6px 10px; font-size: 12px; color: var(--text-secondary); font-style: italic; }
.node-warn { padding: 4px 10px; font-size: 11px; color: #d46b08; background: #fff7e6; }

/* Properties panel */
.props-panel {
  width: 290px; flex-shrink: 0;
  border-radius: 0; border: none; border-left: 1px solid var(--border);
  display: flex; flex-direction: column;
  overflow-y: auto; background: #fff;
}
.props-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.props-type-badge {
  font-size: 11px; font-weight: 700;
  padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px; color: #fff;
}
.props-type-badge.fact { background: var(--primary); }
.props-type-badge.dimension { background: #52c41a; }
.props-type-badge.rel { background: #722ed1; }

.props-body { padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; flex: 1; }

.props-section-title {
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.6px; margin-top: 4px;
}

.props-warn {
  font-size: 12px; color: #d46b08;
  background: #fff7e6; padding: 8px 10px; border-radius: 6px; line-height: 1.4;
}

.fields-list { display: flex; flex-direction: column; gap: 6px; }

.field-item { display: flex; align-items: center; gap: 4px; }

/* Key toggle button */
.key-toggle {
  flex-shrink: 0;
  width: 24px; height: 24px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  opacity: 0.35;
  transition: all 0.15s;
  padding: 0;
}
.key-toggle:hover { opacity: 0.7; border-color: #52c41a; }
.key-toggle.active { opacity: 1; background: #f6ffed; border-color: #52c41a; }

.field-name-input { flex: 1; min-width: 0; font-size: 12px; padding: 4px 6px; height: 28px; }
.field-type-select { width: 86px; flex-shrink: 0; font-size: 12px; padding: 4px 4px; height: 28px; }
.field-del-btn { flex-shrink: 0; color: var(--text-secondary); }
.field-del-btn:hover { color: var(--error); background: #fff2f0; }

.add-field-btn { align-self: flex-start; font-size: 12px; }
.props-divider { height: 1px; background: var(--border); margin: 4px 0; }

.btn-danger-outline {
  background: transparent; color: var(--error); border: 1px solid var(--error);
  padding: 5px 12px; border-radius: var(--border-radius);
  cursor: pointer; font-size: 12px; font-weight: 500; transition: background 0.15s;
}
.btn-danger-outline:hover { background: #fff2f0; }

.rel-nodes-info {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; background: var(--bg); border-radius: 6px; font-size: 13px;
}
.rel-node-tag {
  flex: 1; text-align: center; font-weight: 600; color: var(--text);
  font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 12px; font-weight: 500; color: var(--text); }
</style>
