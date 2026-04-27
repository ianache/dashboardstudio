<template>
  <div class="configurator-view">
    <!-- Header -->
    <header class="configurator-header">
      <div class="header-left">
        <button class="btn btn-secondary btn-sm" @click="handleCancel" :disabled="saving">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Volver
        </button>
        <div class="header-title">
          <input 
            type="text" 
            :value="store.title" 
            @input="store.setTitle($event.target.value)"
            placeholder="Título del gráfico"
            class="title-input"
          />
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="handleCancel" :disabled="saving">Cancelar</button>
        <button class="btn btn-primary" @click="handleSave" :disabled="saving || store.measures.length === 0">
          <span v-if="saving" class="spinner-xs"></span>
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </button>
      </div>
    </header>

    <!-- Main Content Grid -->
    <main class="configurator-content" :class="{ 'is-loading': saving || cubeStore.metaLoading }">
      <!-- Loading Overlay -->
      <div v-if="saving || cubeStore.metaLoading" class="panel-overlay">
        <div class="spinner"></div>
        <span>{{ saving ? 'Guardando configuración...' : 'Cargando metadatos...' }}</span>
      </div>
      <!-- Left Panel: Data Source -->
      <aside class="panel panel-source">
        <header class="panel-header">
          <h3>Fuente</h3>
          <button
            class="btn-icon toggle-cube-name"
            :class="{ active: showCubeName }"
            @click="showCubeName = !showCubeName"
            :title="showCubeName ? 'Ocultar nombre del cubo' : 'Mostrar nombre del cubo'"
          >
            <svg v-if="showCubeName" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
              <line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
          </button>
        </header>
        <div class="panel-body">
          <div class="cube-selector">
            <label>Cubo</label>
            <div class="ct-combobox" :class="{ open: cubeOpen }" @click.stop="cubeOpen = !cubeOpen">
              <div class="ct-combobox-trigger">
                <span class="ct-icon">🗄️</span>
                <span class="ct-name">{{ activeCubeLabel }}</span>
                <svg class="ct-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              <div v-if="cubeOpen" class="ct-combobox-dropdown" @click.stop>
                <div
                  v-for="cube in availableCubes"
                  :key="cube.name"
                  class="ct-combobox-option"
                  :class="{ selected: store.selectedCube === cube.name }"
                  @click="store.setCube(cube.name); cubeOpen = false"
                >
                  <span class="ct-icon">🗄️</span>
                  <span class="ct-name">{{ cube.title || cube.name }}</span>
                  <span v-if="usedCubes.has(cube.name)" class="used-dot" title="Tiene campos en uso">●</span>
                  <svg v-if="store.selectedCube === cube.name" class="ct-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
              </div>
            </div>
            <div v-if="usedCubes.size > 0" class="used-cubes-hint">
              <span>En uso:</span>
              <span v-for="c in [...usedCubes]" :key="c" class="used-cube-tag">{{ c }}</span>
            </div>
          </div>

          <div v-if="store.selectedCube" class="source-lists">
            <!-- Measures -->
            <div class="source-section">
              <div class="section-header">
                <h4>Métricas</h4>
                <div class="search-box">
                  <input type="text" v-model="measureSearch" placeholder="Buscar métrica..." />
                </div>
              </div>
              <draggable
                class="field-list"
                :list="currentMeasures"
                :group="{ name: 'measures', pull: 'clone', put: false }"
                :sort="false"
                item-key="fullName"
                :clone="m => ({ ...m })"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: m }">
                  <div class="field-item">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon measure">#</span>
                      <span class="field-label" :title="m.fullName">{{ showCubeName ? m.title : (m.shortTitle || m.title) }}</span>
                    </div>
                  </div>
                </template>
              </draggable>
              <div v-if="currentMeasures.length === 0" class="no-results">
                No se encontraron métricas
              </div>
            </div>

            <!-- Dimensions -->
            <div class="source-section">
              <div class="section-header">
                <h4>Análisis</h4>
                <div class="search-box">
                  <input type="text" v-model="dimensionSearch" placeholder="Buscar dimensión..." />
                </div>
              </div>
              <draggable
                class="field-list"
                :list="currentDimensions"
                :group="{ name: 'dimensions', pull: 'clone', put: false }"
                :sort="false"
                item-key="fullName"
                :clone="d => ({ ...d })"
              >
                <template #item="{ element: d }">
                  <div class="field-item">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon dimension">A</span>
                      <span class="field-label" :title="d.fullName">{{ showCubeName ? d.title : (d.shortTitle || d.title) }}</span>
                    </div>
                  </div>
                </template>
              </draggable>
              <div v-if="currentDimensions.length === 0" class="no-results">
                No se encontraron dimensiones
              </div>
            </div>
          </div>

          <div v-else-if="cubeStore.metaLoading" class="loading-state">
            <div class="spinner-sm"></div>
            <span>Cargando metadatos...</span>
          </div>

          <div v-else class="empty-state">
            <p>Seleccione un cubo para ver los campos disponibles.</p>
          </div>
        </div>
      </aside>

      <!-- Center Panel: Configuration -->
      <section class="panel panel-config" :class="{ 'collapsed': configCollapsed }">
        <header class="panel-header">
          <div class="header-left-group">
            <button class="toggle-btn" @click="toggleConfig">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="19" y1="12" x2="5" y2="12"/><polyline v-if="!configCollapsed" points="12 19 5 12 12 5"/><polyline v-else points="12 5 19 12 12 19"/>
              </svg>
            </button>
            <h3 v-if="!configCollapsed">Configuración</h3>
          </div>
          <div v-if="!configCollapsed" class="chart-type-selector">
            <div class="ct-combobox" :class="{ open: chartTypeOpen }" @click.stop="chartTypeOpen = !chartTypeOpen">
              <div class="ct-combobox-trigger">
                <span class="ct-icon">{{ activeChartType.icon }}</span>
                <span class="ct-name">{{ activeChartType.label }}</span>
                <svg class="ct-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              <div v-if="chartTypeOpen" class="ct-combobox-dropdown" @click.stop>
                <div
                  v-for="ct in chartTypes"
                  :key="ct.value"
                  class="ct-combobox-option"
                  :class="{ selected: store.chartType === ct.value }"
                  @click="store.setChartType(ct.value); chartTypeOpen = false"
                >
                  <span class="ct-icon">{{ ct.icon }}</span>
                  <span class="ct-name">{{ ct.label }}</span>
                  <svg v-if="store.chartType === ct.value" class="ct-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
              </div>
            </div>
          </div>
        </header>
        <div v-if="!configCollapsed" class="panel-body">
          <div class="config-sections">
            <!-- Measures (Series) -->
            <div class="config-section">
              <div class="section-label">
                <span>Series</span>
                <small>(Métricas)</small>
              </div>
              <draggable
                class="drop-zone"
                v-model="store.measures"
                :group="{ name: 'measures', put: (to, from, element) => !store.measures.some(m => m.fullName === element.fullName) }"
                item-key="fullName"
                :animation="200"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: m }">
                  <div class="field-item active-field">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon measure">#</span>
                      <span class="field-label">{{ m.alias || m.title }}</span>
                    </div>
                    <div class="field-actions">
                      <button class="action-btn" @click="openConfig('measures', m)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                        </svg>
                      </button>
                      <button class="remove-btn" @click="store.removeMeasure(m.fullName)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div v-if="store.measures.length === 0" class="drop-placeholder">
                    Arrastre métricas aquí
                  </div>
                </template>
              </draggable>
            </div>

            <!-- Dimensions (Análisis) -->
            <div class="config-section">
              <div class="section-label">
                <span>Análisis</span>
                <small>(Dimensiones)</small>
              </div>
              <draggable
                class="drop-zone"
                v-model="store.dimensions"
                :group="{ name: 'dimensions', put: (to, from, element) => !store.dimensions.some(d => d.fullName === element.fullName) }"
                item-key="fullName"
                :animation="200"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: d }">
                  <div class="field-item active-field">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon dimension">A</span>
                      <span class="field-label">{{ d.alias || d.title }}</span>
                    </div>
                    <div class="field-actions">
                      <button class="action-btn" @click="openConfig('dimensions', d)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                        </svg>
                      </button>
                      <button class="remove-btn" @click="store.removeDimension(d.fullName)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div v-if="store.dimensions.length === 0" class="drop-placeholder">
                    Arrastre dimensiones aquí
                  </div>
                </template>
              </draggable>
            </div>

            <!-- Quick Filters -->
            <div class="config-section">
              <div class="section-label">
                <span>Filtros Rápidos</span>
                <small>(Dimensiones)</small>
              </div>
              <draggable
                class="drop-zone"
                v-model="store.filters"
                :group="{ name: 'dimensions', pull: false, put: (to, from, element) => !store.filters.some(f => f.fullName === element.fullName) }"
                item-key="fullName"
                :animation="200"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: f }">
                  <div class="field-item active-field filter-field-config">
                    <div class="filter-main">
                      <div class="field-content">
                        <span class="field-icon dimension">F</span>
                        <span class="field-label">{{ f.alias || f.title }}</span>
                      </div>
                      <button class="remove-btn" @click="store.removeFilter(f.fullName)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                    <div class="filter-settings">
                      <!-- String dimension: multiselect checkbox dropdown -->
                      <template v-if="f.type === 'string' || f.memberType === 'string'">
                        <div class="filter-multiselect">
                          <button
                            class="filter-ms-trigger"
                            @click.stop="toggleFilterDropdown(f.fullName)"
                          >
                            <span class="filter-ms-label">{{ getFilterDisplayValue(f) }}</span>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                          </button>
                          <div v-if="openFilterDropdown === f.fullName" class="filter-ms-dropdown" @click.stop>
                            <label class="filter-ms-option">
                              <input
                                type="checkbox"
                                :checked="!f.values || f.values.length === 0"
                                @change="store.updateFilter(f.fullName, { values: [] })"
                              />
                              <span>Todos</span>
                            </label>
                            <template v-if="filterOptions[f.fullName] && filterOptions[f.fullName].length > 0">
                              <label v-for="opt in filterOptions[f.fullName]" :key="opt" class="filter-ms-option">
                                <input
                                  type="checkbox"
                                  :value="opt"
                                  :checked="(f.values || []).includes(String(opt))"
                                  @change="toggleFilterValue(f.fullName, String(opt), f.values || [])"
                                />
                                <span>{{ opt }}</span>
                              </label>
                            </template>
                            <div v-else class="filter-ms-empty">
                              <small>{{ cubeStore.token ? 'Cargando valores...' : 'Sin conexión al cubo' }}</small>
                            </div>
                          </div>
                        </div>
                      </template>
                      <!-- Other types: operator + text input -->
                      <template v-else>
                        <select
                          :value="f.operator || 'equals'"
                          @change="store.updateFilter(f.fullName, { operator: $event.target.value })"
                          class="form-select select-xs"
                        >
                          <option value="equals">Es igual a</option>
                          <option value="notEquals">No es igual a</option>
                          <option value="contains">Contiene</option>
                          <option value="set">Está definido</option>
                        </select>
                        <input
                          type="text"
                          :value="(f.values || []).join(', ')"
                          @change="store.updateFilter(f.fullName, { values: $event.target.value.split(',').map(v => v.trim()) })"
                          placeholder="Valores..."
                          class="form-control input-xs"
                        />
                      </template>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div v-if="store.filters.length === 0" class="drop-placeholder">
                    Arrastre dimensiones para filtrar
                  </div>
                </template>
              </draggable>
            </div>
          </div>
        </div>
      </section>

      <!-- Right Panel: Preview -->
      <section class="panel panel-preview">
        <header class="panel-header">
          <h3>Vista Previa</h3>
        </header>
        <div class="panel-body">
          <div class="preview-container card">
            <template v-if="store.measures.length > 0">
              <!-- Table preview -->
              <div v-if="store.chartType === 'table'" class="preview-table-wrap">
                <div v-if="loading" class="chart-loading"><div class="spinner"></div></div>
                <div v-else-if="error" class="chart-error">⚠️ {{ error }}</div>
                <table v-else class="preview-table">
                  <thead>
                    <tr>
                      <th v-for="col in tableColumns" :key="col.key">{{ col.label }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in data" :key="i">
                      <td v-for="col in tableColumns" :key="col.key">{{ getTableCell(row, col) }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="!loading && data.length === 0" class="empty-state">
                  <p>Sin datos para mostrar.</p>
                </div>
              </div>
              <!-- KPI preview -->
              <KpiWidget
                v-else-if="store.chartType === 'kpi'"
                :data="data"
                :loading="loading"
                :error="error"
                :widget="currentWidget"
                style="height:100%"
              />
              <!-- Chart preview -->
              <EChartWrapper
                v-else
                :chartType="store.chartType"
                :data="data"
                :loading="loading"
                :error="error"
                :widget="currentWidget"
              />
            </template>
            <div v-else class="empty-state">
              <div class="empty-icon">📊</div>
              <h3>Sin vista previa</h3>
              <p>Configure métricas y dimensiones para generar el gráfico.</p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Field Config Modal -->
    <div v-if="activeConfigField" class="modal-backdrop" @click.self="closeConfig">
      <div class="modal-content field-config-modal">
        <header class="modal-header">
          <h3>Configurar {{ activeConfigField.type === 'measures' ? 'Métrica' : 'Dimensión' }}</h3>
          <button class="close-btn" @click="closeConfig">&times;</button>
        </header>
        <div class="modal-body">
          <div class="form-group">
            <label>Nombre Visible (Alias)</label>
            <input 
              type="text" 
              v-model="activeConfigField.field.alias" 
              :placeholder="activeConfigField.field.title"
              class="form-control"
            />
          </div>
          
          <div v-if="activeConfigField.type === 'measures'" class="form-group">
            <label>Formato</label>
            <div class="ct-combobox" :class="{ open: formatOpen }" @click.stop="formatOpen = !formatOpen">
              <div class="ct-combobox-trigger">
                <span class="ct-name">{{ activeFormatLabel }}</span>
                <svg class="ct-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              <div v-if="formatOpen" class="ct-combobox-dropdown" @click.stop>
                <div class="ct-combobox-option" :class="{ selected: !activeConfigField.field.format }" @click="activeConfigField.field.format = undefined; formatOpen = false">
                  <span class="ct-name">Predeterminado</span>
                  <svg v-if="!activeConfigField.field.format" class="ct-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                <div v-for="fmt in formatOptions" :key="fmt.value" class="ct-combobox-option" :class="{ selected: activeConfigField.field.format === fmt.value }" @click="activeConfigField.field.format = fmt.value; formatOpen = false">
                  <span class="ct-name">{{ fmt.label }}</span>
                  <svg v-if="activeConfigField.field.format === fmt.value" class="ct-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
              </div>
            </div>
          </div>
          <!-- Currency selector: only when format = currency -->
          <div v-if="activeConfigField.type === 'measures' && activeConfigField.field.format === 'currency'" class="form-group">
            <label>Moneda</label>
            <div class="ct-combobox" :class="{ open: currencyOpen }" @click.stop="currencyOpen = !currencyOpen">
              <div class="ct-combobox-trigger">
                <span class="ct-name">{{ currencyStore.getById(activeConfigField.field.currencyId)?.code ? `${currencyStore.getById(activeConfigField.field.currencyId).symbol} ${currencyStore.getById(activeConfigField.field.currencyId).code}` : '— Seleccionar —' }}</span>
                <svg class="ct-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              <div v-if="currencyOpen" class="ct-combobox-dropdown" @click.stop>
                <div
                  class="ct-combobox-option"
                  :class="{ selected: !activeConfigField.field.currencyId }"
                  @click="activeConfigField.field.currencyId = null; currencyOpen = false"
                >
                  <span class="ct-name">— Seleccionar —</span>
                  <svg v-if="!activeConfigField.field.currencyId" class="ct-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                <div
                  v-for="cur in currencyStore.activeCurrencies"
                  :key="cur.id"
                  class="ct-combobox-option"
                  :class="{ selected: activeConfigField.field.currencyId === cur.id }"
                  @click="activeConfigField.field.currencyId = cur.id; currencyOpen = false"
                >
                  <span class="ct-name">{{ cur.symbol }} {{ cur.code }} — {{ cur.name }}</span>
                  <svg v-if="activeConfigField.field.currencyId === cur.id" class="ct-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Decimal places: only for number/currency -->
          <div v-if="activeConfigField.type === 'measures' && (activeConfigField.field.format === 'number' || activeConfigField.field.format === 'currency')" class="form-group">
            <label>Decimales</label>
            <input
              type="number"
              v-model.number="activeConfigField.field.decimalPlaces"
              min="0" max="6" step="1"
              placeholder="2"
              class="form-control"
              style="width: 80px"
            />
          </div>
          <!-- Show value label (all chart types) -->
          <div v-if="activeConfigField.type === 'measures'" class="form-group">
            <label class="pie-opt">
              <input type="checkbox" v-model="activeConfigField.field.showLabel" />
              <span>Mostrar valor en el gráfico</span>
            </label>
          </div>
          <template v-if="activeConfigField.type === 'measures' && activeConfigField.field.showLabel">
            <div class="form-group form-row">
              <div class="form-col">
                <label>Rotación etiqueta (°)</label>
                <input
                  type="number"
                  v-model.number="activeConfigField.field.labelRotate"
                  min="-90" max="90" step="5"
                  placeholder="0"
                  class="form-control"
                />
              </div>
              <div class="form-col">
                <label>Posición</label>
                <div class="ct-combobox" :class="{ open: labelPositionOpen }" @click.stop="labelPositionOpen = !labelPositionOpen">
                  <div class="ct-combobox-trigger">
                    <span class="ct-name">{{ activeLabelPositionLabel }}</span>
                    <svg class="ct-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                  </div>
                  <div v-if="labelPositionOpen" class="ct-combobox-dropdown" @click.stop>
                    <div v-for="pos in labelPositions" :key="pos.value" class="ct-combobox-option" :class="{ selected: activeConfigField.field.labelPosition === pos.value }" @click="activeConfigField.field.labelPosition = pos.value; labelPositionOpen = false">
                      <span class="ct-name">{{ pos.label }}</span>
                      <svg v-if="activeConfigField.field.labelPosition === pos.value" class="ct-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- Pie chart display options -->
          <div v-if="activeConfigField.type === 'measures' && store.chartType === 'pie'" class="form-group">
            <label>Etiquetas del gráfico</label>
            <div class="pie-label-options">
              <label class="pie-opt">
                <input type="checkbox" v-model="store.pieOptions.showValue" />
                <span>Valor</span>
              </label>
              <label class="pie-opt">
                <input type="checkbox" v-model="store.pieOptions.showPercent" />
                <span>Porcentaje</span>
              </label>
              <label class="pie-opt">
                <input type="checkbox" v-model="store.pieOptions.showTotal" />
                <span>Total en centro</span>
              </label>
            </div>
          </div>

          <!-- Eje Y secundario: solo para gráfico combinado -->
          <div v-if="store.chartType === 'combined'" class="form-group">
            <label>Eje Y secundario (derecho)</label>
            <label class="pie-opt" style="cursor:pointer" @click="store.combinedOptions.showSecondaryYAxis = !store.combinedOptions.showSecondaryYAxis">
              <input type="checkbox" :checked="store.combinedOptions.showSecondaryYAxis" readonly />
              <span>{{ store.combinedOptions.showSecondaryYAxis ? 'Activado' : 'Desactivado' }}</span>
            </label>
          </div>

          <!-- Series type: only for bar chart -->
          <div v-if="activeConfigField.type === 'measures' && store.chartType === 'bar'" class="form-group">
            <label>Tipo de serie</label>
            <div class="series-type-toggle">
              <button
                class="series-type-btn"
                :class="{ active: !activeConfigField.field.seriesType || activeConfigField.field.seriesType === 'bar' }"
                @click="activeConfigField.field.seriesType = 'bar'"
              >📊 Barra</button>
              <button
                class="series-type-btn"
                :class="{ active: activeConfigField.field.seriesType === 'line' }"
                @click="activeConfigField.field.seriesType = 'line'"
              >📈 Línea</button>
            </div>
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn btn-secondary" @click="closeConfig">Cancelar</button>
          <button class="btn btn-primary" @click="updateFieldConfig">Aplicar</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import draggable from 'vuedraggable'
import { useVisualizationConfiguratorStore } from '@/stores/visualizationConfigurator'
import { useUIStore } from '@/stores/ui'
import { useDashboardStore } from '@/stores/dashboard'
import { useCubeStore } from '@/stores/cubejs'
import { useCurrencyStore } from '@/stores/currencies'
import { useCubeQuery } from '@/composables/useCubeQuery'
import EChartWrapper from '@/components/charts/EChartWrapper.vue'
import KpiWidget from '@/components/charts/KpiWidget.vue'

const router = useRouter()
const route = useRoute()
const store = useVisualizationConfiguratorStore()
const uiStore = useUIStore()
const dashboardStore = useDashboardStore()
const cubeStore = useCubeStore()
const currencyStore = useCurrencyStore()
currencyStore.loadFromBackend()

// Search states
const measureSearch = ref('')
const dimensionSearch = ref('')
const saving = ref(false)
const configCollapsed = ref(false)
const activeConfigField = ref(null) // { type: 'measures'|'dimensions', field: Object }

// Source panel: show/hide cube name prefix (default: hidden)
const showCubeName = ref(false)

// Cube combobox state
const cubeOpen = ref(false)
const activeCubeLabel = computed(() => {
  const cube = availableCubes.value.find(c => c.name === store.selectedCube)
  return cube ? (cube.title || cube.name) : 'Seleccionar cubo...'
})

// Chart type combobox state
const chartTypeOpen = ref(false)
const activeChartType = computed(() => chartTypes.find(ct => ct.value === store.chartType) || chartTypes[0])

// Format combobox state (modal Configurar Métrica)
const formatOpen = ref(false)
const currencyOpen = ref(false)
const formatOptions = [
  { value: 'number',   label: 'Número' },
  { value: 'currency', label: 'Moneda' },
  { value: 'percent',  label: 'Porcentaje' },
]
const activeFormatLabel = computed(() => {
  const fmt = formatOptions.find(f => f.value === activeConfigField.value?.field?.format)
  return fmt ? fmt.label : 'Predeterminado'
})

// Label position combobox state (modal Configurar Métrica)
const labelPositionOpen = ref(false)
const labelPositions = [
  { value: 'top',       label: 'Arriba' },
  { value: 'inside',    label: 'Dentro' },
  { value: 'insideTop', label: 'Dentro arriba' },
  { value: 'bottom',    label: 'Abajo' },
  { value: 'right',     label: 'Derecha' },
]
const activeLabelPositionLabel = computed(() => {
  const pos = labelPositions.find(p => p.value === activeConfigField.value?.field?.labelPosition)
  return pos ? pos.label : 'Arriba'
})

// Filter multiselect state
const filterOptions = ref({}) // { fullName: string[] }
const openFilterDropdown = ref(null)

// Chart type definitions
const chartTypes = [
  { value: 'bar',      label: 'Barras',    icon: '📊' },
  { value: 'line',     label: 'Líneas',    icon: '📈' },
  { value: 'pie',      label: 'Circular',  icon: '🥧' },
  { value: 'gauge',    label: 'Indicador', icon: '🎯' },
  { value: 'radar',    label: 'Radar',     icon: '🕸️' },
  { value: 'combined', label: 'Combinado', icon: '📉' },
  { value: 'table',    label: 'Tabla',     icon: '🗒️' },
  { value: 'kpi',      label: 'KPI',       icon: '🔢' },
]

const toggleConfig = () => {
  configCollapsed.value = !configCollapsed.value
}

// Close filter dropdown when clicking outside
function onDocClick() { openFilterDropdown.value = null; chartTypeOpen.value = false; cubeOpen.value = false; formatOpen.value = false; currencyOpen.value = false; labelPositionOpen.value = false }
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))

// Computed widget for useCubeQuery and persistence
const currentWidget = computed(() => ({
  id: store.widgetId,
  title: store.title,
  chartType: store.chartType,
  cubeQuery: {
    measures: store.measures.map(m => ({
      key: m.fullName,
      label: m.alias || m.title,
      format: m.format,
      currencyId: m.currencyId ?? null,
      decimalPlaces: m.decimalPlaces,
      seriesType: m.seriesType,
      showLabel: m.showLabel,
      labelRotate: m.labelRotate,
      labelPosition: m.labelPosition,
    })),
    dimensions: store.dimensions.map(d => ({ 
      key: d.fullName, 
      label: d.alias || d.title 
    })),
    filters: store.filters.map(f => ({
      member: f.fullName,
      operator: f.operator || 'equals',
      values: f.values || []
    })),
    limit: 100
  },
  chartOptions: store.chartOptions,
  pieOptions: store.pieOptions,
  combinedOptions: store.combinedOptions,
  kpiOptions: store.kpiOptions || { icon: '', accentColor: '', invertTrend: false, showComparison: true, comparisonLabel: 'vs período anterior' },
  useMockData: false
}))

const openConfig = (type, field) => {
  activeConfigField.value = { type, field: { ...field } }
}

const closeConfig = () => {
  activeConfigField.value = null
}

const updateFieldConfig = () => {
  if (!activeConfigField.value) return
  
  const { type, field } = activeConfigField.value
  if (type === 'measures') {
    store.updateMeasure(field.fullName, {
      alias: field.alias,
      format: field.format,
      currencyId: field.currencyId ?? null,
      decimalPlaces: field.decimalPlaces,
      seriesType: field.seriesType,
      showLabel: field.showLabel,
      labelRotate: field.labelRotate,
      labelPosition: field.labelPosition,
    })
  } else if (type === 'dimensions') {
    store.updateDimension(field.fullName, { alias: field.alias })
  }
  closeConfig()
}

const { data, loading, error, fetchData } = useCubeQuery(currentWidget)

// Re-fetch data when query configuration changes
// Re-fetch only when the actual query config changes, not when the user browses a different cube
watch([() => store.measures, () => store.dimensions, () => store.filters], () => {
  if (store.measures.length > 0) {
    fetchData()
  }
}, { deep: true })

// --- Table preview ---
const tableColumns = computed(() => {
  const cols = []
  store.dimensions.forEach(d => cols.push({ key: d.fullName, label: d.alias || d.title, kind: 'dimension' }))
  store.measures.forEach(m => cols.push({ key: m.fullName, label: m.alias || m.title, kind: 'measure' }))
  return cols
})

function getTableCell(row, col) {
  // Real cube data: raw contains the cube keys
  if (row.raw && row.raw[col.key] !== undefined) return row.raw[col.key]
  // Mock data fallback
  if (col.kind === 'measure') return row.value ?? ''
  return row.label ?? ''
}

// --- Filter multiselect ---
async function loadFilterOptions(fullName) {
  if (filterOptions.value[fullName] !== undefined) return
  if (!cubeStore.token || !cubeStore.apiUrl) { filterOptions.value[fullName] = []; return }
  filterOptions.value[fullName] = [] // mark as loading
  try {
    const result = await cubeStore.executeQuery({ dimensions: [fullName], limit: 500 })
    const rows = result.tablePivot ? result.tablePivot() : []
    filterOptions.value[fullName] = [...new Set(rows.map(r => r[fullName]).filter(v => v != null && v !== ''))]
  } catch {
    filterOptions.value[fullName] = []
  }
}

watch(() => store.filters, (filters) => {
  filters.forEach(f => {
    if (f.type === 'string' || f.memberType === 'string') loadFilterOptions(f.fullName)
  })
}, { deep: true, immediate: true })

function toggleFilterDropdown(fullName) {
  openFilterDropdown.value = openFilterDropdown.value === fullName ? null : fullName
}

function toggleFilterValue(fullName, value, current) {
  const next = current.includes(value)
    ? current.filter(v => v !== value)
    : [...current, value]
  store.updateFilter(fullName, { values: next, operator: 'equals' })
}

function getFilterDisplayValue(f) {
  const vals = f.values || []
  if (vals.length === 0) return 'Todos'
  if (vals.length === 1) return vals[0]
  return `${vals.length} seleccionados`
}

// Data source computed properties
const availableCubes = computed(() => cubeStore.cubes)

// Set of cube names that already have fields in the current config
const usedCubes = computed(() => {
  const names = new Set()
  ;[...store.measures, ...store.dimensions, ...store.filters].forEach(f => {
    const cube = f.fullName?.split('.')[0]
    if (cube) names.add(cube)
  })
  return names
})

const currentMeasures = computed(() => {
  if (!store.selectedCube) return []
  const measures = cubeStore.getMeasuresForCube(store.selectedCube)
  return measures
    .map(m => ({
      ...m,
      fullName: m.name.includes('.') ? m.name : `${store.selectedCube}.${m.name}`,
      cubeName: store.selectedCube
    }))
    .filter(m => 
      m.title.toLowerCase().includes(measureSearch.value.toLowerCase()) ||
      m.fullName.toLowerCase().includes(measureSearch.value.toLowerCase())
    )
})

const currentDimensions = computed(() => {
  if (!store.selectedCube) return []
  const dimensions = cubeStore.getDimensionsForCube(store.selectedCube)
  return dimensions
    .map(d => ({
      ...d,
      fullName: d.name.includes('.') ? d.name : `${store.selectedCube}.${d.name}`,
      cubeName: store.selectedCube
    }))
    .filter(d => 
      d.title.toLowerCase().includes(dimensionSearch.value.toLowerCase()) ||
      d.fullName.toLowerCase().includes(dimensionSearch.value.toLowerCase())
    )
})

onMounted(async () => {
  const dashboardId = route.params.dashboardId
  const widgetId = route.params.widgetId
  
  // Ensure metadata is loaded
  if (!cubeStore.meta) {
    await cubeStore.loadConfigFromBackend()
    await cubeStore.loadMeta()
  }

  if (dashboardId) {
    store.setDashboardId(dashboardId)
    
    // Load dashboards if they aren't loaded yet
    if (dashboardStore.allDashboards.length === 0) {
      await dashboardStore.loadFromBackend()
    }
    
    const db = dashboardStore.allDashboards.find(d => d.id === dashboardId)
    if (db) {
      if (widgetId) {
        const widget = db.widgets.find(w => w.id === widgetId)
        if (widget) {
          store.setWidget(widget)
          uiStore.setBreadcrumbs(['Diseño', db.name, 'Configurar: ' + widget.title])
        } else {
          uiStore.setBreadcrumbs(['Diseño', db.name, 'Nuevo Gráfico'])
        }
      } else {
        uiStore.setBreadcrumbs(['Diseño', db.name, 'Nuevo Gráfico'])
      }
    } else {
      uiStore.setBreadcrumbs(['Diseño', 'Configurador'])
    }
  }

  // Set default cube if none selected
  if (!store.selectedCube && cubeStore.cubes.length > 0) {
    store.setCube(cubeStore.cubes[0].name)
  }
})

onUnmounted(() => {
  store.reset()
})

const handleSave = async () => {
  if (!store.dashboardId) return
  
  saving.value = true
  try {
    if (store.widgetId) {
      await dashboardStore.updateWidget(store.dashboardId, store.widgetId, currentWidget.value)
    } else {
      await dashboardStore.addWidget(store.dashboardId, currentWidget.value)
    }
    router.push(`/designer/${store.dashboardId}`)
  } catch (err) {
    console.error('Failed to save widget:', err)
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  if (store.dashboardId) {
    router.push(`/designer/${store.dashboardId}`)
  } else {
    router.push('/designer')
  }
}
</script>

<style scoped>
.configurator-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--topbar-height) - 48px); /* Adjust based on layout */
  gap: 16px;
}

.configurator-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  flex: 1;
  max-width: 400px;
}

.title-input {
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.title-input:hover {
  background: #f0f0f0;
}

.title-input:focus {
  outline: none;
  background: white;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.1);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.configurator-content {
  display: grid;
  grid-template-columns: 280px 320px 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
  transition: grid-template-columns 0.3s ease;
}

.configurator-content.is-collapsed {
  grid-template-columns: 280px 48px 1fr;
}

.panel-config.collapsed {
  width: 48px;
  padding: 0;
}

.header-left-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-btn {
  background: transparent;
  border: none;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #f0f0f0;
  color: var(--primary);
}

.filter-field {
  border-style: dotted !important;
  border-color: #94a3b8 !important;
}

.panel {
  display: flex;
  flex-direction: column;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow);
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
}

.panel-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.panel-preview {
  background: var(--bg); /* Subtle contrast for preview area */
  border: none;
  box-shadow: none;
}

.panel-preview .panel-header {
  background: transparent;
  border-bottom: none;
  padding-bottom: 8px;
}

.panel-preview .panel-body {
  padding: 0 0 16px 0;
  display: flex;
  flex-direction: column;
}

.preview-container {
  flex: 1;
  background: var(--card-bg);
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
  height: 100%;
  gap: 12px;
}

.empty-icon {
  font-size: 40px;
  opacity: 0.3;
}

.empty-state h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
}

.empty-state p {
  font-size: 14px;
  max-width: 240px;
  line-height: 1.5;
}

/* Source Panel Styles */
.cube-selector {
  margin-bottom: 20px;
}

.cube-selector label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.source-lists {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.source-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.search-box input {
  width: 100%;
  padding: 6px 10px;
  font-size: 13px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
}

.search-box input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.1);
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
  user-select: none;
}

.field-item:hover {
  border-color: var(--primary);
  background: #f0f7ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.field-content {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  opacity: 0.3;
  cursor: grab;
  flex-shrink: 0;
}

.field-item:hover .drag-handle {
  opacity: 0.7;
}

.field-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.field-icon.measure {
  background: #e1f5fe;
  color: #0288d1;
}

.field-icon.dimension {
  background: #e8f5e9;
  color: #2e7d32;
}

.field-label {
  font-size: 13px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-results {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  padding: 12px;
  font-style: italic;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 12px;
  color: var(--text-secondary);
}
.spinner-sm {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(0,0,0,0.1);
  border-left-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-xs {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-left-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
  margin-right: 8px;
  vertical-align: middle;
}

.panel-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 100;
  backdrop-filter: blur(2px);
  color: var(--text);
  font-weight: 500;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0,0,0,0.1);
  border-left-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Transitions */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.list-move {
  transition: transform 0.3s ease;
}

/* Config Panel Styles */
.config-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.section-label span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.section-label small {
  font-size: 11px;
  color: var(--text-secondary);
}

.drop-zone {
  min-height: 50px;
  background: #fcfcfc;
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s;
}

.drop-zone:empty {
  display: none; /* Hide if truly empty to let footer show */
}

.drop-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.6;
}

.active-field {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  cursor: default !important;
}

.active-field .drag-handle {
  cursor: grab;
}

.remove-btn {
  background: transparent;
  border: none;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.4;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #ef4444;
  opacity: 1;
}

/* Field Actions & Modal */
.field-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  background: transparent;
  border: none;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.4;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f0f0f0;
  color: var(--primary);
  opacity: 1;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.field-config-modal {
  width: 100%;
  max-width: 400px;
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 24px;
  line-height: 1;
  color: var(--text-secondary);
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fafafa;
}

.filter-field-config {
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 8px !important;
  padding: 10px !important;
}

.filter-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-settings {
  display: flex;
  gap: 6px;
}

.select-xs {
  padding: 2px 4px !important;
  font-size: 11px !important;
  height: 24px !important;
  width: 100px !important;
}

.input-xs {
  padding: 2px 8px !important;
  font-size: 11px !important;
  height: 24px !important;
  flex: 1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ---- Used cubes hint ---- */
.used-cubes-hint {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}
.used-cube-tag {
  background: rgba(24,144,255,0.1);
  color: var(--primary);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 500;
}

/* ---- Source panel: toggle cube name ---- */
.toggle-cube-name {
  color: var(--text-secondary);
  transition: color 0.15s;
}
.toggle-cube-name:hover,
.toggle-cube-name.active { color: var(--primary); }

/* ---- Chart type combobox ---- */
.ct-combobox {
  position: relative;
  width: 100%;
}
.ct-combobox-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: border-color 0.15s;
  user-select: none;
}
.ct-combobox-trigger:hover,
.ct-combobox.open .ct-combobox-trigger { border-color: var(--primary); }
.ct-icon { font-size: 16px; line-height: 1; flex-shrink: 0; }
.ct-name { flex: 1; font-size: 13px; color: var(--text); }
.ct-arrow {
  color: var(--text-secondary);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.ct-combobox.open .ct-arrow { transform: rotate(180deg); }
.ct-combobox-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 300;
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
}
.ct-combobox-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.1s;
  font-size: 13px;
  color: var(--text);
}
.ct-combobox-option:hover { background: #f5f7fa; }
.ct-combobox-option.selected { background: rgba(24,144,255,0.06); color: var(--primary); font-weight: 500; }
.ct-check { margin-left: auto; color: var(--primary); flex-shrink: 0; }

/* ---- Preview table ---- */
.preview-table-wrap {
  width: 100%;
  height: 100%;
  overflow: auto;
}
.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.preview-table th {
  position: sticky;
  top: 0;
  background: #f5f5f5;
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}
.preview-table td {
  padding: 6px 12px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.preview-table tbody tr:hover { background: #fafafa; }

/* ---- Filter multiselect ---- */
.filter-multiselect { position: relative; flex: 1; }
.filter-ms-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  width: 100%;
  padding: 3px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 11px;
  text-align: left;
}
.filter-ms-trigger:hover { border-color: var(--primary); }
.filter-ms-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.filter-ms-dropdown {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  z-index: 200;
  background: white;
  border: 1px solid var(--border);
  border-radius: 6px;
  box-shadow: var(--shadow-md);
  min-width: 180px;
  max-height: 220px;
  overflow-y: auto;
  padding: 4px 0;
}
.filter-ms-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.1s;
}
.filter-ms-option:hover { background: #f5f5f5; }
.filter-ms-option input[type="checkbox"] { margin: 0; cursor: pointer; }
.filter-ms-empty { padding: 8px 12px; color: var(--text-secondary); font-size: 11px; }

/* ---- Form helpers ---- */
.form-row { display: flex; gap: 10px; }
.form-col { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.field-config-modal .form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1.5px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text);
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
  box-sizing: border-box;
}
.field-config-modal .form-control:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(24,144,255,0.12);
}
.field-config-modal label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 4px;
  display: block;
}
/* used-dot in cube combobox */
.used-dot { margin-left: auto; color: var(--primary); font-size: 10px; }

/* ---- Pie label options ---- */
.pie-label-options { display: flex; flex-direction: column; gap: 8px; }
.pie-opt {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
}
.pie-opt input[type="checkbox"] { cursor: pointer; }

/* ---- Series type toggle ---- */
.series-type-toggle { display: flex; gap: 6px; }
.series-type-btn {
  flex: 1;
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-secondary);
  transition: all 0.15s;
}
.series-type-btn:hover { border-color: var(--primary); color: var(--primary); }
.series-type-btn.active { border-color: var(--primary); background: rgba(24,144,255,0.1); color: var(--primary); font-weight: 600; }
</style>
