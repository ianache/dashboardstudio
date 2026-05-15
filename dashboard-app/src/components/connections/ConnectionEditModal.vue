<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h2>{{ connection ? 'Editar Conexión' : 'Nueva Conexión' }}</h2>
      <form @submit.prevent="save">
        <div class="form-group">
          <label>Nombre</label>
          <input v-model="form.name" required />
        </div>
        <div class="form-group">
          <label>Tipo</label>
          <select v-model="form.type" required @change="updateConfigStructure">
            <option value="smtp">SMTP (Email)</option>
            <option value="database">Base de Datos</option>
            <option value="ftp">FTP / SFTP</option>
            <option value="http">HTTP (Basic)</option>
            <option value="jwt">JWT Token</option>
          </select>
        </div>

        <div class="config-fields">
          <div v-for="(val, key) in form.connection_config" :key="key" class="form-group">
            <label>{{ formatLabel(key) }}</label>
            <input v-if="typeof val !== 'boolean'" v-model="form.connection_config[key]" />
            <input v-else type="checkbox" v-model="form.connection_config[key]" />
          </div>
        </div>

        <div class="actions">
          <button type="button" class="btn-sec" @click="test">Probar</button>
          <button type="submit" class="btn-pri">Guardar</button>
        </div>
        <p v-if="testResult" :class="{'success': testResult.success, 'error': !testResult.success}">
          {{ testResult.message }}
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/services/api'

const props = defineProps(['connection'])
const emit = defineEmits(['close', 'saved'])

const form = ref(props.connection ? { ...props.connection } : { 
  name: '', type: 'smtp', connection_config: { host: '', port: 587, email: '', password: '' } 
})
const testResult = ref(null)

const updateConfigStructure = () => {
  const defaults = {
    smtp: { host: '', port: 587, use_ssl: true, email: '', password: '' },
    database: { host: '', port: 5432, username: '', password: '', database: '', schema: 'public' },
    ftp: { host: '', port: 21, username: '', password: '', protocol: 'ftp' },
    http: { url: '', username: '', password: '' },
    jwt: { token_url: '', username: '', password: '', client_id: '', client_secret: '' }
  }
  form.value.connection_config = defaults[form.value.type]
}

const formatLabel = (key) => key.replace('_', ' ').toUpperCase()

const save = async () => {
  if (form.value.id) await api.put(`/data-sources/${form.value.id}`, form.value)
  else await api.post('/data-sources', form.value)
  emit('saved')
  emit('close')
}

const test = async () => {
  if (!form.value.id) {
    alert("Guarda la conexión antes de probarla.");
    return;
  }
  try {
    const { data } = await api.post(`/data-sources/${form.value.id}/test`)
    testResult.value = { success: data.success, message: data.success ? 'Conexión exitosa' : (data.message || 'Error de conexión') }
  } catch (e) {
    testResult.value = { success: false, message: 'Error al realizar el test' }
  }
}
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: white; padding: 24px; border-radius: 8px; width: 400px; }
.form-group { margin-bottom: 16px; display: flex; flex-direction: column; }
.actions { display: flex; gap: 8px; margin-top: 20px; }
.btn-pri { background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
.btn-sec { background: #f1f5f9; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
.success { color: #16a34a; font-size: 13px; }
.error { color: #dc2626; font-size: 13px; }
</style>
