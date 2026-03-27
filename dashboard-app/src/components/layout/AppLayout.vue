<template>
  <div class="app-layout" @click="uiStore.closeDropdowns()">
    <SideMenu />
    <div class="app-content" :class="{ 'sidebar-collapsed': uiStore.sidebarCollapsed }">
      <TopBar />
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import SideMenu from './SideMenu.vue'
import TopBar from './TopBar.vue'
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
}

.app-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-left: var(--sidebar-width);
  transition: margin-left 0.25s ease;
}

.app-content.sidebar-collapsed {
  margin-left: var(--sidebar-collapsed-width);
}

.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
</style>
