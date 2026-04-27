<template>
  <div class="designer-view">
    <!-- Dashboard list mode -->
    <div v-if="!activeDashboard" class="min-h-[calc(100vh-64px)] p-8">
      <!-- Page Header -->
      <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
        <div class="space-y-1">
          <h1 class="font-h1 text-h1 text-slate-900">Mis Dashboards</h1>
          <p class="font-body-md text-slate-500 max-w-2xl">Diseña y gestiona tus dashboards para obtener insights en tiempo real.</p>
        </div>
        <div class="flex items-center gap-3">
          <input ref="importFileInput" type="file" accept=".json" style="display:none" @change="handleImportFile" />
          <button
            class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-all shadow-sm"
            @click="importFileInput.click()">
            <span class="material-symbols-outlined text-lg">download</span>
            Importar
          </button>
          <button
            class="flex items-center gap-2 px-5 py-2 text-sm font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 active:scale-95"
            @click="showNewModal = true">
            <span class="material-symbols-outlined text-lg">add</span>
            Nuevo
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="dashboardStore.allDashboards.length === 0" class="max-w-[1600px] mx-auto">
        <div class="bg-white border border-slate-200 rounded-xl p-12 flex flex-col items-center justify-center gap-4 text-center">
          <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
            <span class="material-symbols-outlined text-3xl text-slate-400">dashboard</span>
          </div>
          <h3 class="text-lg font-semibold text-slate-900">Sin dashboards</h3>
          <p class="text-sm text-slate-500 max-w-md">Crea tu primer dashboard para comenzar a visualizar tus datos.</p>
          <button
            class="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-md"
            @click="showNewModal = true">
            <span class="material-symbols-outlined text-lg">add</span>
            Crear dashboard
          </button>
        </div>
      </div>

      <!-- Designer grid -->
      <div v-else class="max-w-[1600px] mx-auto">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <DesignerCard
            v-for="(db, idx) in dashboardStore.allDashboards"
            :key="db.id"
            :name="db.name"
            :description="db.description"
            :widget-count="db.widgets.length"
            :is-public="db.isPublic"
            :assigned-users-count="db.assignedUsers.length"
            :color-index="idx"
            :category-icon="categoryIcons[idx % categoryIcons.length]"
            @design="openDesigner(db.id)"
            @assign="openAssignModal(db)"
            @view="viewDashboard(db.id)"
            @export="handleExportDashboard(db)"
            @delete="confirmDelete(db)"
          />

          <!-- Create new card -->
          <button
            class="group border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center gap-4 hover:border-blue-500 hover:bg-blue-50/30 transition-all min-h-[280px]"
            @click="showNewModal = true">
            <div class="w-12 h-12 rounded-full bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center transition-colors">
              <span class="material-symbols-outlined text-2xl text-slate-400 group-hover:text-blue-600 transition-colors">add</span>
            </div>
            <div class="text-center">
              <span class="block text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">Nuevo Dashboard</span>
              <span class="block text-xs text-slate-500">Comienza un diseño desde cero</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Designer mode (dashboard open) -->
    <div v-else class="designer-editor">
      <!-- Editor toolbar -->
      <div class="editor-toolbar">
        <button class="btn btn-secondary btn-sm" @click="closeDesigner">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Volver
        </button>

        <div class="toolbar-title">
          <span v-if="!editingTitle" class="db-title-text" @dblclick="startEditTitle">
            {{ activeDashboard.name }}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="edit-hint">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </span>
          <input
            v-else
            ref="titleInput"
            v-model="editTitleValue"
            class="form-input title-edit-input"
            @blur="saveTitle"
            @keyup.enter="saveTitle"
            @keyup.escape="editingTitle = false"
          />
        </div>

        <div class="toolbar-spacer" />

        <!-- Palette picker (design mode only) -->
        <div v-if="isDesignMode" class="palette-picker" v-click-outside="() => paletteOpen = false">
          <button class="palette-trigger" @click="paletteOpen = !paletteOpen" :title="'Paleta del dashboard'">
            <div class="palette-trigger-swatches" v-if="activeDashboardPalette">
              <span
                v-for="c in activeDashboardPalette.colors.slice(0, 5)"
                :key="c"
                class="palette-trigger-swatch"
                :style="{ background: c }"
              />
            </div>
            <div class="palette-trigger-swatches palette-trigger-swatches--default" v-else>
              <span class="palette-trigger-swatch" style="background:#1890ff"/>
              <span class="palette-trigger-swatch" style="background:#52c41a"/>
              <span class="palette-trigger-swatch" style="background:#faad14"/>
              <span class="palette-trigger-swatch" style="background:#f5222d"/>
              <span class="palette-trigger-swatch" style="background:#722ed1"/>
            </div>
            <span class="palette-trigger-label">{{ activeDashboardPalette?.label ?? 'Por defecto' }}</span>
            <svg class="palette-trigger-arrow" :class="{ open: paletteOpen }" width="12" height="12" viewBox="0 0 12 12"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="palette-dropdown" v-if="paletteOpen">
            <div
              class="palette-option"
              :class="{ selected: !activeDashboard?.colorPalette }"
              @click="selectDashboardPalette(null)"
            >
              <span class="palette-option-label">Por defecto</span>
              <div class="palette-option-swatches">
                <span class="palette-option-swatch" style="background:#1890ff"/>
                <span class="palette-option-swatch" style="background:#52c41a"/>
                <span class="palette-option-swatch" style="background:#faad14"/>
                <span class="palette-option-swatch" style="background:#f5222d"/>
                <span class="palette-option-swatch" style="background:#722ed1"/>
                <span class="palette-option-swatch" style="background:#13c2c2"/>
              </div>
            </div>
            <div
              v-for="palette in paletteStore.allPalettes"
              :key="palette.id"
              class="palette-option"
              :class="{ selected: activeDashboard?.colorPalette === palette.id }"
              @click="selectDashboardPalette(palette.id)"
            >
              <span class="palette-option-label">{{ palette.label }}</span>
              <div class="palette-option-swatches">
                <span
                  v-for="c in palette.colors.slice(0, 6)"
                  :key="c"
                  class="palette-option-swatch"
                  :style="{ background: c }"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Public toggle -->
        <label class="toggle-label">
          <input type="checkbox" v-model="isPublic" @change="togglePublic" />
          <span class="toggle-text">Público</span>
        </label>

        <!-- Design / Preview toggle -->
        <div class="mode-toggle">
          <button
            class="mode-btn"
            :class="{ active: isDesignMode }"
            @click="isDesignMode = true"
          >
            <span class="material-symbols-outlined text-sm mr-1">brush</span>
            Diseñar
          </button>
          <button
            class="mode-btn"
            :class="{ active: !isDesignMode }"
            @click="isDesignMode = false"
          >
            <span class="material-symbols-outlined text-sm mr-1">visibility</span>
            Vista previa
          </button>
        </div>

        <button
          v-if="isDesignMode"
          class="btn btn-primary btn-sm"
          @click="addWidget"
        >
          <span class="material-symbols-outlined text-sm">add</span>
          Añadir widget
        </button>
        <button
          v-if="isDesignMode"
          class="btn-ai-assist"
          style="margin-left:8px"
          @click="aiAssistOpen = true"
        >
          <span class="material-symbols-outlined text-sm">auto_awesome</span>
          IA Assist
        </button>
      </div>

      <!-- Description field (design mode) -->
      <div v-if="isDesignMode" class="description-bar">
        <input
          v-model="editDescription"
          type="text"
          class="form-input description-input"
          placeholder="Descripción del dashboard (opcional)..."
          @blur="saveDescription"
        />
      </div>

      <!-- Filter bar -->
      <DashboardFilterBar
        v-if="activeDashboard.filters?.length > 0 || isDesignMode"
        :dashboard-id="activeDashboard.id"
        :filters="activeDashboard.filters || []"
        :is-design-mode="isDesignMode"
        v-model="activeFilterValues"
        @refresh="refreshDesign"
      />

      <!-- Dashboard canvas -->
      <div class="editor-canvas">
        <DashboardGrid
          :widgets="activeDashboard.widgets"
          :is-design-mode="isDesignMode"
          :dashboard-id="activeDashboard.id"
          :dashboard-filters="resolvedDashboardFilters"
          :dashboard-palette="activeDashboard.colorPalette || null"
          :key="designRefreshKey"
          @configure-widget="openConfigModal"
          @layout-widget="openLayoutModal"
          @remove-widget="removeWidget"
        />
      </div>
    </div>

    <!-- ======= MODALS ======= -->

    <!-- New Dashboard Modal -->
    <div v-if="showNewModal" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="showNewModal = false">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[460px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Nuevo Dashboard</h3>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="showNewModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5 flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-slate-700">Nombre *</label>
            <input 
              v-model="newName" 
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              placeholder="Ej: Dashboard de Ventas" 
              autofocus />
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-slate-700">Descripción</label>
            <input 
              v-model="newDescription" 
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              placeholder="Descripción breve..." />
          </div>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="showNewModal = false">Cancelar</button>
          <button 
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed" 
            @click="createDashboard" 
            :disabled="!newName.trim()">Crear</button>
        </div>
      </div>
    </div>

    <!-- Assign Users Modal -->
    <div v-if="assigningDashboard" class="modal-overlay-assign" @click.self="assigningDashboard = null">
      <div class="assign-modal-box">
        <!-- Header -->
        <div class="assign-modal-header">
          <h2>Asignar usuarios — {{ assigningDashboard.name }}</h2>
          <button @click="assigningDashboard = null">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        
        <!-- Content Area -->
        <div class="assign-modal-body">
          <!-- Instruction & Search -->
          <div class="assign-search-section">
            <p class="assign-instruction">Busca y selecciona los usuarios que tendrán acceso a este dashboard.</p>
            <div class="assign-search-row">
              <div class="assign-input-wrapper">
                <span class="material-symbols-outlined assign-search-icon">search</span>
                <input
                  v-model="userSearchQuery"
                  type="text"
                  placeholder="Buscar por nombre o correo..."
                  @keyup.enter="searchUsers"
                />
              </div>
              <button 
                class="assign-search-btn"
                @click="searchUsers"
                :disabled="isSearchingUsers">
                <span class="material-symbols-outlined">hub</span>
                <span>{{ isSearchingUsers ? 'Buscando...' : 'Buscar en Keycloak' }}</span>
              </button>
            </div>
          </div>

          <!-- Search error -->
          <div v-if="searchError" class="assign-error">
            <span class="material-symbols-outlined">error</span>
            {{ searchError }}
          </div>

          <!-- Search results -->
          <div v-if="userSearchResults.length > 0" class="assign-results-section">
            <div class="assign-section-header">
              <h3>RESULTADOS</h3>
              <span class="assign-count-badge">{{ userSearchResults.length }}</span>
            </div>
            <div class="assign-users-list">
              <div 
                v-for="user in userSearchResults" 
                :key="'s'+user.id"
                class="assign-user-item"
                @click="toggleUserFromSearch(user)">
                <div class="assign-user-info">
                  <div class="assign-avatar">{{ user.avatar }}</div>
                  <div class="assign-user-details">
                    <p class="assign-user-name">{{ user.name }}</p>
                    <p class="assign-user-email">{{ user.email || user.username }}</p>
                  </div>
                </div>
                <button 
                  class="assign-add-btn"
                  @click.stop="toggleUserFromSearch(user)">
                  <span class="material-symbols-outlined">add</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Assigned Users -->
          <div class="assign-assigned-section">
            <div class="assign-section-header">
              <h3>USUARIOS ASIGNADOS</h3>
              <span v-if="assignedUsersFull.length" class="assign-count-badge">
                {{ assignedUsersFull.length }} ASIGNADO{{ assignedUsersFull.length !== 1 ? 'S' : '' }}
              </span>
            </div>
            
            <div v-if="assignedUsersFull.length > 0" class="assign-users-list">
              <div 
                v-for="user in assignedUsersFull" 
                :key="'a'+user.id"
                class="assign-user-item">
                <div class="assign-user-info">
                  <div class="assign-avatar">{{ user.avatar }}</div>
                  <div class="assign-user-details">
                    <p class="assign-user-name">{{ user.name }}</p>
                    <p class="assign-user-email">{{ user.email || user.username }}</p>
                  </div>
                </div>
                <button 
                  class="assign-delete-btn"
                  @click.stop="toggleUserFromSearch(user)">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </div>

            <!-- Empty State -->
            <div v-else class="assign-empty-state">
              <span class="material-symbols-outlined">person_search</span>
              <p>No hay usuarios asignados</p>
              <span>Comienza buscando un usuario arriba.</span>
            </div>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="assign-modal-footer">
          <button class="assign-btn-cancel" @click="assigningDashboard = null">Cancelar</button>
          <button class="assign-btn-save" @click="saveAssignment">Guardar asignación</button>
        </div>
      </div>
    </div>

    <!-- Import Dashboard Modal -->
    <div v-if="importPreview" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="importPreview = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[440px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Importar Dashboard</h3>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="importPreview = null">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-500 mb-4">Se creará una copia nueva del siguiente dashboard:</p>
          <div class="p-4 border border-slate-200 rounded-lg bg-slate-50">
            <div class="text-base font-semibold text-slate-900 mb-1">{{ importPreview.name }}</div>
            <p v-if="importPreview.description" class="text-sm text-slate-500 mb-3">{{ importPreview.description }}</p>
            <div class="flex gap-2 flex-wrap">
              <span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-50 text-blue-600 rounded">{{ importPreview.widgets.length }} widgets</span>
              <span v-if="importPreview.filters?.length" class="inline-flex items-center px-2 py-1 text-xs font-medium bg-emerald-50 text-emerald-600 rounded">
                {{ importPreview.filters.length }} filtros
              </span>
            </div>
          </div>
          <p class="text-xs text-slate-400 mt-3">Los identificadores internos serán regenerados.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="importPreview = null">Cancelar</button>
          <button class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700" @click="confirmImport">Importar</button>
        </div>
      </div>
    </div>

    <!-- Chart Config Modal -->
    <ChartConfigModal
      v-if="configuringWidget && !layoutWidget"
      :widget="configuringWidget"
      @close="configuringWidget = null"
      @save="saveWidgetConfig"
      @open-layout="openLayoutModal(configuringWidget)"
    />

    <!-- Chart Layout Modal -->
    <ChartLayoutModal
      v-if="layoutWidget"
      :widget="layoutWidget"
      @close="layoutWidget = null"
      @save="saveLayoutConfig"
    />

    <!-- Delete confirm -->
    <div v-if="deletingDashboard" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="deletingDashboard = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[380px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Eliminar Dashboard</h3>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="deletingDashboard = null">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-700">¿Estás seguro de eliminar <strong>{{ deletingDashboard.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="deletingDashboard = null">Cancelar</button>
          <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700" @click="deleteDashboard">Eliminar</button>
        </div>
      </div>
    </div>

    <!-- Modal: AI Assist -->
    <div v-if="aiAssistOpen" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="aiAssistOpen = false">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[600px] max-w-[95vw] overflow-hidden flex flex-col">
        <div class="flex items-center gap-3 px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <span class="material-symbols-outlined text-indigo-600">auto_awesome</span>
          <span class="text-base font-semibold text-slate-900">IA Assist — Generador de Widgets</span>
          <span v-if="llmStore.isConfigured" class="ml-auto text-xs font-mono bg-white px-2 py-1 rounded border border-slate-200 text-slate-600">
            {{ llmStore.configFor('modelAssist').providerLabel }} · {{ llmStore.configFor('modelAssist').modelLabel }}
          </span>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="aiAssistOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="px-6 py-5 flex flex-col gap-4">
          <div v-if="!llmStore.isConfigured" class="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">
            Sin clave API configurada.
            <router-link to="/settings" @click="aiAssistOpen = false" class="font-semibold underline">
              Ir a Configuración →
            </router-link>
          </div>
          
          <div class="flex items-center gap-2 text-sm">
            <span class="font-semibold text-slate-600">Contexto del Cubo:</span>
            <span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-50 text-blue-600 rounded">{{ cubeStore.allMeasures.length }} métricas</span>
            <span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-purple-50 text-purple-600 rounded">{{ cubeStore.allDimensions.length }} dimensiones</span>
          </div>

          <textarea
            v-model="aiAssistPrompt"
            rows="5"
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
            placeholder="Ej: Muéstrame un gráfico de barras comparando el total de ventas por región..."
            :disabled="aiAssistLoading || !llmStore.isConfigured"
            @keydown.enter.prevent="runAIAssist"
          ></textarea>
        </div>

        <div class="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50">
          <span class="text-xs text-slate-400 italic">Usa Enter para enviar</span>
          <div class="flex items-center gap-3">
            <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="aiAssistOpen = false" :disabled="aiAssistLoading">Cancelar</button>
            <button
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg shadow-md transition-all"
              :class="[!aiAssistPrompt.trim() || aiAssistLoading || !llmStore.isConfigured ? 'opacity-60 cursor-not-allowed grayscale' : 'hover:opacity-90 hover:-translate-y-0.5']"
              :disabled="!aiAssistPrompt.trim() || aiAssistLoading || !llmStore.isConfigured"
              @click="runAIAssist"
              style="background: linear-gradient(135deg, #6366f1, #a855f7);"
            >
              <svg v-if="aiAssistLoading" class="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32" />
              </svg>
              <span v-else class="material-symbols-outlined text-sm">send</span>
              {{ aiAssistLoading ? 'Generando...' : 'Generar Widget' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import DashboardGrid from '@/components/dashboard/DashboardGrid.vue'
import DesignerCard from '@/components/dashboard/DesignerCard.vue'
import ChartConfigModal from '@/components/dashboard/ChartConfigModal.vue'
import ChartLayoutModal from '@/components/dashboard/ChartLayoutModal.vue'
import DashboardFilterBar from '@/components/dashboard/DashboardFilterBar.vue'
import { useDashboardFilters } from '@/composables/useDashboardFilters'
import { useColorPaletteStore } from '@/stores/colorPalettes'
import keycloak from '@/services/keycloak'
import { useCubeStore } from '@/stores/cubejs'
import { useLlmStore } from '@/stores/llm'
import { callLlm } from '@/composables/useLlmCall'

const categoryIcons = ['dashboard', 'directions_car', 'account_tree', 'campaign', 'security', 'monitoring', 'bar_chart', 'pie_chart']
const kcUrl = ''
const kcRealm = import.meta.env.VITE_KEYCLOAK_REALM || 'dashboard'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()
const paletteStore = useColorPaletteStore()
const cubeStore = useCubeStore()
const llmStore = useLlmStore()

// Load data from backend on mount
onMounted(async () => {
  await Promise.all([
    dashboardStore.loadFromBackend(),
    paletteStore.loadFromBackend()
  ])
})

// State
const isDesignMode = ref(true)
const designRefreshKey = ref(0)
function refreshDesign() { designRefreshKey.value++ }
const showNewModal = ref(false)
const configuringWidget = ref(null)
const layoutWidget = ref(null)
const assigningDashboard = ref(null)
const deletingDashboard = ref(null)
const selectedUsers = ref([])
const userSearchQuery = ref('')
const userSearchResults = ref([])
const isSearchingUsers = ref(false)
const searchError = ref(null)
const assignedUsersFull = ref([])

const newName = ref('')
const newDescription = ref('')
const editingTitle = ref(false)
const editTitleValue = ref('')
const editDescription = ref('')
const titleInput = ref(null)
const isPublic = ref(false)
const paletteOpen = ref(false)
const importFileInput = ref(null)
const importPreview = ref(null)

const vClickOutside = {
  mounted(el, binding) {
    el._clickOutsideHandler = (e) => { if (!el.contains(e.target)) binding.value(e) }
    document.addEventListener('mousedown', el._clickOutsideHandler)
  },
  unmounted(el) {
    document.removeEventListener('mousedown', el._clickOutsideHandler)
  }
}

// Active dashboard from route
const activeDashboard = computed(() => {
  const id = route.params.id
  if (!id) return null
  return dashboardStore.allDashboards.find(d => d.id === id) || null
})

const { activeFilterValues, resolvedDashboardFilters, resetFilters } = useDashboardFilters(activeDashboard)

// Watch route changes
watch(() => route.params.id, (id) => {
  if (id) {
    const db = dashboardStore.allDashboards.find(d => d.id === id)
    if (db) {
      editDescription.value = db.description || ''
      isPublic.value = db.isPublic || false
      uiStore.setBreadcrumbs(['Diseño', db.name])
    }
  } else {
    uiStore.setBreadcrumbs(['Diseño', 'Mis Dashboards'])
  }
}, { immediate: true })

// Check for ?new=1 in query
watch(() => route.query.new, (v) => {
  if (v === '1') showNewModal.value = true
}, { immediate: true })

function openDesigner(id) {
  router.push(`/designer/${id}`)
}

function closeDesigner() {
  router.push('/designer')
}

// ── AI Assist ─────────────────────────────────────────────────
const aiAssistOpen = ref(false)
const aiAssistPrompt = ref('')
const aiAssistLoading = ref(false)

function buildWidgetAssistPrompt() {
  const measures = cubeStore.allMeasures.map(m => `- ${m.fullName} (${m.type}) - ${m.title}`).join('\n')
  const dims = cubeStore.allDimensions.map(d => `- ${d.fullName} (${d.type}) - ${d.title}`).join('\n')
  
  return `Eres un experto analista de datos. Tu tarea es generar la configuración de un widget para un dashboard partiendo de un modelo en estrella.

MÉTRICAS DISPONIBLES (Usa el valor 'fullName' para 'measures'):
${measures}

DIMENSIONES DISPONIBLES (Usa el valor 'fullName' para 'dimensions'. Si es de tiempo, úsalo en 'timeDimension'):
${dims}

PETICIÓN DEL USUARIO:
${aiAssistPrompt.value}

INSTRUCCIONES:
1. Responde SOLO con un bloque JSON válido (\`\`\`json ... \`\`\`).
2. El JSON debe referenciar EXCLUSIVAMENTE nombres detallados en los listados anteriores y tener este formato EXACTO:
{
  "title": "Un título corto para el gráfico generado de tu comprensión de la petición temporal o temática",
  "widgetType": "bar", // escoge: bar, line, pie, gauge, radar, table, combined
  "cubeQuery": {
    "measures": ["CubeName.measureName"],
    "dimensions": ["CubeName.dimensionName"],
    "timeDimension": {
      "dimension": "CubeName.timeDimensionName",
      "granularity": "month" // opcional, puede ser: day, week, month, year
    }
  }
}
3. No incluyas texto fuera del bloque JSON.
4. "timeDimension" es opcional. Solo inclúyela si la consulta tiene un enfoque explícito en fechas/tiempo y la petición o métrica pide graficar en el tiempo. NO la incluyas al azar si analizas campos normales de nombre/status.`
}

async function runAIAssist() {
  if (!aiAssistPrompt.value.trim() || !llmStore.isConfigured) return
  aiAssistLoading.value = true

  try {
    const cfg = llmStore.configFor('modelAssist')
    const text = await callLlm({ provider: cfg.provider, modelId: cfg.modelId, apiKey: cfg.apiKey, prompt: buildWidgetAssistPrompt(), maxTokens: 16384 })
    
    let widgetDef = null
    const extractedText = text.trim()

    try {
      widgetDef = JSON.parse(extractedText)
    } catch {
      const match = extractedText.match(/```(?:json)?\s*([\s\S]*?)(?:```|$)/i)
      const block = match ? match[1].trim() : extractedText
      try {
        widgetDef = JSON.parse(block)
      } catch (e2) {
        throw new Error('No se pudo encontrar un objeto JSON válido en la respuesta.')
      }
    }

    if (!widgetDef || !widgetDef.cubeQuery || !widgetDef.widgetType) {
      throw new Error('La respuesta de la IA carece de los campos requeridos.')
    }

    const { cubeQuery } = widgetDef;
    if (cubeQuery.timeDimension && !cubeQuery.timeDimension.dimension) {
        delete cubeQuery.timeDimension
    }
    
    // Map LLM string arrays to {key, label} objects expected by the store
    const normalizedQuery = {
      measures: (cubeQuery.measures || []).map(m => typeof m === 'string' ? { key: m, label: m.split('.').pop(), color: '#1890ff' } : m),
      dimensions: (cubeQuery.dimensions || []).map(d => typeof d === 'string' ? { key: d, label: d.split('.').pop() } : d),
      timeDimension: cubeQuery.timeDimension || null,
      filters: [],
      limit: 100
    }

    dashboardStore.addWidget(activeDashboard.value.id, {
        title: widgetDef.title || 'Gráfico generado por IA',
        chartType: widgetDef.widgetType,
        cubeQuery: normalizedQuery,
        useMockData: false
    })

    aiAssistOpen.value = false
    aiAssistPrompt.value = ''
  } catch (err) {
    alert('Error al generar widget: ' + err.message)
  } finally {
    aiAssistLoading.value = false
  }
}

function viewDashboard(id) {
  router.push(`/dashboard/${id}`)
}

async function openAssignModal(db) {
  assigningDashboard.value = db
  selectedUsers.value = [...db.assignedUsers]
  
  assignedUsersFull.value = []
  userSearchQuery.value = ''
  userSearchResults.value = []
  searchError.value = null

  if (selectedUsers.value.length > 0) {
    try {
        const userPromises = selectedUsers.value.map(id => 
          fetch(`/keycloak/admin/realms/${kcRealm}/users/${id}`, {
           headers: { Authorization: `Bearer ${keycloak.token}` }
         }).then(r => r.ok ? r.json() : null)
       )
       const results = await Promise.all(userPromises)
       assignedUsersFull.value = results.filter(u => u).map(u => ({
          id: u.id,
          name: (u.firstName && u.lastName) ? `${u.firstName} ${u.lastName}` : (u.firstName || u.lastName || u.username),
          email: u.email || '',
          username: u.username || '',
          avatar: (u.firstName ? u.firstName[0] : (u.username?.[0] || '?')).toUpperCase()
       }))
    } catch(err) {
       console.error("No se pudieron cargar perfiles de los usuarios asignados", err)
    }
  }
}

async function searchUsers() {
  if (!userSearchQuery.value || userSearchQuery.value.trim().length < 2) {
    userSearchResults.value = []
    searchError.value = null
    return
  }
  isSearchingUsers.value = true
  searchError.value = null
  try {
    const url = `/keycloak/admin/realms/${kcRealm}/users?search=${encodeURIComponent(userSearchQuery.value.trim())}`
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${keycloak.token}` }
    })
    if (!response.ok) {
      if (response.status === 403) throw new Error('Sin permiso (requiere rol view-users o realm-management en Keycloak)')
      throw new Error(`Error al conectar con el servidor (HTTP ${response.status})`)
    }
    const json = await response.json()
    userSearchResults.value = json.map(u => ({
      id: u.id,
      name: (u.firstName && u.lastName) ? `${u.firstName} ${u.lastName}` : (u.firstName || u.lastName || u.username),
      email: u.email || '',
      username: u.username || '',
      avatar: (u.firstName ? u.firstName[0] : (u.username?.[0] || '?')).toUpperCase()
    }))
  } catch (err) {
    searchError.value = err.message
    userSearchResults.value = []
  } finally {
    isSearchingUsers.value = false
  }
}

function toggleUserFromSearch(user) {
  const isSelected = selectedUsers.value.includes(user.id)
  if (!isSelected) {
    selectedUsers.value.push(user.id)
    if (!assignedUsersFull.value.find(u => u.id === user.id)) {
      assignedUsersFull.value.push(user)
    }
  } else {
    selectedUsers.value = selectedUsers.value.filter(id => id !== user.id)
    assignedUsersFull.value = assignedUsersFull.value.filter(u => u.id !== user.id)
  }
}

function saveAssignment() {
  if (!assigningDashboard.value) return
  dashboardStore.assignDashboardToUsers(assigningDashboard.value.id, selectedUsers.value)
  uiStore.addAlert({
    type: 'success',
    message: `Dashboard "${assigningDashboard.value.name}" asignado a ${selectedUsers.value.length} usuario(s)`
  })
  assigningDashboard.value = null
}

function confirmDelete(db) {
  deletingDashboard.value = db
}

function deleteDashboard() {
  if (!deletingDashboard.value) return
  const name = deletingDashboard.value.name
  dashboardStore.deleteDashboard(deletingDashboard.value.id)
  deletingDashboard.value = null
  if (activeDashboard.value?.id === deletingDashboard.value?.id) {
    router.push('/designer')
  }
  uiStore.addAlert({ type: 'success', message: `Dashboard "${name}" eliminado` })
}

async function createDashboard() {
  if (!newName.value.trim()) return
  const db = await dashboardStore.createDashboard(newName.value.trim(), newDescription.value.trim(), authStore.user.id)
  showNewModal.value = false
  newName.value = ''
  newDescription.value = ''
  // Remove ?new query param and navigate
  router.push(`/designer/${db.id}`)
}

function addWidget() {
  if (!activeDashboard.value) return
  router.push(`/designer/${activeDashboard.value.id}/configure`)
}

function removeWidget(widgetId) {
  if (!activeDashboard.value) return
  dashboardStore.removeWidget(activeDashboard.value.id, widgetId)
}

function openConfigModal(widget) {
  router.push(`/designer/${activeDashboard.value.id}/configure/${widget.id}`)
}

function openLayoutModal(widget) {
  configuringWidget.value = null
  layoutWidget.value = activeDashboard.value?.widgets.find(w => w.id === widget.id) || widget
}

function saveLayoutConfig(patch) {
  if (!activeDashboard.value || !layoutWidget.value) return
  dashboardStore.updateWidget(activeDashboard.value.id, layoutWidget.value.id, patch)
  layoutWidget.value = null
  uiStore.addAlert({ type: 'success', message: 'Formato del widget actualizado' })
}

function saveWidgetConfig(updatedWidget) {
  if (!activeDashboard.value || !updatedWidget.id) {
    console.error('Cannot save widget config: missing dashboard or widget id', { dashboardId: activeDashboard.value?.id, widgetId: updatedWidget?.id })
    configuringWidget.value = null
    return
  }
  dashboardStore.updateWidget(activeDashboard.value.id, updatedWidget.id, updatedWidget)
  configuringWidget.value = null
  uiStore.addAlert({ type: 'success', message: 'Widget actualizado correctamente' })
}

function startEditTitle() {
  editTitleValue.value = activeDashboard.value?.name || ''
  editingTitle.value = true
  nextTick(() => titleInput.value?.focus())
}

function saveTitle() {
  if (activeDashboard.value && editTitleValue.value.trim()) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { name: editTitleValue.value.trim() })
    uiStore.setBreadcrumbs(['Diseño', editTitleValue.value.trim()])
  }
  editingTitle.value = false
}

function saveDescription() {
  if (activeDashboard.value) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { description: editDescription.value })
  }
}

function togglePublic() {
  if (activeDashboard.value) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { isPublic: isPublic.value })
  }
}

function selectDashboardPalette(paletteId) {
  if (activeDashboard.value) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { colorPalette: paletteId })
  }
  paletteOpen.value = false
}

const activeDashboardPalette = computed(() =>
  paletteStore.getPaletteById(activeDashboard.value?.colorPalette) || null
)

// ── Export / Import ───────────────────────────────────────────

function handleExportDashboard(db) {
  const payload = {
    __dashboardStudio: true,
    version: '1.0',
    exportedAt: new Date().toISOString(),
    dashboard: {
      name: db.name,
      description: db.description || '',
      isPublic: db.isPublic || false,
      filters: db.filters || [],
      colorPalette: db.colorPalette || null,
      widgets: db.widgets
    }
  }
  const slug = db.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'dashboard'
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${slug}.dashboard.json`
  a.click()
  URL.revokeObjectURL(url)
  uiStore.addAlert({ type: 'success', message: `Dashboard "${db.name}" exportado` })
}

function handleImportFile(e) {
  const file = e.target.files[0]
  if (!file) return
  e.target.value = ''
  const reader = new FileReader()
  reader.onload = (evt) => {
    try {
      const data = JSON.parse(evt.target.result)
      if (!data.__dashboardStudio || !data.dashboard?.name) {
        uiStore.addAlert({ type: 'error', message: 'Archivo inválido: no es un dashboard exportado de Dashboard Studio' })
        return
      }
      importPreview.value = data.dashboard
    } catch {
      uiStore.addAlert({ type: 'error', message: 'Error al leer el archivo: JSON inválido' })
    }
  }
  reader.readAsText(file)
}

function confirmImport() {
  if (!importPreview.value) return
  const d = importPreview.value
  const db = dashboardStore.createDashboard(d.name, d.description, authStore.user.id)
  dashboardStore.updateDashboard(db.id, {
    isPublic: d.isPublic || false,
    filters: d.filters || [],
    colorPalette: d.colorPalette || null,
    widgets: d.widgets.map(w => ({
      ...w,
      id: Math.random().toString(36).substr(2, 9)
    }))
  })
  uiStore.addAlert({ type: 'success', message: `Dashboard "${d.name}" importado correctamente` })
  importPreview.value = null
  router.push(`/designer/${db.id}`)
}
</script>

<style scoped>
.designer-view { display: flex; flex-direction: column; height: 100%; }

/* Material Symbols font */
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

.text-sm { font-size: 14px; }

/* Editor */
.designer-editor { display: flex; flex-direction: column; height: 100%; padding: 20px; }

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.toolbar-title { flex: 1; min-width: 0; }
.db-title-text {
  font-size: 16px; font-weight: 600; color: var(--text);
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
}
.db-title-text:hover { color: var(--primary); }
.edit-hint { opacity: 0.5; }
.title-edit-input { max-width: 300px; font-size: 15px; font-weight: 600; }
.toolbar-spacer { flex: 1; }

/* Palette picker */
.palette-picker {
  position: relative;
  flex-shrink: 0;
}
.palette-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  color: var(--text);
  transition: border-color 0.15s;
  white-space: nowrap;
}
.palette-trigger:hover { border-color: var(--primary); }
.palette-trigger-swatches {
  display: flex;
  gap: 2px;
}
.palette-trigger-swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  display: inline-block;
}
.palette-trigger-label {
  font-size: 12px;
  color: var(--text-secondary);
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.palette-trigger-arrow {
  color: var(--text-secondary);
  transition: transform 0.15s;
  flex-shrink: 0;
}
.palette-trigger-arrow.open { transform: rotate(180deg); }

.palette-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  min-width: 220px;
  z-index: 200;
  overflow: hidden;
}
.palette-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.1s;
  gap: 12px;
}
.palette-option:hover { background: var(--bg); }
.palette-option.selected { background: #e6f4ff; }
.palette-option-label {
  font-size: 13px;
  color: var(--text);
  white-space: nowrap;
  flex-shrink: 0;
}
.palette-option.selected .palette-option-label { color: var(--primary); font-weight: 600; }
.palette-option-swatches {
  display: flex;
  gap: 3px;
}
.palette-option-swatch {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  display: inline-block;
}

.toggle-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--text-secondary); cursor: pointer;
  flex-shrink: 0;
}
.toggle-text { white-space: nowrap; }

.mode-toggle {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}
.mode-btn {
  display: inline-flex; align-items: center;
  padding: 6px 12px; border: none; background: transparent;
  font-size: 13px; cursor: pointer; color: var(--text-secondary);
  transition: all 0.15s; white-space: nowrap;
}
.mode-btn:hover { background: var(--bg); }
.mode-btn.active { background: var(--primary); color: #fff; }

.description-bar { margin-bottom: 10px; }
.description-input { font-size: 13px; }

.editor-canvas {
  flex: 1;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: auto;
  box-shadow: var(--shadow);
  padding: 8px;
  min-height: 400px;
}

/* Add widget types */
.widget-type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.widget-type-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 14px 8px; border: 2px solid var(--border);
  border-radius: 8px; cursor: pointer; transition: all 0.15s; text-align: center;
}
.widget-type-card:hover { border-color: var(--primary); background: var(--primary-light); }
.widget-type-card.selected { border-color: var(--primary); background: var(--primary-light); }
.wt-icon { font-size: 28px; margin-bottom: 6px; }
.wt-label { font-size: 13px; font-weight: 600; color: var(--text); }
.wt-desc { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }

/* AI Assist */
.btn-ai-assist {
  display: inline-flex; align-items: center; gap: 6px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  color: white; border: none; padding: 6px 14px;
  border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; box-shadow: 0 4px 12px rgba(168, 85, 247, 0.25);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.btn-ai-assist:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(168, 85, 247, 0.35); }
.btn-ai-assist:active:not(:disabled) { transform: translateY(0); }
.btn-ai-assist:disabled { opacity: 0.6; cursor: not-allowed; box-shadow: none; filter: grayscale(50%); }

.animate-spin { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Custom font classes */
.font-h1 {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* Assign Users Modal Styles */
.modal-overlay-assign {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  padding: 16px;
}

.assign-modal-box {
  background: white;
  width: 100%;
  max-width: 672px;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.assign-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.assign-modal-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.assign-modal-header button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}

.assign-modal-header button:hover {
  background: #f1f5f9;
  color: #334155;
}

.assign-modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.assign-search-section {
  margin-bottom: 24px;
}

.assign-instruction {
  font-size: 14px;
  color: #475569;
  margin: 0 0 16px 0;
}

.assign-search-row {
  display: flex;
  gap: 12px;
}

.assign-input-wrapper {
  position: relative;
  flex: 1;
}

.assign-search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 20px;
  pointer-events: none;
}

.assign-input-wrapper input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: #f8fafc;
  outline: none;
  transition: all 0.2s;
}

.assign-input-wrapper input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.assign-search-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.assign-search-btn:hover:not(:disabled) {
  background: #2563eb;
}

.assign-search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.assign-search-btn .material-symbols-outlined {
  font-size: 18px;
}

.assign-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 24px;
}

.assign-results-section,
.assign-assigned-section {
  margin-bottom: 24px;
}

.assign-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 0 4px;
}

.assign-section-header h3 {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.assign-count-badge {
  padding: 2px 8px;
  background: #dbeafe;
  color: #1d4ed8;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
}

.assign-users-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.assign-user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.2s;
}

.assign-user-item:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.assign-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assign-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.assign-user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.assign-user-name {
  font-size: 14px;
  font-weight: 500;
  color: #0f172a;
  margin: 0;
}

.assign-user-email {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.assign-delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s;
}

.assign-delete-btn:hover {
  color: #dc2626;
  background: #fef2f2;
}

.assign-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #3b82f6;
  transition: all 0.2s;
}

.assign-add-btn:hover {
  color: #2563eb;
  background: #eff6ff;
}

.assign-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  background: #f8fafc;
  text-align: center;
}

.assign-empty-state .material-symbols-outlined {
  font-size: 48px;
  color: #94a3b8;
  margin-bottom: 12px;
}

.assign-empty-state p {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin: 0 0 4px 0;
}

.assign-empty-state span {
  font-size: 13px;
  color: #94a3b8;
}

.assign-modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.assign-btn-cancel {
  padding: 10px 24px;
  background: transparent;
  color: #475569;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.assign-btn-cancel:hover {
  background: #f1f5f9;
}

.assign-btn-save {
  padding: 10px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
}

.assign-btn-save:hover {
  background: #2563eb;
}

</style>
