<template>
  <div class="conn-overlay" @click.self="$emit('close')">
    <div class="conn-modal">

      <!-- Header -->
      <div class="conn-modal-header">
        <div class="conn-modal-header-inner">
          <div>
            <h2 class="conn-modal-title">{{ connection ? 'Editar Conexión' : 'Nueva Conexión' }}</h2>
            <p class="conn-modal-sub">{{ connection ? 'Modifica los parámetros de acceso.' : 'Configura una nueva fuente o destino de datos.' }}</p>
          </div>
          <button class="conn-modal-close-btn" @click="$emit('close')">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="conn-modal-body">

        <!-- Name -->
        <div class="conn-field">
          <label class="conn-label">Nombre de la conexión</label>
          <input v-model="form.name" type="text" class="conn-input" placeholder="Ej: PostgreSQL ODS Producción" autofocus />
        </div>

        <!-- Type -->
        <div class="conn-field">
          <label class="conn-label">Tipo de conexión</label>
          <div class="conn-select-wrap">
            <select v-model="form.type" class="conn-select" @change="updateConfigStructure">
              <option v-for="ct in CONN_TYPES" :key="ct.value" :value="ct.value">{{ ct.label }}</option>
            </select>
            <span class="material-symbols-outlined conn-select-arrow">expand_more</span>
          </div>
        </div>

        <!-- Dynamic config fields -->
        <div class="conn-section-title">Configuración de acceso</div>
        <div class="conn-form-grid">
          <div v-for="(val, key) in form.connection_config" :key="key" class="conn-field">
            <label class="conn-label">{{ formatLabel(key) }}</label>
            <input
              v-if="typeof val !== 'boolean'"
              v-model="form.connection_config[key]"
              :type="sensitiveKey(key) ? 'password' : 'text'"
              class="conn-input"
              :placeholder="placeholder(key)"
            />
            <label v-else class="conn-toggle">
              <input type="checkbox" v-model="form.connection_config[key]" class="conn-checkbox" />
              <span>Habilitado</span>
            </label>
          </div>
        </div>

        <!-- Test result -->
        <div v-if="testResult" class="conn-test-result" :class="testResult.success ? 'conn-test-ok' : 'conn-test-err'">
          <span class="material-symbols-outlined" style="font-size:16px">{{ testResult.success ? 'check_circle' : 'error' }}</span>
          {{ testResult.message }}
        </div>

      </div>

      <!-- Footer -->
      <div class="conn-modal-footer">
        <button class="btn btn-ghost" type="button" @click="$emit('close')">Cancelar</button>
        <button class="btn btn-ghost" type="button" :disabled="!form.id || testing" @click="test">
          <span class="material-symbols-outlined" style="font-size:16px">wifi_tethering</span>
          {{ testing ? 'Probando…' : 'Probar' }}
        </button>
        <button class="btn btn-primary" type="button" :disabled="!form.name?.trim() || saving" @click="save">
          <span>{{ connection ? 'Guardar' : 'Crear' }}</span>
          <span class="material-symbols-outlined" style="font-size:16px">{{ connection ? 'save' : 'add_circle' }}</span>
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { dataSourcesApi } from '@/services/api'
import { CONN_TYPES, CONN_DEFAULTS } from '@/constants/connectionTypes'

const props = defineProps(['connection'])
const emit  = defineEmits(['close', 'saved'])

// ─── Config templates per type (from shared constants) ──────────────────
const DEFAULTS = CONN_DEFAULTS

const SENSITIVE = new Set(['password', 'client_secret', 'api_key', 'token'])
const PLACEHOLDERS = {
  host: 'db.example.com', port: '5432', email: 'user@domain.com',
  url: 'https://api.example.com', token_url: 'https://auth.example.com/token',
  username: 'admin', database: 'mydb', schema: 'public',
  client_id: 'client-id', protocol: 'ftp',
}

// ─── Form state ────────────────────────────────────────────────────────────
const form = ref(
  props.connection
    ? { ...props.connection }
    : { name: '', type: 'database', connection_config: { ...DEFAULTS.database } }
)
const testResult = ref(null)
const saving     = ref(false)
const testing    = ref(false)

function updateConfigStructure() {
  form.value.connection_config = { ...DEFAULTS[form.value.type] }
  testResult.value = null
}

function formatLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
function sensitiveKey(key) { return SENSITIVE.has(key) }
function placeholder(key)  { return PLACEHOLDERS[key] || '' }

// ─── Actions ───────────────────────────────────────────────────────────────
async function save() {
  if (!form.value.name?.trim()) return
  saving.value = true
  try {
    if (form.value.id) await dataSourcesApi.update(form.value.id, form.value)
    else               await dataSourcesApi.create(form.value)
    emit('saved')
    emit('close')
  } catch (e) {
    testResult.value = { success: false, message: 'Error al guardar: ' + (e.message || 'desconocido') }
  } finally {
    saving.value = false
  }
}

async function test() {
  if (!form.value.id) return
  testing.value = true
  testResult.value = null
  try {
    const data = await dataSourcesApi.testConnection(form.value.id)
    testResult.value = { success: data.success, message: data.success ? 'Conexión exitosa ✓' : (data.message || 'Error de conexión') }
  } catch (e) {
    testResult.value = { success: false, message: 'Error al probar la conexión' }
  } finally {
    testing.value = false
  }
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

/* Overlay */
.conn-overlay {
  position: fixed; inset: 0; z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(15,23,42,0.55); padding: 16px;
}

/* Modal shell */
.conn-modal {
  background: #fff;
  width: 100%; max-width: 560px;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  display: flex; flex-direction: column;
  max-height: calc(100vh - 32px);
  overflow: hidden;
}

/* Header */
.conn-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.conn-modal-header-inner {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px;
}
.conn-modal-title {
  font-size: 20px; font-weight: 700; color: #0f172a;
  margin: 0 0 4px 0;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}
.conn-modal-sub { font-size: 13px; color: #64748b; margin: 0; }
.conn-modal-close-btn {
  width: 32px; height: 32px;
  border: none; background: transparent;
  border-radius: 50%; cursor: pointer;
  color: #64748b; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s; flex-shrink: 0;
}
.conn-modal-close-btn:hover { background: #f1f5f9; color: #334155; }

/* Body */
.conn-modal-body { padding: 24px; overflow-y: auto; flex: 1; }

/* Footer */
.conn-modal-footer {
  display: flex; align-items: center;
  justify-content: flex-end; gap: 10px;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

/* Section title */
.conn-section-title {
  font-size: 11px; font-weight: 700; color: #475569;
  text-transform: uppercase; letter-spacing: 0.07em;
  margin: 4px 0 12px;
}

/* Form layout */
.conn-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.conn-field { margin-bottom: 18px; }
.conn-field:last-child { margin-bottom: 0; }

/* Labels */
.conn-label {
  display: block; font-size: 13px; font-weight: 500;
  color: #0f172a; margin-bottom: 6px;
}

/* Inputs */
.conn-input,
.conn-select {
  width: 100%; padding: 9px 13px;
  border: 1px solid #cbd5e1; border-radius: 8px;
  font-size: 13px; background: #fff; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box; font-family: inherit;
}
.conn-input::placeholder { color: #94a3b8; }
.conn-input:focus,
.conn-select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}

/* Select wrapper */
.conn-select-wrap { position: relative; }
.conn-select { padding-right: 36px; appearance: none; cursor: pointer; }
.conn-select-arrow {
  position: absolute; right: 10px; top: 50%;
  transform: translateY(-50%);
  color: #64748b; font-size: 18px; pointer-events: none;
}

/* Toggle (boolean fields) */
.conn-toggle {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #334155; cursor: pointer;
}
.conn-checkbox { width: 16px; height: 16px; accent-color: #2563eb; cursor: pointer; }

/* Test result */
.conn-test-result {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border-radius: 8px;
  font-size: 13px; font-weight: 500; margin-top: 4px;
}
.conn-test-ok  { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.conn-test-err { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
</style>
