<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useCubeStore } from '@/stores/cubejs'

const cubeStore = useCubeStore()

onMounted(async () => {
  await cubeStore.loadConfigFromBackend()
})
</script>
