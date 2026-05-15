<template>
  <div class="connections-view">
    <div class="cv-header">
      <div class="cv-title">
        <h1>Conexiones</h1>
        <p>Administra tus fuentes y destinos de integración.</p>
      </div>
      <button class="cv-add-btn" @click="openNewModal">
        <MIcon icon="add" :size="20" /> Nueva Conexión
      </button>
    </div>

    <div class="cv-content">
      <div v-if="loading" class="cv-loading">Cargando conexiones...</div>
      <div v-else-if="connections.length === 0" class="cv-empty">
        <MIcon icon="hub" :size="48" />
        <p>No hay conexiones configuradas.</p>
        <button class="cv-add-btn" @click="openNewModal">Crear primera conexión</button>
      </div>
      <div v-else class="cv-list">
        <div v-for="conn in connections" :key="conn.id" class="cv-item">
          <div class="cv-item-info">
            <MIcon :icon="getTypeIcon(conn.type)" :size="24" />
            <div class="cv-item-text">
              <span class="cv-item-name">{{ conn.name }}</span>
              <span class="cv-item-type">{{ conn.type.toUpperCase() }}</span>
            </div>
          </div>
          <div class="cv-item-actions">
            <button class="cv-action" @click="editConn(conn)">
              <MIcon icon="edit" :size="18" />
            </button>
            <button class="cv-action delete" @click="deleteConn(conn)">
              <MIcon icon="delete" :size="18" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <ConnectionEditModal 
      v-if="showModal" 
      :connection="editingConn" 
      @close="showModal = false" 
      @saved="fetchConnections" 
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import MIcon from '@/components/common/MIcon.vue'
import ConnectionEditModal from '@/components/connections/ConnectionEditModal.vue'

const connections = ref([])
const loading = ref(true)
const showModal = ref(false)
const editingConn = ref(null)

const fetchConnections = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/data-sources')
    connections.value = data
  } catch (err) {
    console.error('Error loading connections:', err)
  } finally {
    loading.value = false
  }
}

const getTypeIcon = (type) => {
  const icons = { 'smtp': 'email', 'database': 'storage', 'ftp': 'cloud_upload', 'http': 'language', 'jwt': 'vpn_key' }
  return icons[type] || 'settings'
}

const openNewModal = () => { editingConn.value = null; showModal.value = true }
const editConn = (conn) => { editingConn.value = conn; showModal.value = true }
const deleteConn = async (conn) => {
  if (confirm(`¿Eliminar ${conn.name}?`)) {
    await api.delete(`/data-sources/${conn.id}`)
    fetchConnections()
  }
}

onMounted(fetchConnections)
</script>

<style scoped>
.connections-view { padding: 24px; max-width: 1000px; margin: 0 auto; }
.cv-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; }
.cv-title h1 { font-size: 24px; color: #1e293b; margin: 0; }
.cv-title p { color: #64748b; margin: 4px 0 0; }
.cv-add-btn { display: flex; align-items: center; gap: 8px; background: #2563eb; color: white; padding: 10px 16px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; }
.cv-add-btn:hover { background: #1d4ed8; }
.cv-list { display: flex; flex-direction: column; gap: 12px; }
.cv-item { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; }
.cv-item-info { display: flex; align-items: center; gap: 16px; }
.cv-item-text { display: flex; flex-direction: column; }
.cv-item-name { font-weight: 600; color: #1e293b; }
.cv-item-type { font-size: 12px; color: #94a3b8; }
.cv-item-actions { display: flex; gap: 8px; }
.cv-action { background: none; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px; cursor: pointer; color: #64748b; }
.cv-action:hover { background: #f8fafc; }
.cv-action.delete:hover { color: #ef4444; border-color: #fca5a5; }
.cv-empty { text-align: center; padding: 48px; color: #94a3b8; }
</style>
