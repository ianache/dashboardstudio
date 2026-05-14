<template>
  <div class="min-h-[calc(100vh-64px)] p-8">
    <!-- Header -->
    <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
      <div class="space-y-1">
        <span class="text-xs font-semibold tracking-wider text-blue-600 uppercase">Data Integration</span>
        <h1 class="dt-h1">Tipos de Diagrama</h1>
        <p class="dt-sub text-slate-500 max-w-2xl">Gestiona los tipos de diagrama disponibles en el editor visual. Cada tipo define el contexto de diseño.</p>
      </div>
      <button class="btn btn-primary" @click="openNew">
        <span class="msym">add</span>Nuevo Tipo
      </button>
    </div>

    <!-- Grid -->
    <div class="max-w-[1600px] mx-auto">
      <div class="dt-grid">
        <div v-for="(dt, idx) in catalog.diagramTypes" :key="dt.id" class="dt-card" :style="{ animationDelay: `${idx * 40}ms` }">
          <div class="dt-card-stripe" :style="{ background: dt.color }"></div>
          <div class="dt-card-body">
            <div class="dt-card-ico" :style="{ background: dt.color + '18', color: dt.color }">
              <span class="msym" style="font-size:24px">{{ dt.icon }}</span>
            </div>
            <h3 class="dt-card-name">{{ dt.name }}</h3>
            <p class="dt-card-desc">{{ dt.description || 'Sin descripción' }}</p>
            <div class="dt-card-meta">
              <span class="dt-tools-badge">
                <span class="msym" style="font-size:13px">construction</span>
                {{ toolCountFor(dt.id) }} herramientas
              </span>
            </div>
          </div>
          <div class="dt-card-footer">
            <button class="dt-action" title="Editar" @click="openEdit(dt)"><span class="msym" style="font-size:17px">edit</span></button>
            <button class="dt-action dt-action--danger" title="Eliminar" @click="confirmDelete(dt)"><span class="msym" style="font-size:17px">delete</span></button>
          </div>
        </div>

        <!-- New card -->
        <button class="dt-new-card" @click="openNew">
          <div class="dt-new-ico"><span class="msym" style="font-size:22px;color:#94a3b8">add</span></div>
          <span class="dt-new-lbl">Nuevo tipo de diagrama</span>
        </button>
      </div>
    </div>

    <!-- Modal: New / Edit -->
    <div v-if="showModal" class="dt-overlay" @click.self="closeModal">
      <div class="dt-modal">
        <div class="dt-modal-hdr">
          <div>
            <h2 class="dt-modal-title">{{ editTarget ? 'Editar Tipo de Diagrama' : 'Nuevo Tipo de Diagrama' }}</h2>
            <p class="dt-modal-sub">{{ editTarget ? 'Modifica los atributos del tipo.' : 'Define un nuevo tipo de diagrama para el editor.' }}</p>
          </div>
          <button class="dt-close-btn" @click="closeModal"><span class="msym">close</span></button>
        </div>
        <div class="dt-modal-body">
          <div class="dt-field">
            <label class="dt-label">ID (único, sin espacios)</label>
            <input v-model="form.id" class="dt-input" placeholder="data-integration" :disabled="!!editTarget" />
          </div>
          <div class="dt-field">
            <label class="dt-label">Nombre</label>
            <input v-model="form.name" class="dt-input" placeholder="Data Integration Flow" autofocus />
          </div>
          <div class="dt-field">
            <label class="dt-label">Descripción</label>
            <textarea v-model="form.description" class="dt-textarea" rows="2" placeholder="Describe el propósito de este tipo de diagrama..."></textarea>
          </div>
          <div class="dt-form-row">
            <div class="dt-field">
              <label class="dt-label">Ícono (Material Symbol)</label>
              <input v-model="form.icon" class="dt-input" placeholder="sync_alt" />
              <span class="msym dt-icon-preview" :style="{ color: form.color || '#2563eb' }">{{ form.icon || 'circle' }}</span>
            </div>
            <div class="dt-field">
              <label class="dt-label">Color</label>
              <div class="dt-color-row">
                <input v-model="form.color" class="dt-input" placeholder="#2563eb" />
                <input type="color" v-model="form.color" class="dt-color-swatch" />
              </div>
            </div>
          </div>
          <div class="dt-field">
            <label class="dt-label">
              <span class="msym" style="font-size:14px;color:#7c3aed;vertical-align:middle">auto_awesome</span>
              AI Assist — Prompt de Sistema
            </label>
            <textarea
              v-model="form.ai_assist_prompt"
              class="dt-textarea dt-textarea--ai"
              rows="7"
              placeholder="Instrucciones para el AI Code Assist. Define qué tipo de código o activos debe generar a partir del diagrama. Debe pedir respuesta en JSON con la estructura: { title, description, artifacts: [{ filename, language, description, code }] }"></textarea>
            <p class="dt-field-hint">Este prompt se usa como instrucción base para el AI Code Assist en el editor de este tipo de diagrama.</p>
          </div>
        </div>
        <div class="dt-modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" :disabled="!form.id?.trim() || !form.name?.trim()" @click="save">
            {{ editTarget ? 'Guardar' : 'Crear' }}
            <span class="msym" style="font-size:15px">{{ editTarget ? 'save' : 'add_circle' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm delete -->
    <div v-if="deleteTarget" class="dt-overlay" @click.self="deleteTarget = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[420px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Eliminar Tipo de Diagrama</h3>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-700">¿Eliminar <strong>{{ deleteTarget.name }}</strong>? Las herramientas asociadas perderán este tipo de su lista.</p>
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
import { ref, onMounted } from 'vue'
import { useToolCatalogStore } from '@/stores/toolCatalog'
import { useUIStore } from '@/stores/ui'

const catalog = useToolCatalogStore()
const uiStore = useUIStore()

onMounted(async () => {
  await catalog.loadAll()
  uiStore.setBreadcrumbs(['Data Integration', 'Tipos de Diagrama'])
})

function toolCountFor(diagramTypeId) {
  return catalog.tools.filter(t => (t.applicable_diagram_types || []).includes(diagramTypeId)).length
}

const showModal   = ref(false)
const editTarget  = ref(null)
const deleteTarget = ref(null)
const emptyForm   = () => ({ id: '', name: '', description: '', icon: 'schema', color: '#2563eb', ai_assist_prompt: '' })
const form        = ref(emptyForm())

function openNew()    { editTarget.value = null; form.value = emptyForm(); showModal.value = true }
function openEdit(dt) { editTarget.value = dt; form.value = { id: dt.id, name: dt.name, description: dt.description || '', icon: dt.icon || 'schema', color: dt.color || '#2563eb', ai_assist_prompt: dt.ai_assist_prompt || '' }; showModal.value = true }
function closeModal() { showModal.value = false; editTarget.value = null; form.value = emptyForm() }
function confirmDelete(dt) { deleteTarget.value = dt }

function save() {
  if (editTarget.value) {
    catalog.updateDiagramType(editTarget.value.id, { name: form.value.name, description: form.value.description, icon: form.value.icon, color: form.value.color, ai_assist_prompt: form.value.ai_assist_prompt || null })
    uiStore.addAlert({ type: 'success', message: 'Tipo actualizado exitosamente' })
  } else {
    catalog.addDiagramType({ ...form.value })
    uiStore.addAlert({ type: 'success', message: 'Tipo creado exitosamente' })
  }
  closeModal()
}

function doDelete() {
  catalog.deleteDiagramType(deleteTarget.value.id)
  deleteTarget.value = null
  uiStore.addAlert({ type: 'success', message: 'Tipo eliminado exitosamente' })
}
</script>

<style scoped>
.msym {
  font-family: 'Material Symbols Outlined'; font-weight: normal; font-style: normal;
  font-size: 20px; line-height: 1; display: inline-flex; align-items: center; justify-content: center;
  white-space: nowrap; direction: ltr; -webkit-font-smoothing: antialiased;
}
.dt-h1  { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 36px; font-weight: 700; color: #0f172a; line-height: 1.2; letter-spacing: -0.02em; }
.dt-sub { font-family: 'Inter', sans-serif; font-size: 14px; }

.dt-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }

.dt-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
  display: flex; flex-direction: column; box-shadow: 0 1px 4px rgba(15,23,42,0.06);
  transition: box-shadow 0.2s, transform 0.2s; animation: dtFadeIn 0.35s ease forwards; opacity: 0;
}
@keyframes dtFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.dt-card:hover { box-shadow: 0 6px 24px rgba(15,23,42,0.1); transform: translateY(-2px); }
.dt-card-stripe { height: 4px; }
.dt-card-body { padding: 20px; flex: 1; display: flex; flex-direction: column; gap: 8px; }
.dt-card-ico { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }
.dt-card-name { font-size: 16px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; }
.dt-card-desc { font-size: 13px; color: #64748b; flex: 1; }
.dt-card-meta { margin-top: 8px; }
.dt-tools-badge { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 500; color: #64748b; background: #f1f5f9; border-radius: 20px; padding: 3px 10px; }
.dt-card-footer { display: flex; align-items: center; justify-content: flex-end; gap: 6px; padding: 12px 16px; border-top: 1px solid #f1f5f9; background: #fafafa; }
.dt-action { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; background: #fff; border-radius: 7px; cursor: pointer; color: #64748b; transition: all 0.15s; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.dt-action:hover { color: #2563eb; background: #eff6ff; }
.dt-action--danger:hover { color: #dc2626; background: #fef2f2; }
.dt-new-card {
  border: 2px dashed #e2e8f0; border-radius: 12px; padding: 32px; min-height: 220px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
  background: transparent; cursor: pointer; transition: all 0.2s;
}
.dt-new-card:hover { border-color: #2563eb; background: #eff6ff30; }
.dt-new-ico { width: 44px; height: 44px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
.dt-new-card:hover .dt-new-ico { background: #dbeafe; }
.dt-new-lbl { font-size: 13px; font-weight: 600; color: #64748b; }
.dt-new-card:hover .dt-new-lbl { color: #2563eb; }

/* Modal */
.dt-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; background: rgba(15,23,42,0.55); padding: 16px; }
.dt-modal { background: #fff; width: 100%; max-width: 520px; border-radius: 12px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); display: flex; flex-direction: column; max-height: calc(100vh - 32px); overflow: hidden; }
.dt-modal-hdr { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 20px 24px; border-bottom: 1px solid #e2e8f0; }
.dt-modal-title { font-size: 18px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; }
.dt-modal-sub { font-size: 13px; color: #64748b; margin-top: 2px; }
.dt-close-btn { width: 30px; height: 30px; border: none; background: transparent; border-radius: 50%; cursor: pointer; color: #64748b; display: flex; align-items: center; justify-content: center; transition: all 0.15s; flex-shrink: 0; }
.dt-close-btn:hover { background: #f1f5f9; }
.dt-modal-body { padding: 24px; overflow-y: auto; flex: 1; }
.dt-modal-footer { display: flex; align-items: center; justify-content: flex-end; gap: 12px; padding: 16px 24px; background: #f8fafc; border-top: 1px solid #e2e8f0; }
.dt-field { margin-bottom: 16px; position: relative; }
.dt-label { display: block; font-size: 13px; font-weight: 500; color: #0f172a; margin-bottom: 6px; }
.dt-input, .dt-textarea { width: 100%; box-sizing: border-box; padding: 9px 13px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 13px; background: #fff; outline: none; transition: all 0.15s; }
.dt-input:focus, .dt-textarea:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.dt-input:disabled { background: #f8fafc; color: #94a3b8; }
.dt-textarea { resize: none; }
.dt-textarea--ai { resize: vertical; min-height: 130px; font-family: 'Fira Code', 'Consolas', monospace; font-size: 11.5px; line-height: 1.6; }
.dt-field-hint { font-size: 11px; color: #94a3b8; margin-top: 5px; }
.dt-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.dt-color-row { display: flex; gap: 8px; align-items: center; }
.dt-color-swatch { width: 38px; height: 38px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 2px; cursor: pointer; flex-shrink: 0; }
.dt-icon-preview { position: absolute; right: 10px; bottom: 10px; font-size: 20px; pointer-events: none; opacity: 0.7; }
</style>
