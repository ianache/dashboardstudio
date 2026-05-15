<template>
  <div class="min-h-[calc(100vh-64px)] p-8">
    <!-- Page Header -->
    <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
      <div class="space-y-1">
        <span class="text-xs font-semibold tracking-wider text-blue-600 uppercase">Data Integration</span>
        <h1 class="intg-h1 text-slate-900">Integrations</h1>
        <p class="intg-subtitle text-slate-500 max-w-2xl">Gestiona los flujos de integración de datos desde los sistemas transaccionales hacia el ODS.</p>
      </div>
      <button class="btn btn-primary" @click="openNewModal">
        <span class="material-symbols-outlined text-lg">add</span>
        Nueva Integración
      </button>
    </div>

    <!-- Stats -->
    <div class="max-w-[1600px] mx-auto mb-8 intg-kpi-row">
      <KpiCard
        v-for="stat in stats"
        :key="stat.label"
        :icon="stat.icon"
        :label="stat.label"
        :value="stat.value"
        :trend="stat.trend"
        :icon-color="stat.iconColor"
        :icon-bg="stat.iconBg"
      />
    </div>

    <!-- Table Section -->
    <div class="max-w-[1600px] mx-auto">
      <div class="intg-table-wrap">

        <!-- Toolbar -->
        <div class="intg-toolbar">
          <div class="intg-toolbar-left">
            <div class="intg-search-wrap">
              <span class="material-symbols-outlined intg-search-icon">search</span>
              <input v-model="searchQuery" type="text" placeholder="Buscar flujos..." class="intg-search-input" />
            </div>
            <div class="intg-filter-wrap">
              <select v-model="statusFilter" class="intg-filter-select">
                <option value="">Status</option>
                <option value="active">Activo</option>
                <option value="scheduled">Programado</option>
                <option value="paused">Pausado</option>
                <option value="error">Error</option>
              </select>
              <span class="material-symbols-outlined intg-filter-arrow">expand_more</span>
            </div>
          </div>
          <div class="intg-toolbar-right">
            <span class="intg-showing-label">{{ showingLabel }}</span>
            <div class="intg-view-toggle">
              <button
                class="intg-view-btn"
                :class="{ active: viewMode === 'table' }"
                title="Vista tabla"
                @click="viewMode = 'table'">
                <span class="material-symbols-outlined" style="font-size:18px">table_rows</span>
              </button>
              <button
                class="intg-view-btn"
                :class="{ active: viewMode === 'card' }"
                title="Vista tarjetas"
                @click="viewMode = 'card'">
                <span class="material-symbols-outlined" style="font-size:18px">grid_view</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Card view -->
        <div v-if="viewMode === 'card'" class="intg-card-grid">
          <div v-if="pagedFlows.length === 0" class="intg-empty" style="grid-column:1/-1">
            <span class="material-symbols-outlined intg-empty-icon">sync_disabled</span>
            <span class="intg-empty-text">No se encontraron flujos</span>
          </div>
          <div v-for="flow in pagedFlows" :key="flow.id" class="intg-flow-card">
            <div class="intg-flow-card-header">
              <div class="intg-flow-icon-wrap">
                <span class="material-symbols-outlined" style="font-size:20px;color:#2563eb">sync</span>
              </div>
              <span class="intg-badge" :class="`intg-badge--${flow.status}`">{{ STATUS_LABELS[flow.status] }}</span>
            </div>
            <p class="intg-flow-name" style="margin-top:12px">{{ flow.name }}</p>
            <p class="intg-flow-desc">{{ flow.description }}</p>
            <div class="intg-flow-card-meta">
              <span class="intg-type-pill">{{ flow.type }}</span>
            </div>
            <div class="intg-flow-card-route">
              <span class="text-slate-500 text-xs">{{ flow.source }}</span>
              <span class="material-symbols-outlined" style="font-size:14px;color:#94a3b8">arrow_forward</span>
              <span class="text-slate-500 text-xs">{{ flow.target }}</span>
            </div>
            <div class="intg-flow-card-footer">
              <span class="text-xs text-slate-400">{{ formatDate(flow.lastRun) }}</span>
              <div class="intg-row-actions">
                <button class="intg-action intg-action--diagram" title="Abrir editor de diagrama" @click="openDiagramEditor(flow)">
                  <span class="material-symbols-outlined" style="font-size:16px">schema</span>
                </button>
                <button class="intg-action" title="Editar metadata" @click="openEditModal(flow)">
                  <span class="material-symbols-outlined" style="font-size:16px">edit</span>
                </button>
                <button class="intg-action" :title="flow.status === 'paused' ? 'Activar' : 'Pausar'" @click="togglePause(flow)">
                  <span class="material-symbols-outlined" style="font-size:16px">{{ flow.status === 'paused' ? 'play_arrow' : 'pause' }}</span>
                </button>
                <button class="intg-action intg-action--danger" title="Eliminar" @click="confirmDelete(flow)">
                  <span class="material-symbols-outlined" style="font-size:16px">delete</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Table view -->
        <div v-else class="overflow-x-auto">
          <table class="intg-table">
            <thead>
              <tr>
                <th>Nombre del Flujo</th>
                <th>Estado</th>
                <th>Tipo</th>
                <th>Origen → Destino</th>
                <th>Última Ejecución</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="pagedFlows.length === 0">
                <td colspan="6">
                  <div class="intg-empty">
                    <span class="material-symbols-outlined intg-empty-icon">sync_disabled</span>
                    <span class="intg-empty-text">No se encontraron flujos</span>
                  </div>
                </td>
              </tr>
              <tr v-for="flow in pagedFlows" :key="flow.id" class="intg-table-row">
                <td>
                  <div class="intg-flow-cell">
                    <div class="intg-flow-icon-wrap">
                      <span class="material-symbols-outlined" style="font-size:18px;color:#2563eb">sync</span>
                    </div>
                    <div>
                      <p class="intg-flow-name">{{ flow.name }}</p>
                      <p class="intg-flow-desc">{{ flow.description }}</p>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="intg-badge" :class="`intg-badge--${flow.status}`">
                    {{ STATUS_LABELS[flow.status] || flow.status }}
                  </span>
                </td>
                <td><span class="intg-type-pill">{{ flow.type }}</span></td>
                <td>
                  <span class="intg-route">
                    <span>{{ flow.source }}</span>
                    <span class="intg-route-arrow">→</span>
                    <span>{{ flow.target }}</span>
                  </span>
                </td>
                <td>
                  <p class="text-sm text-slate-700">{{ formatDate(flow.lastRun) }}</p>
                  <p class="text-xs" :class="flow.lastRunSuccess ? 'text-emerald-600' : 'text-red-500'">
                    {{ flow.lastRunSuccess ? 'Exitoso' : 'Fallido' }}
                  </p>
                </td>
                <td>
                <div class="intg-row-actions">
                    <button class="intg-action" title="Historial de ejecuciones" @click="openHistory(flow)">
                      <span class="material-symbols-outlined" style="font-size:18px">history</span>
                    </button>
                    <button class="intg-action intg-action--diagram" title="Abrir editor de diagrama" @click="openDiagramEditor(flow)">
                      <span class="material-symbols-outlined" style="font-size:18px">schema</span>
                    </button>
                    <button class="intg-action" title="Editar metadata" @click="openEditModal(flow)">
                      <span class="material-symbols-outlined" style="font-size:18px">edit</span>
                    </button>
                    <button class="intg-action" :title="flow.status === 'paused' ? 'Activar' : 'Pausar'" @click="togglePause(flow)">
                      <span class="material-symbols-outlined" style="font-size:18px">{{ flow.status === 'paused' ? 'play_arrow' : 'pause' }}</span>
                    </button>
                    <button class="intg-action intg-action--danger" title="Eliminar" @click="confirmDelete(flow)">
                      <span class="material-symbols-outlined" style="font-size:18px">delete</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination footer -->
        <div class="intg-pagination">
          <button
            class="intg-page-nav"
            :disabled="currentPage === 1"
            @click="currentPage--">
            <span class="material-symbols-outlined" style="font-size:16px">chevron_left</span>
            Previous
          </button>
          <div class="intg-page-numbers">
            <button
              v-for="p in totalPages"
              :key="p"
              class="intg-page-num"
              :class="{ active: p === currentPage }"
              @click="currentPage = p">
              {{ p }}
            </button>
          </div>
          <button
            class="intg-page-nav"
            :disabled="currentPage === totalPages"
            @click="currentPage++">
            Next
            <span class="material-symbols-outlined" style="font-size:16px">chevron_right</span>
          </button>
        </div>

      </div>
    </div>

    <!-- Modal: Nueva / Editar Integración -->
    <div v-if="showModal" class="intg-overlay" @click.self="closeModal">
      <div class="intg-modal">
        <div class="intg-modal-header">
          <div class="intg-modal-header-inner">
            <div>
              <h2 class="intg-modal-title">{{ editTarget ? 'Editar Integración' : 'Nueva Integración' }}</h2>
              <p class="intg-modal-sub">{{ editTarget ? 'Modifica los datos del flujo.' : 'Define un nuevo flujo de integración de datos.' }}</p>
            </div>
            <button class="intg-modal-close-btn" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
        <div class="intg-modal-body">
          <div class="intg-field">
            <label class="intg-label">Nombre</label>
            <input v-model="form.name" type="text" class="intg-input" placeholder="Ej: ERP → ODS Ventas" autofocus />
          </div>
          <div class="intg-field">
            <label class="intg-label">Descripción</label>
            <textarea v-model="form.description" class="intg-textarea" rows="2" placeholder="Describe el propósito de este flujo..."></textarea>
          </div>
          <div class="intg-form-grid">
            <div class="intg-field">
              <label class="intg-label">Tipo de diagrama</label>
              <div class="intg-select-wrap">
                <select v-model="form.diagramType" class="intg-select">
                  <option v-if="catalog.diagramTypes.length === 0" value="" disabled>Cargando...</option>
                  <option
                    v-for="dt in catalog.diagramTypes"
                    :key="dt.id"
                    :value="dt.id"
                  >{{ dt.name }}</option>
                </select>
                <span class="material-symbols-outlined intg-select-arrow">expand_more</span>
              </div>
            </div>
            <div class="intg-field">
              <label class="intg-label">Estado inicial</label>
              <div class="intg-select-wrap">
                <select v-model="form.status" class="intg-select">
                  <option value="active">Activo</option>
                  <option value="scheduled">Programado</option>
                  <option value="paused">Pausado</option>
                </select>
                <span class="material-symbols-outlined intg-select-arrow">expand_more</span>
              </div>
            </div>
          </div>
          <div class="intg-form-grid">
            <div class="intg-field">
              <label class="intg-label">Sistema Origen</label>
              <input v-model="form.source" type="text" class="intg-input" placeholder="Ej: ERP SAP" />
            </div>
            <div class="intg-field">
              <label class="intg-label">Sistema Destino</label>
              <input v-model="form.target" type="text" class="intg-input" placeholder="Ej: ODS PostgreSQL" />
            </div>
          </div>
        </div>
        <div class="intg-modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" :disabled="!form.name.trim()" @click="saveFlow">
            <span>{{ editTarget ? 'Guardar' : 'Crear' }}</span>
            <span class="material-symbols-outlined" style="font-size:16px">{{ editTarget ? 'save' : 'add_circle' }}</span>
          </button>
        </div>
      </div>
    </div>

    <ExecutionHistoryModal
      v-if="showHistoryModal"
      :flow-id="historyTarget?.id"
      :flow-name="historyTarget?.name"
      @close="showHistoryModal = false"
    />

    <!-- Modal: Confirmar eliminar -->
    <div v-if="deleteTarget" class="intg-overlay" @click.self="deleteTarget = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[420px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Eliminar Integración</h3>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-700">¿Eliminar <strong>{{ deleteTarget.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="btn btn-ghost" @click="deleteTarget = null">Cancelar</button>
          <button class="btn btn-danger" @click="doDelete">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUIStore } from '@/stores/ui'
import { useIntegrationsStore } from '@/stores/integrations'
import { useToolCatalogStore } from '@/stores/toolCatalog'
import KpiCard from '@/components/common/KpiCard.vue'

const router = useRouter()
const uiStore = useUIStore()
const flowStore = useIntegrationsStore()
const catalog = useToolCatalogStore()

onMounted(async () => {
  uiStore.setBreadcrumbs([
    { label: 'Data Integration', path: '/integrations' },
    { label: 'Integrations', path: '/integrations' }
  ])
  await Promise.all([flowStore.loadFromBackend(), catalog.loadDiagramTypes()])
})

const STATUS_LABELS = { active: 'Activo', scheduled: 'Programado', paused: 'Pausado', error: 'Error' }

const flows = computed(() =>
  flowStore.allFlows.map(f => ({
    id: f.id, name: f.name, description: f.description,
    status: f.status, type: f.flow_type,
    source: f.source_system, target: f.target_system,
    lastRun: f.last_run, lastRunSuccess: f.last_run_success,
  }))
)

const searchQuery = ref('')
const statusFilter = ref('')
const viewMode = ref('table')
const currentPage = ref(1)
const PAGE_SIZE = 10
const showModal = ref(false)
const showHistoryModal = ref(false)
const historyTarget = ref(null)
const editTarget = ref(null)
const deleteTarget = ref(null)

const openHistory = (flow) => {
  historyTarget.value = flow
  showHistoryModal.value = true
}

const emptyForm = () => ({
  name: '', description: '',
  diagramType: catalog.diagramTypes[0]?.id || '',
  status: 'active', source: '', target: '',
})
const form = ref(emptyForm())

const stats = computed(() => [
  {
    label: 'Total Flujos',
    value: flows.value.length,
    trend: 'Registrados',
    icon: 'account_tree',
    iconColor: 'var(--primary)',
    iconBg: 'rgba(0,88,190,0.1)'
  },
  {
    label: 'Activos',
    value: flows.value.filter(f => f.status === 'active').length,
    trend: 'En ejecución',
    icon: 'check_circle',
    iconColor: '#16a34a',
    iconBg: 'rgba(22,163,74,0.1)'
  },
  {
    label: 'Con Errores',
    value: flows.value.filter(f => f.status === 'error').length,
    trend: 'Requieren atención',
    icon: 'error',
    iconColor: 'var(--error)',
    iconBg: 'rgba(186,26,26,0.1)'
  },
  {
    label: 'Programados',
    value: flows.value.filter(f => f.status === 'scheduled').length,
    trend: 'Próxima ejecución',
    icon: 'schedule',
    iconColor: 'var(--secondary)',
    iconBg: 'rgba(86,94,116,0.1)'
  }
])

const filteredFlows = computed(() =>
  flows.value.filter(f => {
    const q = searchQuery.value.toLowerCase()
    const matchSearch = !q || f.name.toLowerCase().includes(q) || f.description.toLowerCase().includes(q)
    const matchStatus = !statusFilter.value || f.status === statusFilter.value
    return matchSearch && matchStatus
  })
)

const totalPages = computed(() => Math.max(1, Math.ceil(filteredFlows.value.length / PAGE_SIZE)))

const pagedFlows = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredFlows.value.slice(start, start + PAGE_SIZE)
})

const showingLabel = computed(() => {
  const total = filteredFlows.value.length
  if (total === 0) return 'Showing 0 flows'
  const start = (currentPage.value - 1) * PAGE_SIZE + 1
  const end = Math.min(currentPage.value * PAGE_SIZE, total)
  return `Showing ${start}–${end} of ${total} flows`
})

watch([searchQuery, statusFilter], () => { currentPage.value = 1 })

function formatDate(str) {
  if (!str) return '—'
  return new Date(str).toLocaleString('es-PE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function openNewModal() {
  editTarget.value = null
  form.value = emptyForm()
  showModal.value = true
}

function openDiagramEditor(flow) {
  router.push(`/integrations/${flow.id}/editor`)
}

function openEditModal(flow) {
  const raw = flowStore.allFlows.find(f => f.id === flow.id)
  editTarget.value = flow
  form.value = {
    name: flow.name,
    description: flow.description || '',
    diagramType: raw?.diagram_type || catalog.diagramTypes[0]?.id || '',
    status: flow.status,
    source: flow.source || '',
    target: flow.target || '',
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
  form.value = emptyForm()
}

async function saveFlow() {
  if (!form.value.name.trim()) return
  try {
    const payload = {
      name: form.value.name, description: form.value.description,
      status: form.value.status, diagram_type: form.value.diagramType,
      source_system: form.value.source, target_system: form.value.target,
    }
    if (editTarget.value) {
      await flowStore.updateFlow(editTarget.value.id, payload)
      uiStore.addAlert({ type: 'success', message: 'Integración actualizada exitosamente' })
    } else {
      await flowStore.createFlow(payload)
      uiStore.addAlert({ type: 'success', message: 'Integración creada exitosamente' })
    }
    closeModal()
  } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error: ' + err.message })
  }
}

async function togglePause(flow) {
  try { await flowStore.togglePause(flow.id) } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error: ' + err.message })
  }
}

function confirmDelete(flow) { deleteTarget.value = flow }

async function doDelete() {
  if (!deleteTarget.value) return
  try {
    await flowStore.deleteFlow(deleteTarget.value.id)
    uiStore.addAlert({ type: 'success', message: 'Integración eliminada exitosamente' })
  } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error: ' + err.message })
  }
  deleteTarget.value = null
}
</script>

<style scoped>
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
  -webkit-font-smoothing: antialiased;
}

.intg-h1 {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 36px;
  line-height: 1.2;
  letter-spacing: -0.02em;
  font-weight: 700;
}
.intg-subtitle {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 14px;
}

/* Stats row — mismo patrón que HomeView .kpi-row */
.intg-kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--gutter);
}

/* Table container */
.intg-table-wrap {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(15,23,42,0.06);
  overflow: hidden;
}

/* Toolbar */
.intg-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
}
.intg-toolbar-left  { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.intg-toolbar-right { display: flex; align-items: center; gap: 12px; margin-left: auto; }

.intg-showing-label {
  font-size: 13px;
  color: #64748b;
  white-space: nowrap;
}

.intg-view-toggle {
  display: flex;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.intg-view-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border: none; background: #fff;
  cursor: pointer; color: #94a3b8;
  transition: all 0.15s;
}
.intg-view-btn:first-child { border-right: 1px solid #e2e8f0; }
.intg-view-btn:hover { background: #f8fafc; color: #475569; }
.intg-view-btn.active { background: #eff6ff; color: #2563eb; }

.intg-search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.intg-search-icon {
  position: absolute;
  left: 10px;
  color: #94a3b8;
  font-size: 18px;
  pointer-events: none;
}
.intg-search-input {
  padding: 8px 12px 8px 36px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  width: 220px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.intg-search-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.intg-search-input::placeholder { color: #94a3b8; }

.intg-filter-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.intg-filter-select {
  padding: 8px 32px 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  appearance: none;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s;
}
.intg-filter-select:focus { border-color: #2563eb; }
.intg-filter-arrow {
  position: absolute; right: 8px;
  color: #64748b; font-size: 18px; pointer-events: none;
}

/* Table */
.intg-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.intg-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.intg-table td {
  padding: 14px 16px;
  vertical-align: middle;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}
.intg-table-row:last-child td { border-bottom: none; }
.intg-table-row:hover td { background: #f8fafc; }

.intg-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px 0; }
.intg-empty-icon { font-size: 40px; color: #cbd5e1; }
.intg-empty-text { font-size: 13px; color: #94a3b8; }

/* Flow cell */
.intg-flow-cell { display: flex; align-items: center; gap: 10px; }
.intg-flow-icon-wrap {
  width: 34px; height: 34px;
  background: #eff6ff;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.intg-flow-name { font-weight: 600; color: #0f172a; font-size: 13px; }
.intg-flow-desc { font-size: 11px; color: #94a3b8; margin-top: 2px; }

/* Status badge */
.intg-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.intg-badge--active    { background: #dcfce7; color: #16a34a; }
.intg-badge--scheduled { background: #dbeafe; color: #1d4ed8; }
.intg-badge--paused    { background: #f1f5f9; color: #64748b; }
.intg-badge--error     { background: #fee2e2; color: #dc2626; }

/* Type pill */
.intg-type-pill {
  display: inline-block;
  padding: 3px 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: #475569;
}

/* Route */
.intg-route { display: flex; align-items: center; gap: 4px; font-size: 13px; flex-wrap: wrap; }
.intg-route-arrow { color: #94a3b8; }

/* Card view */
.intg-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  padding: 20px;
}
.intg-flow-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: box-shadow 0.2s, transform 0.2s;
}
.intg-flow-card:hover { box-shadow: 0 4px 16px rgba(15,23,42,0.08); transform: translateY(-1px); }
.intg-flow-card-header { display: flex; align-items: center; justify-content: space-between; }
.intg-flow-card-meta { margin-top: 8px; }
.intg-flow-card-route {
  display: flex; align-items: center; gap: 4px;
  margin-top: 4px;
}
.intg-flow-card-footer {
  display: flex; align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

/* Pagination */
.intg-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  background: #fafafa;
}
.intg-page-nav {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  font-size: 13px; font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s;
}
.intg-page-nav:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; background: #eff6ff; }
.intg-page-nav:disabled { opacity: 0.4; cursor: default; }

.intg-page-numbers { display: flex; align-items: center; gap: 4px; }
.intg-page-num {
  min-width: 30px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  font-size: 13px; font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
  padding: 0 6px;
}
.intg-page-num:hover { border-color: #2563eb; color: #2563eb; }
.intg-page-num.active { background: #2563eb; border-color: #2563eb; color: #fff; }

/* Row actions */
.intg-row-actions { display: flex; align-items: center; gap: 4px; }
.intg-action {
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  border: none; background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}
.intg-action:hover { color: #2563eb; background: #eff6ff; }
.intg-action--diagram:hover { color: #7c3aed; background: #f5f3ff; }
.intg-action--danger:hover { color: #dc2626; background: #fef2f2; }

/* Overlay */
.intg-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(15,23,42,0.55);
  padding: 16px;
}

/* Modal */
.intg-modal {
  background: #fff;
  width: 100%; max-width: 560px;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  display: flex; flex-direction: column;
  max-height: calc(100vh - 32px);
  overflow: hidden;
}
.intg-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.intg-modal-header-inner {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px;
}
.intg-modal-title {
  font-size: 20px; font-weight: 700; color: #0f172a;
  margin: 0 0 4px 0;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}
.intg-modal-sub { font-size: 13px; color: #64748b; margin: 0; }
.intg-modal-close-btn {
  width: 32px; height: 32px;
  border: none; background: transparent;
  border-radius: 50%; cursor: pointer;
  color: #64748b; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s; flex-shrink: 0;
}
.intg-modal-close-btn:hover { background: #f1f5f9; color: #334155; }
.intg-modal-body {
  padding: 24px; overflow-y: auto; flex: 1;
}
.intg-modal-footer {
  display: flex; align-items: center;
  justify-content: flex-end; gap: 12px;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

/* Form */
.intg-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.intg-field { margin-bottom: 18px; }
.intg-field:last-child { margin-bottom: 0; }
.intg-label { display: block; font-size: 13px; font-weight: 500; color: #0f172a; margin-bottom: 6px; }
.intg-input,
.intg-textarea,
.intg-select {
  width: 100%; padding: 9px 13px;
  border: 1px solid #cbd5e1; border-radius: 8px;
  font-size: 13px; background: #fff; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}
.intg-input::placeholder,
.intg-textarea::placeholder { color: #94a3b8; }
.intg-input:focus,
.intg-textarea:focus,
.intg-select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.intg-textarea { resize: none; min-height: 72px; }
.intg-select-wrap { position: relative; }
.intg-select { padding-right: 36px; appearance: none; cursor: pointer; }
.intg-select-arrow {
  position: absolute; right: 10px; top: 50%;
  transform: translateY(-50%);
  color: #64748b; font-size: 18px; pointer-events: none;
}
</style>
