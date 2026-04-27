<template>
  <div class="min-h-[calc(100vh-64px)] p-8">
    <!-- Page Header -->
    <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
      <div class="space-y-1">
        <h1 class="font-h1 text-h1 text-slate-900" style="">Tipos de Datos</h1>
        <p class="font-body-md text-slate-500 max-w-2xl" style="">Define los tipos SQL reutilizables para
          los campos de tus modelos dimensionales.</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-all shadow-sm"
          @click="confirmReset">
          <span class="material-symbols-outlined text-lg" style="">history</span>
          Defaults</button>
        <input ref="importFileInput" type="file" accept=".json" style="display:none" @change="handleImportFile" />
        <button
          class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-all shadow-sm"
          @click="importFileInput.click()">
          <span class="material-symbols-outlined text-lg" style="">download</span>
          Import
        </button>
        <button
          class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-all shadow-sm"
          @click="exportTypes">
          <span class="material-symbols-outlined text-lg" style="">upload</span>
          Export
        </button>
        <button
          class="flex items-center gap-2 px-5 py-2 text-sm font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 active:scale-95"
          @click="startAdd">
          <span class="material-symbols-outlined text-lg" style="">add</span>
          Nuevo</button>
      </div>
    </div>

    <!-- Table Container -->
    <div
      class="max-w-[1600px] mx-auto bg-white rounded-xl border border-slate-200 shadow-[0px_4px_20px_rgba(15,23,42,0.05)] overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50/50 border-b border-slate-200">
              <th class="px-6 py-4 font-label-md text-slate-500 uppercase tracking-wider" style="">
                Nombre</th>
              <th class="px-6 py-4 font-label-md text-slate-500 uppercase tracking-wider" style="">
                Tipo Base SQL</th>
              <th class="px-6 py-4 font-label-md text-slate-500 uppercase tracking-wider" style="">
                Tamaño / Precisión</th>
              <th class="px-6 py-4 font-label-md text-slate-500 uppercase tracking-wider" style="">SQL
                Completo</th>
              <th class="px-6 py-4 font-label-md text-slate-500 uppercase tracking-wider" style="">
                Descripción</th>
              <th class="px-6 py-4 font-label-md text-slate-500 uppercase tracking-wider text-right"
                style="">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <!-- New row form -->
            <tr v-if="adding" class="bg-blue-50/50">
              <td class="px-6 py-4">
                <input v-model="form.name" type="text" class="form-input w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Ej: Código" autofocus />
              </td>
              <td class="px-6 py-4">
                <select v-model="form.baseType" class="form-select w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500" @change="onBaseTypeChange(form)">
                  <option v-for="b in BASE_TYPES" :key="b.value" :value="b.value">{{ b.value }}</option>
                </select>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <input
                    v-if="baseMeta(form.baseType)?.hasSize"
                    v-model.number="form.size"
                    type="number" min="1" max="65535"
                    class="form-input w-20 px-2 py-1 text-sm border border-slate-300 rounded-md"
                    placeholder="Tam."
                  />
                  <span v-if="baseMeta(form.baseType)?.hasPrecision" class="text-slate-400 font-medium">,</span>
                  <input
                    v-if="baseMeta(form.baseType)?.hasPrecision"
                    v-model.number="form.precision"
                    type="number" min="0" max="30"
                    class="form-input w-20 px-2 py-1 text-sm border border-slate-300 rounded-md"
                    placeholder="Prec."
                  />
                  <span v-if="!baseMeta(form.baseType)?.hasSize" class="text-slate-400">—</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-block px-2 py-1 text-xs font-mono font-medium bg-emerald-50 text-emerald-700 rounded">{{ previewSql(form) }}</span>
              </td>
              <td class="px-6 py-4">
                <input v-model="form.description" type="text" class="form-input w-full px-3 py-2 text-sm border border-slate-300 rounded-md" placeholder="Descripción opcional" />
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button class="px-3 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed" :disabled="!form.name.trim()" @click="saveAdd">Añadir</button>
                  <button class="px-3 py-1.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-md hover:bg-slate-50" @click="cancelAdd">Cancelar</button>
                </div>
              </td>
            </tr>

            <!-- Existing rows -->
            <tr v-for="dt in dtStore.allTypes" :key="dt.id" :class="{ 'bg-blue-50/30': editingId === dt.id }" class="hover:bg-blue-50/30 transition-colors group">
              <!-- View mode -->
              <template v-if="editingId !== dt.id">
                <td class="px-6 py-4 font-semibold text-slate-900">{{ dt.name }}</td>
                <td class="px-6 py-4">
                  <span class="inline-block px-2 py-1 text-xs font-mono font-medium bg-blue-50 text-blue-600 rounded">{{ dt.baseType }}</span>
                </td>
                <td class="px-6 py-4 text-slate-600 font-medium">{{ sizeLabel(dt) }}</td>
                <td class="px-6 py-4">
                  <span class="inline-block px-2 py-1 text-xs font-mono font-medium bg-emerald-50 text-emerald-700 rounded">{{ dtStore.sqlOf(dt.id) }}</span>
                </td>
                <td class="px-6 py-4 text-slate-500 text-sm">{{ dt.description || '—' }}</td>
                <td class="px-6 py-4 text-right">
                  <div class="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-all"
                      @click="startEditRow(dt)"
                      title="Editar">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                    </button>
                    <button
                      class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-all"
                      @click="confirmDelete(dt)"
                      title="Eliminar">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                        <path d="M10 11v6M14 11v6"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </template>

              <!-- Edit mode -->
              <template v-else>
                <td class="px-6 py-4">
                  <input v-model="form.name" type="text" class="form-input w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                </td>
                <td class="px-6 py-4">
                  <select v-model="form.baseType" class="form-select w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500" @change="onBaseTypeChange(form)">
                    <option v-for="b in BASE_TYPES" :key="b.value" :value="b.value">{{ b.value }}</option>
                  </select>
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <input
                      v-if="baseMeta(form.baseType)?.hasSize"
                      v-model.number="form.size"
                      type="number" min="1" max="65535"
                      class="form-input w-20 px-2 py-1 text-sm border border-slate-300 rounded-md"
                      placeholder="Tam."
                    />
                    <span v-if="baseMeta(form.baseType)?.hasPrecision" class="text-slate-400 font-medium">,</span>
                    <input
                      v-if="baseMeta(form.baseType)?.hasPrecision"
                      v-model.number="form.precision"
                      type="number" min="0" max="30"
                      class="form-input w-20 px-2 py-1 text-sm border border-slate-300 rounded-md"
                      placeholder="Prec."
                    />
                    <span v-if="!baseMeta(form.baseType)?.hasSize" class="text-slate-400">—</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span class="inline-block px-2 py-1 text-xs font-mono font-medium bg-emerald-50 text-emerald-700 rounded">{{ previewSql(form) }}</span>
                </td>
                <td class="px-6 py-4">
                  <input v-model="form.description" type="text" class="form-input w-full px-3 py-2 text-sm border border-slate-300 rounded-md" placeholder="Descripción" />
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="flex justify-end gap-2">
                    <button class="px-3 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed" :disabled="!form.name.trim()" @click="saveEditRow(dt.id)">Guardar</button>
                    <button class="px-3 py-1.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-md hover:bg-slate-50" @click="cancelEdit">Cancelar</button>
                  </div>
                </td>
              </template>
            </tr>

            <tr v-if="!dtStore.allTypes.length && !adding">
              <td colspan="6" class="px-6 py-12 text-center text-slate-400">
                Sin tipos definidos. Haz clic en "Nuevo" para añadir.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer/Pagination -->
      <div v-if="dtStore.allTypes.length > 0" class="px-6 py-4 bg-slate-50/30 border-t border-slate-200 flex items-center justify-between">
        <span class="text-sm text-slate-500 font-medium">{{ dtStore.allTypes.length }} tipo(s) definido(s)</span>
      </div>
    </div>

    <!-- Bento Info Section -->
    <div class="max-w-[1600px] mx-auto mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-6 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col gap-4">
        <div class="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center">
          <span class="material-symbols-outlined text-indigo-600" style="">auto_awesome</span>
        </div>
        <div>
          <h4 class="font-bold text-slate-900" style="">Validación Automática</h4>
          <p class="text-sm text-slate-500 mt-1" style="">Sugerencias basadas en el motor SQL seleccionado
            para prevenir errores de casting.</p>
        </div>
      </div>
      <div class="p-6 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col gap-4">
        <div class="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center">
          <span class="material-symbols-outlined text-emerald-600" style="">terminal</span>
        </div>
        <div>
          <h4 class="font-bold text-slate-900" style="">Compatibilidad ANSI</h4>
          <p class="text-sm text-slate-500 mt-1" style="">Tipos configurados para ser portables entre
            Postgres, Snowflake y BigQuery.</p>
        </div>
      </div>
      <div class="p-6 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col gap-4">
        <div class="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center">
          <span class="material-symbols-outlined text-orange-600" style="">security</span>
        </div>
        <div>
          <h4 class="font-bold text-slate-900" style="">Control de Precisión</h4>
          <p class="text-sm text-slate-500 mt-1" style="">Definición estricta de escala para asegurar
            integridad en reportes financieros.</p>
        </div>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="deleteTarget = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[420px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Eliminar tipo de dato</h3>
        </div>
        <div class="px-6 py-5 flex flex-col gap-3">
          <p class="text-sm text-slate-700">¿Eliminar <strong>{{ deleteTarget.name }}</strong> (<code class="px-1.5 py-0.5 text-xs font-mono bg-emerald-50 text-emerald-700 rounded">{{ dtStore.sqlOf(deleteTarget.id) }}</code>)?</p>
          <p class="text-xs text-amber-700 bg-amber-50 p-3 rounded-lg">Los campos que usen este tipo conservarán su referencia pero no se podrán resolver.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="deleteTarget = null">Cancelar</button>
          <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700" @click="doDelete">Eliminar</button>
        </div>
      </div>
    </div>

    <!-- Import preview modal -->
    <div v-if="importPreview" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="importPreview = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[480px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Importar tipos de datos</h3>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="importPreview = null">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5 flex flex-col gap-4">
          <div v-if="importPreview.toAdd.length" class="flex flex-col gap-2">
            <p class="flex items-center gap-2 text-sm font-semibold text-emerald-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              {{ importPreview.toAdd.length }} tipo(s) nuevos a agregar
            </p>
            <ul class="pl-5 text-sm text-slate-700 space-y-1">
              <li v-for="dt in importPreview.toAdd" :key="dt.name" class="flex items-center gap-2">
                <strong>{{ dt.name }}</strong> <code class="px-1.5 py-0.5 text-xs font-mono bg-emerald-50 text-emerald-700 rounded">{{ previewSql(dt) }}</code>
              </li>
            </ul>
          </div>
          <div v-if="importPreview.toReplace.length" class="flex flex-col gap-2">
            <p class="flex items-center gap-2 text-sm font-semibold text-amber-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.59"/></svg>
              {{ importPreview.toReplace.length }} tipo(s) a reemplazar (mismo nombre)
            </p>
            <ul class="pl-5 text-sm text-slate-700 space-y-1">
              <li v-for="dt in importPreview.toReplace" :key="dt.name" class="flex items-center gap-2">
                <strong>{{ dt.name }}</strong> <code class="px-1.5 py-0.5 text-xs font-mono bg-emerald-50 text-emerald-700 rounded">{{ previewSql(dt) }}</code>
              </li>
            </ul>
          </div>
          <p v-if="!importPreview.toAdd.length && !importPreview.toReplace.length" class="text-sm text-amber-700 bg-amber-50 p-3 rounded-lg">
            El archivo no contiene tipos de datos.
          </p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="importPreview = null">Cancelar</button>
          <button
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!importPreview.toAdd.length && !importPreview.toReplace.length"
            @click="doImport"
          >Importar</button>
        </div>
      </div>
    </div>

    <!-- Reset confirm modal -->
    <div v-if="showResetConfirm" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="showResetConfirm = false">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[420px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Restaurar tipos predeterminados</h3>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-700">Se reemplazarán todos los tipos actuales por los predeterminados. ¿Continuar?</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="showResetConfirm = false">Cancelar</button>
          <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700" @click="doReset">Restaurar</button>
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

// ── Export ────────────────────────────────────────────────────
function exportTypes() {
  const payload = {
    __dashboardStudio: true,
    type: 'dataTypes',
    version: '1.0',
    exportedAt: new Date().toISOString(),
    dataTypes: dtStore.allTypes.map(({ id, name, baseType, size, precision, description }) => ({
      id, name, baseType, size, precision, description
    }))
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'tipos-de-datos.datatypes.json'
  a.click()
  URL.revokeObjectURL(url)
}

// ── Import ────────────────────────────────────────────────────
const importFileInput = ref(null)
const importPreview = ref(null)

function handleImportFile(e) {
  const file = e.target.files[0]
  if (!file) return
  e.target.value = ''
  const reader = new FileReader()
  reader.onload = (evt) => {
    try {
      const data = JSON.parse(evt.target.result)
      if (!data.__dashboardStudio || data.type !== 'dataTypes' || !Array.isArray(data.dataTypes)) {
        uiStore.addAlert({ type: 'error', message: 'Archivo inválido: no es un export de tipos de datos.' })
        return
      }
      const toAdd = []
      const toReplace = []
      for (const dt of data.dataTypes) {
        const existing = dtStore.allTypes.find(t => t.name.toLowerCase() === dt.name.toLowerCase())
        if (existing) {
          toReplace.push({ ...dt, existingId: existing.id })
        } else {
          toAdd.push(dt)
        }
      }
      importPreview.value = { toAdd, toReplace }
    } catch {
      uiStore.addAlert({ type: 'error', message: 'Error al leer el archivo.' })
    }
  }
  reader.readAsText(file)
}

function doImport() {
  if (!importPreview.value) return
  const { toAdd, toReplace } = importPreview.value
  for (const dt of toReplace) {
    dtStore.updateType(dt.existingId, {
      name: dt.name,
      baseType: dt.baseType,
      size: dt.size ?? null,
      precision: dt.precision ?? null,
      description: dt.description || ''
    })
  }
  for (const dt of toAdd) {
    dtStore.addType({
      name: dt.name,
      baseType: dt.baseType,
      size: dt.size ?? null,
      precision: dt.precision ?? null,
      description: dt.description || ''
    })
  }
  importPreview.value = null
  uiStore.addAlert({ type: 'success', message: `Importación completada: ${toAdd.length} añadidos, ${toReplace.length} reemplazados.` })
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
/* Material Symbols font */
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

/* Custom font classes matching the design system */
.font-h1 {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.font-body-md {
  font-family: 'Inter', system-ui, sans-serif;
}

.font-label-md {
  font-family: 'Inter', system-ui, sans-serif;
}

.text-h1 {
  font-size: 36px;
  line-height: 1.2;
  letter-spacing: -0.02em;
  font-weight: 700;
}

/* Form inputs */
.form-input:focus,
.form-select:focus {
  outline: none;
}

/* Table row hover effect */
tr.group:hover .opacity-0 {
  opacity: 1;
}
</style>
