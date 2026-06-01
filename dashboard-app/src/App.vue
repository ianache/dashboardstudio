<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useCubeStore } from '@/stores/cubejs'
import { useLlmStore } from '@/stores/llm'
import { useUIStore } from '@/stores/ui'

const cubeStore = useCubeStore()
const llmStore  = useLlmStore()
const uiStore   = useUIStore()

onMounted(async () => {
  uiStore.initTheme()
  await Promise.all([
    cubeStore.loadConfigFromBackend(),
    llmStore.loadConfigFromBackend(),
  ])
  // Pre-load meta to avoid lag during first dashboard navigation
  if (cubeStore.token && cubeStore.apiUrl) {
    await cubeStore.loadMeta()
  }
})
</script>
