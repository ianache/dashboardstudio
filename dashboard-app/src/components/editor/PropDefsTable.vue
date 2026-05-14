<!--
  PropDefsTable — Visual editor for tool property definitions.

  Manages a list of property definitions, each with:
    name, label, type, placeholder, defaultValue, options? (for select type)

  Props:
    modelValue: PropItem[]

  Emits:
    update:modelValue — updated array

  PropItem shape:
    { name, label, type, placeholder, defaultValue, options }
    where options is a JSON string for type=select
-->
<template>
  <div class="pdt-root">
    <!-- Table -->
    <div class="pdt-table-wrap">
      <table class="pdt-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Label</th>
            <th>Tipo</th>
            <th>Placeholder</th>
            <th>Valor por defecto</th>
            <th style="width:72px">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="6" class="pdt-empty">
              <span class="pdt-msi" style="font-size:24px;color:#cbd5e1">list_alt</span>
              <span>Sin propiedades definidas</span>
            </td>
          </tr>
          <tr v-for="(item, idx) in items" :key="item.name + idx" class="pdt-row">
            <td><code class="pdt-code">{{ item.name }}</code></td>
            <td><span class="pdt-cell">{{ item.label }}</span></td>
            <td>
              <span class="pdt-type-badge" :class="`pdt-type-${item.type}`">{{ item.type }}</span>
            </td>
            <td><span class="pdt-cell pdt-muted">{{ item.placeholder || '—' }}</span></td>
            <td><span class="pdt-cell pdt-muted">{{ item.defaultValue || '—' }}</span></td>
            <td>
              <div class="pdt-row-actions">
                <button class="pdt-act" title="Editar" @click="openEdit(idx)">
                  <span class="pdt-msi" style="font-size:15px">edit</span>
                </button>
                <button class="pdt-act pdt-act--del" title="Eliminar" @click="remove(idx)">
                  <span class="pdt-msi" style="font-size:15px">delete</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add button -->
    <button class="pdt-add-btn" @click="openNew">
      <span class="pdt-msi" style="font-size:16px">add</span>
      Añadir propiedad
    </button>

    <!-- Modal: New / Edit property -->
    <Teleport to="body">
      <div v-if="showModal" class="pdt-overlay" @click.self="closeModal">
        <div class="pdt-modal">
          <div class="pdt-modal-hdr">
            <div>
              <h3 class="pdt-modal-title">{{ editIdx !== null ? 'Editar propiedad' : 'Nueva propiedad' }}</h3>
              <p class="pdt-modal-sub">Define los atributos de la propiedad del componente.</p>
            </div>
            <button class="pdt-close" @click="closeModal"><span class="pdt-msi" style="font-size:16px">close</span></button>
          </div>

          <div class="pdt-modal-body">
            <div class="pdt-form-row">
              <div class="pdt-field">
                <label class="pdt-label">Nombre <span class="pdt-req">*</span></label>
                <input
                  v-model="form.name"
                  class="pdt-input"
                  placeholder="host"
                  :disabled="editIdx !== null"
                  @input="form.name = form.name.replace(/[^a-z0-9_]/g, '_').toLowerCase()"
                />
                <span class="pdt-hint">Solo letras minúsculas, números y guión bajo</span>
              </div>
              <div class="pdt-field">
                <label class="pdt-label">Label <span class="pdt-req">*</span></label>
                <input v-model="form.label" class="pdt-input" placeholder="Host" />
              </div>
            </div>

            <div class="pdt-form-row">
              <div class="pdt-field">
                <label class="pdt-label">Tipo <span class="pdt-req">*</span></label>
                <div class="pdt-sel-wrap">
                  <select v-model="form.type" class="pdt-input pdt-sel">
                    <option value="text">text — Campo de texto</option>
                    <option value="textarea">textarea — Área de texto</option>
                    <option value="select">select — Lista desplegable</option>
                    <option value="number">number — Campo numérico</option>
                  </select>
                  <span class="pdt-msi pdt-sel-arr" style="font-size:16px">expand_more</span>
                </div>
              </div>
              <div class="pdt-field">
                <label class="pdt-label">Placeholder</label>
                <input v-model="form.placeholder" class="pdt-input" placeholder="Ej: localhost" />
              </div>
            </div>

            <div class="pdt-field">
              <label class="pdt-label">Valor por defecto</label>
              <input v-model="form.defaultValue" class="pdt-input" placeholder="Dejar vacío si no hay valor por defecto" />
            </div>

            <!-- Options (only for select type) -->
            <div v-if="form.type === 'select'" class="pdt-field">
              <label class="pdt-label">
                Opciones (JSON)
                <span class="pdt-hint" style="margin-left:8px">[{"value":"a","label":"A"}, ...]</span>
              </label>
              <textarea
                v-model="form.options"
                class="pdt-input pdt-textarea"
                rows="4"
                placeholder='[{"value":"option1","label":"Opción 1"},{"value":"option2","label":"Opción 2"}]'
              ></textarea>
              <span v-if="optionsError" class="pdt-err">{{ optionsError }}</span>
            </div>

            <!-- Rows (only for textarea type) -->
            <div v-if="form.type === 'textarea'" class="pdt-field" style="max-width:120px">
              <label class="pdt-label">Filas visibles</label>
              <input v-model.number="form.rows" type="number" min="2" max="12" class="pdt-input" />
            </div>
          </div>

          <div class="pdt-modal-footer">
            <button class="btn btn-ghost" @click="closeModal">Cancelar</button>
            <button class="btn btn-primary" :disabled="!canSave" @click="saveItem">
              {{ editIdx !== null ? 'Guardar' : 'Añadir' }}
              <span class="pdt-msi" style="font-size:14px">{{ editIdx !== null ? 'save' : 'add_circle' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

// ─── Internal items list ──────────────────────────────────────────────────────
const items = ref([])

watch(() => props.modelValue, (val) => {
  items.value = val ? JSON.parse(JSON.stringify(val)) : []
}, { immediate: true, deep: true })

// ─── Modal state ──────────────────────────────────────────────────────────────
const showModal = ref(false)
const editIdx   = ref(null)

const emptyForm = () => ({ name: '', label: '', type: 'text', placeholder: '', defaultValue: '', options: '[]', rows: 3 })
const form = ref(emptyForm())

const optionsError = computed(() => {
  if (form.value.type !== 'select') return ''
  try { JSON.parse(form.value.options); return '' } catch (e) { return 'JSON inválido: ' + e.message }
})

const canSave = computed(() =>
  form.value.name.trim() !== '' && form.value.label.trim() !== '' && !optionsError.value
)

function openNew() {
  editIdx.value = null
  form.value = emptyForm()
  showModal.value = true
}

function openEdit(idx) {
  editIdx.value = idx
  const item = items.value[idx]
  form.value = {
    name:         item.name,
    label:        item.label,
    type:         item.type || 'text',
    placeholder:  item.placeholder || '',
    defaultValue: item.defaultValue ?? '',
    options:      item.options ? (typeof item.options === 'string' ? item.options : JSON.stringify(item.options, null, 2)) : '[]',
    rows:         item.rows || 3,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editIdx.value = null
  form.value = emptyForm()
}

function saveItem() {
  if (!canSave.value) return

  const newItem = {
    name:         form.value.name.trim(),
    label:        form.value.label.trim(),
    type:         form.value.type,
    placeholder:  form.value.placeholder.trim(),
    defaultValue: form.value.defaultValue,
    ...(form.value.type === 'select'   && { options: form.value.options }),
    ...(form.value.type === 'textarea' && { rows: form.value.rows }),
  }

  if (editIdx.value !== null) {
    items.value[editIdx.value] = newItem
  } else {
    // Check for duplicate name
    if (items.value.some(i => i.name === newItem.name)) {
      alert(`Ya existe una propiedad con el nombre "${newItem.name}"`)
      return
    }
    items.value.push(newItem)
  }

  emit('update:modelValue', JSON.parse(JSON.stringify(items.value)))
  closeModal()
}

function remove(idx) {
  items.value.splice(idx, 1)
  emit('update:modelValue', JSON.parse(JSON.stringify(items.value)))
}
</script>

<style scoped>
.pdt-msi {
  font-family: 'Material Symbols Outlined'; font-weight: normal; font-style: normal;
  font-size: 20px; line-height: 1; display: inline-flex; align-items: center; justify-content: center;
  white-space: nowrap; direction: ltr; -webkit-font-smoothing: antialiased;
}

.pdt-root { display: flex; flex-direction: column; gap: 8px; }

/* Table */
.pdt-table-wrap {
  border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;
  background: #fff;
}
.pdt-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.pdt-table th {
  padding: 8px 12px; text-align: left;
  font-size: 10px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.06em;
  background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.pdt-table td { padding: 9px 12px; vertical-align: middle; border-bottom: 1px solid #f1f5f9; color: #334155; }
.pdt-row:last-child td { border-bottom: none; }
.pdt-row:hover td { background: #f8fafc; }

.pdt-empty { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 24px 0; font-size: 12px; color: #94a3b8; }
.pdt-code { font-family: 'Fira Code', monospace; font-size: 11px; background: #f1f5f9; color: #2563eb; padding: 2px 6px; border-radius: 4px; }
.pdt-cell { font-size: 12px; }
.pdt-muted { color: #94a3b8; }
.pdt-type-badge { font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 4px; white-space: nowrap; }
.pdt-type-text     { background: #f1f5f9; color: #475569; }
.pdt-type-textarea { background: #faf5ff; color: #7c3aed; }
.pdt-type-select   { background: #fff7ed; color: #c2410c; }
.pdt-type-number   { background: #f0fdf4; color: #16a34a; }

.pdt-row-actions { display: flex; gap: 2px; }
.pdt-act { width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; border: none; background: transparent; border-radius: 5px; cursor: pointer; color: #94a3b8; transition: all 0.12s; }
.pdt-act:hover { color: #2563eb; background: #eff6ff; }
.pdt-act--del:hover { color: #dc2626; background: #fef2f2; }

/* Add button */
.pdt-add-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border: 1px dashed #cbd5e1; border-radius: 7px;
  background: transparent; cursor: pointer; font-size: 12px; font-weight: 500;
  color: #64748b; transition: all 0.15s; align-self: flex-start;
}
.pdt-add-btn:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }

/* Modal overlay */
.pdt-overlay {
  position: fixed; inset: 0; z-index: 2000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(15,23,42,0.55); padding: 16px;
}
.pdt-modal {
  background: #fff; width: 100%; max-width: 560px; border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  display: flex; flex-direction: column; max-height: calc(100vh - 32px); overflow: hidden;
}
.pdt-modal-hdr {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;
  padding: 18px 22px; border-bottom: 1px solid #e2e8f0; flex-shrink: 0;
}
.pdt-modal-title { font-size: 16px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; }
.pdt-modal-sub   { font-size: 12px; color: #64748b; margin-top: 2px; }
.pdt-close { width: 28px; height: 28px; border: none; background: transparent; border-radius: 50%; cursor: pointer; color: #64748b; display: flex; align-items: center; justify-content: center; transition: all 0.12s; flex-shrink: 0; }
.pdt-close:hover { background: #f1f5f9; }
.pdt-modal-body { padding: 20px 22px; overflow-y: auto; flex: 1; }
.pdt-modal-footer { display: flex; align-items: center; justify-content: flex-end; gap: 10px; padding: 14px 22px; background: #f8fafc; border-top: 1px solid #e2e8f0; flex-shrink: 0; }

/* Form */
.pdt-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.pdt-field { margin-bottom: 14px; position: relative; }
.pdt-label { display: block; font-size: 11px; font-weight: 600; color: #334155; margin-bottom: 5px; }
.pdt-req { color: #dc2626; }
.pdt-hint { font-size: 10px; color: #94a3b8; font-weight: 400; }
.pdt-input { width: 100%; box-sizing: border-box; padding: 7px 11px; border: 1px solid #cbd5e1; border-radius: 7px; font-size: 12px; background: #fff; outline: none; transition: all 0.15s; font-family: inherit; }
.pdt-input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.pdt-input:disabled { background: #f8fafc; color: #94a3b8; }
.pdt-sel-wrap { position: relative; }
.pdt-sel { padding-right: 28px; appearance: none; cursor: pointer; }
.pdt-sel-arr { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); color: #64748b; pointer-events: none; }
.pdt-textarea { resize: vertical; min-height: 72px; font-family: 'Fira Code', monospace; font-size: 11px; }
.pdt-err { display: block; font-size: 10px; color: #dc2626; margin-top: 3px; }
</style>
