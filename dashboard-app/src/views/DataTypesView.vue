<template>
  <div class="dt-view">
    <div class="page-header">
      <div>
        <h2 class="page-title">Tipos de Datos</h2>
        <p class="page-subtitle">Define los tipos SQL reutilizables para los campos de tus modelos dimensionales</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary btn-sm" @click="confirmReset" title="Restaurar tipos predeterminados">
          Restaurar defaults
        </button>
        <button class="btn btn-primary" @click="startAdd">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Nuevo tipo
        </button>
      </div>
    </div>

    <div class="card dt-table-wrap">
      <table class="dt-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Tipo base SQL</th>
            <th class="col-size">Tamaño / Precisión</th>
            <th class="col-sql">SQL completo</th>
            <th>Descripción</th>
            <th class="col-actions"></th>
          </tr>
        </thead>
        <tbody>
          <!-- New row form -->
          <tr v-if="adding" class="row-edit">
            <td>
              <input v-model="form.name" type="text" class="form-input cell-input" placeholder="Ej: Código" autofocus />
            </td>
            <td>
              <select v-model="form.baseType" class="form-input form-select cell-input" @change="onBaseTypeChange(form)">
                <option v-for="b in BASE_TYPES" :key="b.value" :value="b.value">{{ b.value }}</option>
              </select>
            </td>
            <td class="col-size">
              <div class="size-inputs">
                <input
                  v-if="baseMeta(form.baseType)?.hasSize"
                  v-model.number="form.size"
                  type="number" min="1" max="65535"
                  class="form-input cell-input size-input"
                  placeholder="Tam."
                />
                <span v-if="baseMeta(form.baseType)?.hasPrecision" class="size-sep">,</span>
                <input
                  v-if="baseMeta(form.baseType)?.hasPrecision"
                  v-model.number="form.precision"
                  type="number" min="0" max="30"
                  class="form-input cell-input size-input"
                  placeholder="Prec."
                />
                <span v-if="!baseMeta(form.baseType)?.hasSize" class="no-size">—</span>
              </div>
            </td>
            <td class="col-sql"><code class="sql-badge">{{ previewSql(form) }}</code></td>
            <td>
              <input v-model="form.description" type="text" class="form-input cell-input" placeholder="Descripción opcional" />
            </td>
            <td class="col-actions">
              <button class="btn btn-primary btn-sm" :disabled="!form.name.trim()" @click="saveAdd">Añadir</button>
              <button class="btn btn-secondary btn-sm" @click="cancelAdd">Cancelar</button>
            </td>
          </tr>

          <!-- Existing rows -->
          <tr v-for="dt in dtStore.allTypes" :key="dt.id" :class="{ 'row-edit': editingId === dt.id }">
            <!-- View mode -->
            <template v-if="editingId !== dt.id">
              <td class="cell-name">{{ dt.name }}</td>
              <td><span class="base-badge">{{ dt.baseType }}</span></td>
              <td class="col-size cell-size">{{ sizeLabel(dt) }}</td>
              <td class="col-sql"><code class="sql-badge">{{ dtStore.sqlOf(dt.id) }}</code></td>
              <td class="cell-desc">{{ dt.description || '—' }}</td>
              <td class="col-actions">
                <button class="btn-icon" data-tooltip="Editar" @click="startEditRow(dt)">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button class="btn-icon btn-icon-danger" data-tooltip="Eliminar" @click="confirmDelete(dt)">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                    <path d="M10 11v6M14 11v6"/>
                  </svg>
                </button>
              </td>
            </template>

            <!-- Edit mode -->
            <template v-else>
              <td>
                <input v-model="form.name" type="text" class="form-input cell-input" />
              </td>
              <td>
                <select v-model="form.baseType" class="form-input form-select cell-input" @change="onBaseTypeChange(form)">
                  <option v-for="b in BASE_TYPES" :key="b.value" :value="b.value">{{ b.value }}</option>
                </select>
              </td>
              <td class="col-size">
                <div class="size-inputs">
                  <input
                    v-if="baseMeta(form.baseType)?.hasSize"
                    v-model.number="form.size"
                    type="number" min="1" max="65535"
                    class="form-input cell-input size-input"
                    placeholder="Tam."
                  />
                  <span v-if="baseMeta(form.baseType)?.hasPrecision" class="size-sep">,</span>
                  <input
                    v-if="baseMeta(form.baseType)?.hasPrecision"
                    v-model.number="form.precision"
                    type="number" min="0" max="30"
                    class="form-input cell-input size-input"
                    placeholder="Prec."
                  />
                  <span v-if="!baseMeta(form.baseType)?.hasSize" class="no-size">—</span>
                </div>
              </td>
              <td class="col-sql"><code class="sql-badge">{{ previewSql(form) }}</code></td>
              <td>
                <input v-model="form.description" type="text" class="form-input cell-input" placeholder="Descripción" />
              </td>
              <td class="col-actions">
                <button class="btn btn-primary btn-sm" :disabled="!form.name.trim()" @click="saveEditRow(dt.id)">Guardar</button>
                <button class="btn btn-secondary btn-sm" @click="cancelEdit">Cancelar</button>
              </td>
            </template>
          </tr>

          <tr v-if="!dtStore.allTypes.length && !adding">
            <td colspan="6" class="empty-row">Sin tipos definidos. Haz clic en "Nuevo tipo" para añadir.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Delete confirm modal -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal card">
        <div class="modal-header">
          <h3>Eliminar tipo de dato</h3>
        </div>
        <div class="modal-body">
          <p>¿Eliminar <strong>{{ deleteTarget.name }}</strong> (<code>{{ dtStore.sqlOf(deleteTarget.id) }}</code>)?</p>
          <p class="modal-warn">Los campos que usen este tipo conservarán su referencia pero no se podrán resolver.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="deleteTarget = null">Cancelar</button>
          <button class="btn btn-danger" @click="doDelete">Eliminar</button>
        </div>
      </div>
    </div>

    <!-- Reset confirm modal -->
    <div v-if="showResetConfirm" class="modal-overlay" @click.self="showResetConfirm = false">
      <div class="modal card">
        <div class="modal-header"><h3>Restaurar tipos predeterminados</h3></div>
        <div class="modal-body">
          <p>Se reemplazarán todos los tipos actuales por los predeterminados. ¿Continuar?</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showResetConfirm = false">Cancelar</button>
          <button class="btn btn-danger" @click="doReset">Restaurar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDataTypeStore, BASE_TYPES, sqlTypeString } from '@/stores/dataTypes'
import { useUIStore } from '@/stores/ui'

const dtStore = useDataTypeStore()
const uiStore = useUIStore()

onMounted(() => uiStore.setBreadcrumbs(['Modelos', 'Tipos de datos']))

// ── Helpers ──────────────────────────────────────────────────
function baseMeta(baseType) {
  return BASE_TYPES.find(b => b.value === baseType)
}

function sizeLabel(dt) {
  const meta = baseMeta(dt.baseType)
  if (!meta?.hasSize || dt.size == null) return '—'
  if (meta.hasPrecision && dt.precision != null) return `${dt.size}, ${dt.precision}`
  return String(dt.size)
}

function previewSql(f) {
  return sqlTypeString({ baseType: f.baseType, size: f.size ?? null, precision: f.precision ?? null })
}

function emptyForm() {
  return { name: '', baseType: 'VARCHAR', size: 255, precision: null, description: '' }
}

function onBaseTypeChange(f) {
  const meta = baseMeta(f.baseType)
  if (!meta?.hasSize)      { f.size = null; f.precision = null }
  if (!meta?.hasPrecision) { f.precision = null }
  // Set sensible defaults
  if (meta?.hasSize && f.size == null) f.size = 255
}

// ── Add ───────────────────────────────────────────────────────
const adding = ref(false)
const form = ref(emptyForm())

function startAdd() {
  adding.value = true
  editingId.value = null
  form.value = emptyForm()
}

function saveAdd() {
  if (!form.value.name.trim()) return
  dtStore.addType({
    name: form.value.name.trim(),
    baseType: form.value.baseType,
    size: form.value.size ?? null,
    precision: form.value.precision ?? null,
    description: form.value.description.trim()
  })
  adding.value = false
  form.value = emptyForm()
}

function cancelAdd() {
  adding.value = false
  form.value = emptyForm()
}

// ── Edit ──────────────────────────────────────────────────────
const editingId = ref(null)

function startEditRow(dt) {
  adding.value = false
  editingId.value = dt.id
  form.value = {
    name: dt.name,
    baseType: dt.baseType,
    size: dt.size,
    precision: dt.precision,
    description: dt.description || ''
  }
}

function saveEditRow(id) {
  dtStore.updateType(id, {
    name: form.value.name.trim(),
    baseType: form.value.baseType,
    size: form.value.size ?? null,
    precision: form.value.precision ?? null,
    description: form.value.description.trim()
  })
  cancelEdit()
}

function cancelEdit() {
  editingId.value = null
  form.value = emptyForm()
}

// ── Delete ────────────────────────────────────────────────────
const deleteTarget = ref(null)

function confirmDelete(dt) { deleteTarget.value = dt }
function doDelete() {
  dtStore.deleteType(deleteTarget.value.id)
  deleteTarget.value = null
}

// ── Reset ─────────────────────────────────────────────────────
const showResetConfirm = ref(false)
function confirmReset() { showResetConfirm.value = true }
function doReset() {
  dtStore.resetToDefaults()
  showResetConfirm.value = false
  cancelEdit()
  cancelAdd()
}
</script>

<style scoped>
.dt-view { display: flex; flex-direction: column; gap: 20px; }

.page-header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;
}
.page-title { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); margin: 0; }
.header-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }

/* Table */
.dt-table-wrap { padding: 0; overflow: auto; }

.dt-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.dt-table th {
  background: #fafafa;
  padding: 10px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}

.dt-table td {
  padding: 8px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
  vertical-align: middle;
}

.dt-table tr:last-child td { border-bottom: none; }
.dt-table tr:hover td { background: #fafafa; }
.dt-table tr.row-edit td { background: #f0f7ff; }

.col-size  { width: 160px; }
.col-sql   { width: 180px; }
.col-actions { width: 120px; white-space: nowrap; }

.cell-name { font-weight: 600; }
.cell-size { color: var(--text-secondary); font-size: 12px; }
.cell-desc { color: var(--text-secondary); max-width: 240px; }

.base-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  font-family: monospace;
  background: #e6f7ff;
  color: #096dd9;
  padding: 2px 6px;
  border-radius: 4px;
}

.sql-badge {
  display: inline-block;
  font-size: 12px;
  font-family: monospace;
  background: #f6ffed;
  color: #389e0d;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #b7eb8f;
  white-space: nowrap;
}

.cell-input { height: 28px; font-size: 12px; padding: 3px 6px; width: 100%; }

.size-inputs { display: flex; align-items: center; gap: 4px; }
.size-input  { width: 68px; flex-shrink: 0; }
.size-sep    { color: var(--text-secondary); font-weight: 600; }
.no-size     { color: var(--text-secondary); }

.empty-row { text-align: center; color: var(--text-secondary); padding: 32px; font-style: italic; }

/* Action buttons */
.btn-icon { color: var(--text-secondary); }
.btn-icon:hover { color: var(--primary); background: var(--bg); }
.btn-icon-danger:hover { color: var(--error); background: #fff2f0; }

.col-actions { display: flex; gap: 4px; align-items: center; }

/* Modals */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal { width: 420px; max-width: 95vw; padding: 0; overflow: hidden; }
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
}
.modal-header h3 { font-size: 16px; font-weight: 600; color: var(--text); margin: 0; }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 10px; }
.modal-body p { margin: 0; font-size: 14px; color: var(--text); }
.modal-warn { font-size: 12px; color: #d46b08; background: #fff7e6; padding: 8px 10px; border-radius: 6px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px; border-top: 1px solid var(--border); background: #fafafa;
}
.btn-danger {
  background: var(--error); color: #fff; border: none;
  padding: 6px 16px; border-radius: var(--border-radius);
  cursor: pointer; font-size: 13px; font-weight: 500;
}
.btn-danger:hover { background: #cf1322; }
</style>
