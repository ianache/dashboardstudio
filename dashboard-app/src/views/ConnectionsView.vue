<template>
  <div class="min-h-[calc(100vh-64px)] p-8">

    <!-- Page Header -->
    <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
      <div class="space-y-1">
        <span class="text-xs font-semibold tracking-wider text-blue-600 uppercase">Data Integration</span>
        <h1 class="font-h1 text-h1 text-slate-900">Conexiones</h1>
        <p class="font-body-md text-slate-500 max-w-2xl">
          Gestiona las conexiones a fuentes y destinos de datos externos utilizados por los flujos de integración.
        </p>
      </div>
      <button class="btn btn-primary" @click="openNew">
        <span class="material-symbols-outlined text-lg">add</span>
        Nueva Conexión
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="connections.length === 0 && !loading" class="max-w-[1600px] mx-auto">
      <div class="bg-white border border-slate-200 rounded-xl p-12 flex flex-col items-center justify-center gap-4 text-center">
        <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
          <span class="material-symbols-outlined text-3xl text-slate-400">cable</span>
        </div>
        <h3 class="text-lg font-semibold text-slate-900">Sin conexiones configuradas</h3>
        <p class="text-sm text-slate-500 max-w-md">
          Agrega tu primera conexión para que los flujos de integración puedan acceder a fuentes de datos externas.
        </p>
        <button class="btn btn-primary" @click="openNew">
          <span class="material-symbols-outlined text-lg">add</span>
          Crear conexión
        </button>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-else-if="loading" class="max-w-[1600px] mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="i in 4" :key="i" class="bg-white border border-slate-200 rounded-xl p-5 animate-pulse min-h-[200px]">
          <div class="h-4 bg-slate-100 rounded w-2/3 mb-3"></div>
          <div class="h-3 bg-slate-100 rounded w-full mb-2"></div>
          <div class="h-3 bg-slate-100 rounded w-4/5"></div>
        </div>
      </div>
    </div>

    <!-- Connection cards grid -->
    <div v-else class="max-w-[1600px] mx-auto">
      <div class="cv-grid">

        <!-- Connection card -->
        <div
          v-for="(conn, idx) in connections"
          :key="conn.id"
          class="cv-card"
          :style="{ animationDelay: `${idx * 40}ms` }"
        >
          <!-- Colored stripe -->
          <div class="cv-card-stripe" :style="{ background: typeColor(conn.type).accent }"></div>

          <!-- Card body -->
          <div class="cv-card-body">
            <div class="cv-card-ico" :style="{ background: typeColor(conn.type).accent + '18', color: typeColor(conn.type).accent }">
              <span class="material-symbols-outlined" style="font-size:24px">{{ typeIcon(conn.type) }}</span>
            </div>
            <h3 class="cv-card-name">{{ conn.name }}</h3>
            <p class="cv-card-desc">{{ typeName(conn.type) }}</p>
            <div class="cv-card-meta">
              <span class="cv-meta-badge" :class="conn.status === 'active' ? 'cv-badge--ok' : 'cv-badge--off'">
                <span class="material-symbols-outlined" style="font-size:12px">{{ conn.status === 'active' ? 'check_circle' : 'pause_circle' }}</span>
                {{ conn.status === 'active' ? 'Activa' : 'Inactiva' }}
              </span>
              <span class="cv-host-label" v-if="conn.connection_config?.host || conn.connection_config?.url">
                {{ conn.connection_config?.host || conn.connection_config?.url }}
              </span>
            </div>
          </div>

          <!-- Footer actions -->
          <div class="cv-card-footer">
            <button class="cv-action" title="Editar" @click="openEdit(conn)">
              <span class="material-symbols-outlined" style="font-size:17px">edit</span>
            </button>
            <button class="cv-action cv-action--danger" title="Eliminar" @click="deleteTarget = conn">
              <span class="material-symbols-outlined" style="font-size:17px">delete</span>
            </button>
          </div>
        </div>

        <!-- Add new card -->
        <button class="cv-new-card" @click="openNew">
          <div class="cv-new-ico">
            <span class="material-symbols-outlined" style="font-size:22px;color:#94a3b8">add</span>
          </div>
          <span class="cv-new-lbl">Nueva Conexión</span>
        </button>

      </div>
    </div>

    <!-- Edit/Create Modal -->
    <ConnectionEditModal
      v-if="showModal"
      :connection="editingConn"
      @close="closeModal"
      @saved="onSaved"
    />

    <!-- Delete confirm -->
    <div v-if="deleteTarget" class="cv-overlay" @click.self="deleteTarget = null">
      <div class="cv-confirm">

        <!-- Warning icon -->
        <div class="cv-confirm-icon">
          <span class="material-symbols-outlined" style="font-size:32px;color:#dc2626">delete_forever</span>
        </div>

        <!-- Title -->
        <h3 class="cv-confirm-title">Eliminar Conexión</h3>

        <!-- Connection chip -->
        <div class="cv-confirm-chip">
          <div class="cv-chip-ico" :style="{ background: typeColor(deleteTarget.type).accent + '18', color: typeColor(deleteTarget.type).accent }">
            <span class="material-symbols-outlined" style="font-size:15px">{{ typeIcon(deleteTarget.type) }}</span>
          </div>
          <span class="cv-chip-name">{{ deleteTarget.name }}</span>
          <span class="cv-chip-type">{{ typeName(deleteTarget.type) }}</span>
        </div>

        <!-- Warning text -->
        <p class="cv-confirm-msg">
          Esta acción eliminará permanentemente la conexión y no puede deshacerse.
          Los flujos de integración que la referencian podrían fallar.
        </p>

        <!-- Actions -->
        <div class="cv-confirm-actions">
          <button class="btn btn-ghost" @click="deleteTarget = null">Cancelar</button>
          <button class="btn btn-danger" @click="doDelete">
            <span class="material-symbols-outlined" style="font-size:16px">delete</span>
            Eliminar
          </button>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUIStore } from '@/stores/ui'
import { dataSourcesApi } from '@/services/api'
import { CONN_TYPES, CONN_META, connTypeMeta, connTypeLabel as _connTypeLabel } from '@/constants/connectionTypes'
import ConnectionEditModal from '@/components/connections/ConnectionEditModal.vue'

const uiStore = useUIStore()

onMounted(async () => {
  uiStore.setBreadcrumbs([
    { label: 'Data Integration', path: '/integrations' },
    { label: 'Conexiones', path: '/integrations/connections' }
  ])
  await fetchConnections()
})

// ─── Type metadata ────────────────────────────────────────────────────────────
const TYPE_META = CONN_META

function typeColor(t) { return connTypeMeta(t) }
function typeIcon(t)  { return connTypeMeta(t).icon }
function typeName(t)  { return _connTypeLabel(t) }

// ─── State ────────────────────────────────────────────────────────────────────
const connections  = ref([])
const loading      = ref(true)
const showModal    = ref(false)
const editingConn  = ref(null)
const deleteTarget = ref(null)

async function fetchConnections() {
  try {
    loading.value = true
    connections.value = await dataSourcesApi.getAll()
  } catch (err) {
    console.error('Error loading connections:', err)
    uiStore.addAlert({ type: 'error', message: 'No se pudieron cargar las conexiones' })
  } finally {
    loading.value = false
  }
}

function openNew()       { editingConn.value = null; showModal.value = true }
function openEdit(conn)  { editingConn.value = conn; showModal.value = true }
function closeModal()    { showModal.value = false; editingConn.value = null }

async function onSaved() {
  closeModal()
  await fetchConnections()
  uiStore.addAlert({ type: 'success', message: editingConn.value ? 'Conexión actualizada' : 'Conexión creada' })
}

async function doDelete() {
  try {
    await dataSourcesApi.delete(deleteTarget.value.id)
    uiStore.addAlert({ type: 'success', message: 'Conexión eliminada' })
    await fetchConnections()
  } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error al eliminar: ' + err.message })
  }
  deleteTarget.value = null
}
</script>

<style scoped>
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal;
  font-size: 24px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
  white-space: nowrap; direction: ltr; -webkit-font-smoothing: antialiased;
}

/* Grid */
.cv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }

/* Card */
.cv-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
  display: flex; flex-direction: column; box-shadow: 0 1px 4px rgba(15,23,42,0.06);
  transition: box-shadow 0.2s, transform 0.2s;
  animation: cvFadeIn 0.35s ease forwards; opacity: 0;
}
@keyframes cvFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.cv-card:hover { box-shadow: 0 6px 24px rgba(15,23,42,0.1); transform: translateY(-2px); }

/* Stripe */
.cv-card-stripe { height: 4px; flex-shrink: 0; }

/* Body */
.cv-card-body { padding: 20px; flex: 1; display: flex; flex-direction: column; gap: 8px; }
.cv-card-ico   { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 4px; flex-shrink: 0; }
.cv-card-name  { font-size: 16px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; margin: 0; }
.cv-card-desc  { font-size: 13px; color: #64748b; flex: 1; margin: 0; }

/* Meta row */
.cv-card-meta  { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.cv-meta-badge { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 600; border-radius: 20px; padding: 3px 10px; width: fit-content; }
.cv-badge--ok  { background: #dcfce7; color: #16a34a; }
.cv-badge--off { background: #f1f5f9; color: #64748b; }
.cv-host-label { font-size: 11px; font-family: 'Fira Code', 'Consolas', monospace; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Footer */
.cv-card-footer { display: flex; align-items: center; justify-content: flex-end; gap: 6px; padding: 12px 16px; border-top: 1px solid #f1f5f9; background: #fafafa; }
.cv-action { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; background: #fff; border-radius: 7px; cursor: pointer; color: #64748b; transition: all 0.15s; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.cv-action:hover { color: #2563eb; background: #eff6ff; }
.cv-action--danger:hover { color: #dc2626; background: #fef2f2; }

/* New-card */
.cv-new-card {
  border: 2px dashed #e2e8f0; border-radius: 12px; padding: 32px; min-height: 220px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
  background: transparent; cursor: pointer; transition: all 0.2s;
}
.cv-new-card:hover { border-color: #2563eb; background: rgba(239,246,255,0.3); }
.cv-new-ico { width: 44px; height: 44px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
.cv-new-card:hover .cv-new-ico { background: #dbeafe; }
.cv-new-lbl { font-size: 13px; font-weight: 600; color: #64748b; }
.cv-new-card:hover .cv-new-lbl { color: #2563eb; }
/* Overlay (shared) */
.cv-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; background: rgba(15,23,42,0.55); padding: 16px; }

/* Danger confirm dialog */
.cv-confirm {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  width: 100%; max-width: 400px;
  padding: 32px 28px 24px;
  display: flex; flex-direction: column; align-items: center; gap: 16px;
  text-align: center;
  animation: cvFadeIn 0.2s ease;
}
.cv-confirm-icon {
  width: 64px; height: 64px;
  border-radius: 50%;
  background: #fef2f2;
  border: 1px solid #fecaca;
  display: flex; align-items: center; justify-content: center;
}
.cv-confirm-title {
  font-size: 18px; font-weight: 700; color: #0f172a;
  font-family: 'Plus Jakarta Sans', sans-serif;
  margin: 0;
}
.cv-confirm-chip {
  display: inline-flex; align-items: center; gap: 8px;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 8px 14px;
  width: 100%; box-sizing: border-box;
}
.cv-chip-ico {
  width: 26px; height: 26px;
  border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.cv-chip-name { font-size: 13px; font-weight: 600; color: #0f172a; flex: 1; text-align: left; }
.cv-chip-type { font-size: 11px; color: #94a3b8; white-space: nowrap; }
.cv-confirm-msg {
  font-size: 13px; color: #64748b; line-height: 1.6;
  margin: 0; max-width: 320px;
}
.cv-confirm-actions {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}
</style>
