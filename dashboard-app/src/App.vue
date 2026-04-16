<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useCubeStore } from '@/stores/cubejs'

const cubeStore = useCubeStore()

onMounted(async () => {
  await cubeStore.loadConfigFromBackend()
  // Pre-load meta to avoid lag during first dashboard navigation
  if (cubeStore.token && cubeStore.apiUrl) {
    await cubeStore.loadMeta()
  }
})
</script>
