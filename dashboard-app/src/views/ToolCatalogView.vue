<template>
  <div class="min-h-[calc(100vh-64px)] p-8">
    <!-- Header -->
    <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
      <div class="space-y-1">
        <span class="text-xs font-semibold tracking-wider text-blue-600 uppercase">Data Integration</span>
        <h1 class="tc-h1">Catálogo de Herramientas</h1>
        <p class="tc-sub page-subtitle max-w-2xl">Define y gestiona las herramientas disponibles en el editor visual. Cada herramienta especifica a qué tipos de diagrama aplica.</p>
      </div>
      <button class="btn btn-primary" @click="openNew">
        <span class="msym">add</span>Nueva Herramienta
      </button>
    </div>

    <!-- Filters -->
    <div class="max-w-[1600px] mx-auto mb-5 flex items-center gap-3 flex-wrap">
      <div class="tc-search-wrap">
        <span class="msym tc-search-ico">search</span>
        <input v-model="search" type="text" placeholder="Buscar herramientas..." class="tc-search-in" />
      </div>
      <div class="tc-sel-wrap">
        <select v-model="filterCat" class="tc-filter-sel">
          <option value="">Todas las categorías</option>
          <option v-for="(meta, key) in CAT_META" :key="key" :value="key">{{ meta.label }}</option>
        </select>
        <span class="msym tc-sel-arr">expand_more</span>
      </div>
      <div class="tc-sel-wrap">
        <select v-model="filterDiagram" class="tc-filter-sel">
          <option value="">Todos los diagramas</option>
          <option v-for="dt in catalog.diagramTypes" :key="dt.id" :value="dt.id">{{ dt.name }}</option>
        </select>
        <span class="msym tc-sel-arr">expand_more</span>
      </div>
      <span class="text-sm page-subtitle ml-auto">{{ filteredTools.length }} herramienta(s)</span>
    </div>

    <!-- Table -->
    <div class="max-w-[1600px] mx-auto">
      <div class="tc-table-wrap">
        <table class="tc-table">
          <thead>
            <tr>
              <th>Herramienta</th>
              <th>Categoría</th>
              <th>Tipos de Diagrama</th>
              <th>Propiedades</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredTools.length === 0">
              <td colspan="5">
                <div class="tc-empty"><span class="msym" style="font-size:36px;color:#cbd5e1">construction</span><span>No se encontraron herramientas</span></div>
              </td>
            </tr>
            <tr v-for="tool in filteredTools" :key="tool.id" class="tc-row">
              <td>
                <div class="tc-tool-cell">
                  <div class="tc-tool-ico" :style="{ background: catMeta(tool.category).bg, color: catMeta(tool.category).color }">
                    <span class="msym" style="font-size:16px">{{ tool.icon }}</span>
                  </div>
                  <div>
                    <p class="tc-tool-name">{{ tool.name }}</p>
                    <p class="tc-tool-sub">{{ tool.description }}</p>
                  </div>
                </div>
              </td>
              <td>
                <span class="tc-cat-badge" :style="{ background: catMeta(tool.category).bg, color: catMeta(tool.category).color }">
                  {{ catMeta(tool.category).label }}
                </span>
              </td>
              <td>
                <div class="tc-diagram-pills">
                  <span v-for="dtId in (tool.applicable_diagram_types || [])" :key="dtId" class="tc-dt-pill">
                    {{ diagramLabel(dtId) }}
                  </span>
                  <span v-if="!(tool.applicable_diagram_types || []).length" class="tc-none">—</span>
                </div>
              </td>
              <td>
                <span class="tc-prop-count">{{ Object.keys(tool.prop_defs || {}).length }} campos</span>
              </td>
              <td>
                <div class="tc-row-actions">
                  <button class="tc-action" title="Editar" @click="openEdit(tool)"><span class="msym" style="font-size:17px">edit</span></button>
                  <button class="tc-action tc-action--danger" title="Eliminar" @click="confirmDelete(tool)"><span class="msym" style="font-size:17px">delete</span></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal: New / Edit Tool -->
    <div v-if="showModal" class="tc-overlay" @click.self="closeModal">
      <div class="tc-modal">
        <div class="tc-modal-hdr">
          <div>
            <h2 class="tc-modal-title">{{ editTarget ? 'Editar Herramienta' : 'Nueva Herramienta' }}</h2>
            <p class="tc-modal-sub">Configura los atributos y propiedades de esta herramienta del editor.</p>
          </div>
          <button class="tc-close-btn" @click="closeModal"><span class="msym">close</span></button>
        </div>

        <div class="tc-modal-body">
          <!-- Basic fields -->
          <div class="tc-section-title">Identificación</div>
          <div class="tc-form-row">
            <div class="tc-field">
              <label class="tc-label">Tipo (único, sin espacios)</label>
              <input v-model="form.type" class="tc-input" placeholder="postgresql" :disabled="!!editTarget" />
            </div>
            <div class="tc-field">
              <label class="tc-label">Nombre</label>
              <input v-model="form.name" class="tc-input" placeholder="PostgreSQL" autofocus />
            </div>
          </div>
          <div class="tc-field">
            <label class="tc-label">Descripción</label>
            <input v-model="form.description" class="tc-input" placeholder="Breve descripción de la herramienta" />
          </div>
          <div class="tc-field">
            <label class="tc-label">Subtitle (panel izquierdo)</label>
            <input v-model="form.subtitle" class="tc-input" placeholder="Base de datos relacional" />
          </div>

          <div class="tc-section-title" style="margin-top:16px">Apariencia</div>
          <div class="tc-form-row">
            <div class="tc-field">
              <label class="tc-label">Ícono (Material Symbol)</label>
              <input v-model="form.icon" class="tc-input" placeholder="storage" />
            </div>
            <div class="tc-field">
              <label class="tc-label">Categoría</label>
              <div class="tc-sel-wrap">
                <select v-model="form.category" class="tc-input tc-sel-inp">
                  <option v-for="(meta, key) in CAT_META" :key="key" :value="key">{{ meta.label }}</option>
                  <option value="custom">Personalizada</option>
                </select>
                <span class="msym tc-sel-arr">expand_more</span>
              </div>
            </div>
          </div>

          <div class="tc-section-title" style="margin-top:16px">Tipos de Diagrama aplicables</div>
          <div class="tc-dt-checks">
            <label v-for="dt in catalog.diagramTypes" :key="dt.id" class="tc-check-item">
              <input type="checkbox" :value="dt.id" v-model="form.applicable_diagram_types" class="tc-checkbox" />
              <div class="tc-check-ico" :style="{ background: dt.color + '18', color: dt.color }">
                <span class="msym" style="font-size:14px">{{ dt.icon }}</span>
              </div>
              <div>
                <span class="tc-check-name">{{ dt.name }}</span>
                <span class="tc-check-id">{{ dt.id }}</span>
              </div>
            </label>
            <p v-if="catalog.diagramTypes.length === 0" class="text-sm page-subtitle">No hay tipos de diagrama definidos.</p>
          </div>

          <div class="tc-section-title" style="margin-top:16px">
            Definición de propiedades
            <span class="tc-hint">Cada propiedad define un campo en el panel derecho del editor</span>
          </div>
          <PropDefsTable v-model="form.propItems" />
        </div>

        <div class="tc-modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" :disabled="!canSave" @click="saveTool">
            {{ editTarget ? 'Guardar' : 'Crear' }}
            <span class="msym" style="font-size:15px">{{ editTarget ? 'save' : 'add_circle' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm delete -->
    <div v-if="deleteTarget" class="tc-overlay" @click.self="deleteTarget = null">
      <div class="tc-confirm-modal rounded-xl shadow-xl w-[420px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b tc-confirm-border">
          <h3 class="text-base font-semibold tc-confirm-title">Eliminar Herramienta</h3>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm tc-confirm-title">¿Eliminar <strong>{{ deleteTarget.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t tc-confirm-footer">
          <button class="btn btn-ghost" @click="deleteTarget = null">Cancelar</button>
          <button class="btn btn-danger" @click="doDelete">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToolCatalogStore, CAT_META } from '@/stores/toolCatalog'
import { useUIStore } from '@/stores/ui'
import PropDefsTable from '@/components/editor/PropDefsTable.vue'

const catalog = useToolCatalogStore()
const uiStore = useUIStore()

onMounted(async () => {
  await catalog.loadAll()
  uiStore.setBreadcrumbs([
    { label: 'Data Integration', path: '/integrations' },
    { label: 'Catálogo de Herramientas', path: '/integrations/tool-catalog' }
  ])
})

// ─── Helpers ──────────────────────────────────────────────────────────────────
function toItems(prop_defs, default_props) {
  return Object.entries(prop_defs || {}).map(([name, def]) => ({
    name, label: def.label || name, type: def.type || 'text',
    placeholder: def.placeholder || '', defaultValue: (default_props || {})[name] ?? '',
    options: def.options ? JSON.stringify(def.options, null, 2) : '[]',
    rows: def.rows || 3,
  }))
}
function fromItems(items) {
  const prop_defs = {}, default_props = {}
  for (const item of items) {
    prop_defs[item.name] = {
      label: item.label, type: item.type,
      ...(item.placeholder && { placeholder: item.placeholder }),
      ...(item.type === 'select' && item.options && { options: JSON.parse(item.options) }),
      ...(item.type === 'textarea' && { rows: Number(item.rows) || 3 }),
    }
    default_props[item.name] = item.defaultValue
  }
  return { prop_defs, default_props }
}

// ─── Filters ──────────────────────────────────────────────────────────────────
const search = ref(''), filterCat = ref(''), filterDiagram = ref('')

const filteredTools = computed(() =>
  catalog.tools.filter(t => {
    const q = search.value.toLowerCase()
    const matchQ = !q || t.name.toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q)
    const matchC = !filterCat.value || t.category === filterCat.value
    const matchD = !filterDiagram.value || (t.applicable_diagram_types || []).includes(filterDiagram.value)
    return matchQ && matchC && matchD
  })
)
function catMeta(cat) { return CAT_META[cat] || { label: cat, color: '#64748b', bg: '#f8fafc' } }
function diagramLabel(id) { return catalog.diagramTypes.find(dt => dt.id === id)?.name || id }

// ─── Modal ────────────────────────────────────────────────────────────────────
const showModal = ref(false), editTarget = ref(null), deleteTarget = ref(null)

const emptyForm = () => ({
  type: '', name: '', description: '', subtitle: '', icon: 'storage', category: 'source',
  applicable_diagram_types: [], propItems: [],
})
const form = ref(emptyForm())
const canSave = computed(() => form.value.type?.trim() && form.value.name?.trim())

function openNew() { editTarget.value = null; form.value = emptyForm(); showModal.value = true }
function openEdit(tool) {
  editTarget.value = tool
  form.value = {
    type: tool.type, name: tool.name, description: tool.description || '',
    subtitle: tool.subtitle || '', icon: tool.icon || 'storage', category: tool.category || 'source',
    applicable_diagram_types: [...(tool.applicable_diagram_types || [])],
    propItems: toItems(tool.prop_defs, tool.default_props),
  }
  showModal.value = true
}
function closeModal() { showModal.value = false; editTarget.value = null; form.value = emptyForm() }
function confirmDelete(tool) { deleteTarget.value = tool }

async function saveTool() {
  const { prop_defs, default_props } = fromItems(form.value.propItems)
  const payload = {
    type: form.value.type, name: form.value.name, description: form.value.description,
    subtitle: form.value.subtitle, icon: form.value.icon, category: form.value.category,
    applicable_diagram_types: form.value.applicable_diagram_types, prop_defs, default_props,
  }
  try {
    if (editTarget.value) {
      await catalog.updateTool(editTarget.value.id, payload)
      uiStore.addAlert({ type: 'success', message: 'Herramienta actualizada exitosamente' })
    } else {
      await catalog.addTool(payload)
      uiStore.addAlert({ type: 'success', message: 'Herramienta creada exitosamente' })
    }
    closeModal()
  } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error: ' + err.message })
  }
}
async function doDelete() {
  try {
    await catalog.deleteTool(deleteTarget.value.id)
    uiStore.addAlert({ type: 'success', message: 'Herramienta eliminada exitosamente' })
  } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error: ' + err.message })
  }
  deleteTarget.value = null
}
</script>

<style scoped>
.msym {
  font-family: 'Material Symbols Outlined'; font-weight: normal; font-style: normal;
  font-size: 20px; line-height: 1; display: inline-flex; align-items: center; justify-content: center;
  white-space: nowrap; direction: ltr; -webkit-font-smoothing: antialiased;
}
.tc-h1  { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 36px; font-weight: 700; color: var(--on-surface); line-height: 1.2; letter-spacing: -0.02em; }
.tc-sub { font-family: 'Inter', sans-serif; font-size: 14px; }
.page-subtitle { color: var(--on-surface-variant); }

/* Filters */
.tc-search-wrap { position: relative; display: flex; align-items: center; }
.tc-search-ico  { position: absolute; left: 10px; color: #94a3b8; font-size: 17px; pointer-events: none; }
.tc-search-in   { padding: 7px 12px 7px 34px; border: 1px solid var(--outline-variant); border-radius: 8px; font-size: 13px; outline: none; width: 220px; background: var(--card-bg); color: var(--on-surface); transition: all 0.15s; }
.tc-search-in:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.tc-sel-wrap { position: relative; display: flex; align-items: center; }
.tc-filter-sel  { padding: 7px 30px 7px 12px; border: 1px solid var(--outline-variant); border-radius: 8px; font-size: 13px; outline: none; appearance: none; background: var(--card-bg); color: var(--on-surface); cursor: pointer; }
.tc-filter-sel:focus { border-color: var(--primary); }
.tc-sel-arr { position: absolute; right: 7px; color: var(--on-surface-variant); font-size: 17px; pointer-events: none; }

/* Table */
.tc-table-wrap { background: var(--card-bg); border: 1px solid var(--outline-variant); border-radius: 12px; overflow: hidden; box-shadow: 0 1px 4px rgba(15,23,42,0.06); }
.tc-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.tc-table th { padding: 12px 16px; text-align: left; font-size: 10px; font-weight: 700; color: var(--on-surface-variant); text-transform: uppercase; letter-spacing: 0.06em; background: var(--surface-container); border-bottom: 1px solid var(--outline-variant); }
.tc-table td { padding: 13px 16px; vertical-align: middle; border-bottom: 1px solid var(--outline-variant); }
.tc-row:last-child td { border-bottom: none; }
.tc-row:hover td { background: var(--surface-container); }
.tc-tool-cell { display: flex; align-items: center; gap: 10px; }
.tc-tool-ico  { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.tc-tool-name { font-weight: 600; color: var(--on-surface); }
.tc-tool-sub  { font-size: 11px; color: var(--on-surface-variant); margin-top: 1px; }
.tc-cat-badge { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
.tc-diagram-pills { display: flex; flex-wrap: wrap; gap: 4px; }
.tc-dt-pill { font-size: 10px; font-weight: 500; padding: 2px 8px; background: var(--surface-container); color: var(--on-surface-variant); border-radius: 4px; white-space: nowrap; }
.tc-none { font-size: 12px; color: var(--on-surface-variant); }
.tc-prop-count { font-size: 12px; color: var(--on-surface-variant); }
.tc-row-actions { display: flex; align-items: center; gap: 4px; }
.tc-action { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border: none; background: transparent; border-radius: 6px; cursor: pointer; color: var(--on-surface-variant); transition: all 0.15s; }
.tc-action:hover { color: #2563eb; background: #eff6ff; }
.tc-action--danger:hover { color: #dc2626; background: #fef2f2; }
.tc-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px 0; font-size: 13px; color: var(--on-surface-variant); }

/* Modal */
.tc-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; background: rgba(15,23,42,0.55); padding: 16px; }
.tc-modal { background: var(--card-bg); width: 100%; max-width: 620px; border-radius: 12px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); display: flex; flex-direction: column; max-height: calc(100vh - 32px); overflow: hidden; }
.tc-modal-hdr { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 20px 24px; border-bottom: 1px solid var(--outline-variant); flex-shrink: 0; }
.tc-modal-title { font-size: 18px; font-weight: 700; color: var(--on-surface); font-family: 'Plus Jakarta Sans', sans-serif; }
.tc-modal-sub { font-size: 13px; color: var(--on-surface-variant); margin-top: 2px; }
.tc-close-btn { width: 30px; height: 30px; border: none; background: transparent; border-radius: 50%; cursor: pointer; color: var(--on-surface-variant); display: flex; align-items: center; justify-content: center; transition: all 0.15s; flex-shrink: 0; }
.tc-close-btn:hover { background: var(--surface-container); }
.tc-modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.tc-modal-footer { display: flex; align-items: center; justify-content: flex-end; gap: 12px; padding: 16px 24px; background: var(--surface-container); border-top: 1px solid var(--outline-variant); flex-shrink: 0; }
.tc-section-title { font-size: 11px; font-weight: 700; color: var(--on-surface-variant); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 10px; display: flex; align-items: baseline; gap: 8px; }
.tc-hint { font-size: 10px; font-weight: 400; color: var(--on-surface-variant); text-transform: none; letter-spacing: 0; }
.tc-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.tc-field { margin-bottom: 12px; position: relative; }
.tc-label { display: block; font-size: 12px; font-weight: 500; color: var(--on-surface); margin-bottom: 5px; }
.tc-input { width: 100%; box-sizing: border-box; padding: 8px 12px; border: 1px solid var(--outline-variant); border-radius: 8px; font-size: 13px; background: var(--card-bg); color: var(--on-surface); outline: none; transition: all 0.15s; font-family: inherit; }
.tc-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.tc-input:disabled { background: var(--surface-container); color: var(--on-surface-variant); }
.tc-sel-inp { padding-right: 28px; appearance: none; cursor: pointer; }
.tc-json-ta { font-family: 'Fira Code', 'Courier New', monospace; font-size: 12px; resize: vertical; line-height: 1.5; }
.tc-json-err { font-size: 11px; color: #dc2626; margin-top: 4px; }
.tc-dt-checks { display: flex; flex-direction: column; gap: 8px; }
.tc-check-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border: 1px solid var(--outline-variant); border-radius: 8px; cursor: pointer; transition: background 0.12s; }
.tc-check-item:hover { background: var(--surface-container); }
.tc-checkbox { width: 16px; height: 16px; accent-color: var(--primary); flex-shrink: 0; cursor: pointer; }
.tc-check-ico { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.tc-check-name { display: block; font-size: 13px; font-weight: 500; color: var(--on-surface); }
.tc-check-id   { display: block; font-size: 10px; color: var(--on-surface-variant); }
/* Confirm modal token helpers */
.tc-confirm-modal  { background: var(--card-bg); border: 1px solid var(--outline-variant); }
.tc-confirm-border { border-color: var(--outline-variant); }
.tc-confirm-title  { color: var(--on-surface); }
.tc-confirm-footer { background: var(--surface-container); border-color: var(--outline-variant); }
</style>
