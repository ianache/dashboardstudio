<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box" style="max-width: 700px;">
      <div class="modal-header">
        <h3>
          <span style="margin-right:8px">⚙️</span>
          Configurar Widget
        </h3>
        <button class="btn-icon" @click="$emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="tabs" style="padding: 0 20px; margin-bottom: 0; border-bottom: 1px solid var(--border);">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >{{ tab.label }}</button>
      </div>

      <div class="modal-body">
        <!-- TAB: General -->
        <div v-if="activeTab === 'general'">
          <div class="config-grid">
            <div class="form-group">
              <label class="form-label">Título del widget</label>
              <input v-model="form.title" type="text" class="form-input" placeholder="Ej: Ventas Mensuales" />
            </div>

            <div class="form-group">
              <label class="form-label">Tipo de gráfico</label>
              <div class="chart-type-grid">
                <div
                  v-for="ct in chartTypes"
                  :key="ct.value"
                  class="chart-type-card"
                  :class="{ selected: form.chartType === ct.value }"
                  @click="form.chartType = ct.value"
                >
                  <span class="ct-icon">{{ ct.icon }}</span>
                  <span class="ct-label">{{ ct.label }}</span>
                </div>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                <input type="checkbox" v-model="form.useMockData" />
                Usar datos de demostración
              </label>
              <span class="form-hint">Activa esto para visualizar el gráfico sin conexión a CubeJS</span>
            </div>

            <div class="form-group" style="flex-direction: row; align-items: center; gap: 12px;">
              <div style="flex:1">
                <label class="form-label">Ancho (columnas de 12)</label>
                <div style="display:flex; align-items:center; gap:8px">
                  <input v-model.number="form.position.w" type="range" min="1" max="12" style="flex:1"/>
                  <span style="width:24px; text-align:center; font-weight:600">{{ form.position.w }}</span>
                </div>
              </div>
              <div style="flex:1">
                <label class="form-label">Alto (filas)</label>
                <div style="display:flex; align-items:center; gap:8px">
                  <input v-model.number="form.position.h" type="range" min="1" max="10" style="flex:1"/>
                  <span style="width:24px; text-align:center; font-weight:600">{{ form.position.h }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB: Datos CubeJS -->
        <div v-if="activeTab === 'data'">
          <div class="config-grid">
            <!-- Measures -->
            <div class="form-group">
              <label class="form-label">Medidas (Measures)</label>
              <div class="measure-list">
                <div
                  v-for="(measure, idx) in form.cubeQuery.measures"
                  :key="idx"
                  class="measure-row"
                >
                  <input
                    v-model="form.cubeQuery.measures[idx].key"
                    type="text"
                    class="form-input"
                    placeholder="Ej: Orders.totalRevenue"
                    style="flex:2"
                  />
                  <input
                    v-model="form.cubeQuery.measures[idx].label"
                    type="text"
                    class="form-input"
                    placeholder="Etiqueta"
                    style="flex:1"
                  />
                  <input
                    v-model="form.cubeQuery.measures[idx].color"
                    type="color"
                    class="color-picker"
                    :title="'Color serie ' + (idx+1)"
                  />
                  <!-- Formato de la medida -->
                  <select
                    v-model="measure.format"
                    class="form-input form-select measure-format-select"
                    :title="'Formato de la medida'"
                  >
                    <option value="numero">Número</option>
                    <option value="moneda">Moneda</option>
                    <option value="porcentaje">Porcentaje</option>
                  </select>
                  <!-- Selector de moneda (solo si formato = moneda) -->
                  <select
                    v-if="measure.format === 'moneda'"
                    v-model="measure.currencyId"
                    class="form-input form-select measure-currency-select"
                    :title="'Moneda'"
                  >
                    <option :value="null">— Moneda —</option>
                    <option
                      v-for="cur in currencyStore.activeCurrencies"
                      :key="cur.id"
                      :value="cur.id"
                    >{{ cur.symbol }} {{ cur.code }}</option>
                  </select>
                  <!-- Estilo de serie (solo bar y combined) -->
                  <div
                    v-if="form.chartType === 'bar' || form.chartType === 'combined'"
                    class="series-type-toggle"
                    :title="'Estilo de visualización'"
                  >
                    <button
                      v-for="st in seriesTypes"
                      :key="st.value"
                      class="st-btn"
                      :class="{ active: (form.cubeQuery.measures[idx].seriesType || 'bar') === st.value }"
                      :title="st.label"
                      @click="form.cubeQuery.measures[idx].seriesType = st.value"
                    >{{ st.icon }}</button>
                  </div>
                  <button class="btn-icon" @click="removeMeasure(idx)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
                <button class="btn btn-secondary btn-sm" @click="addMeasure" style="align-self:flex-start">
                  + Añadir medida
                </button>
              </div>
              <span class="form-hint">Ejemplo: <code>Orders.count</code>, <code>Revenue.total</code></span>
            </div>

            <!-- Dimensions -->
            <div class="form-group">
              <label class="form-label">Dimensiones (Dimensions)</label>
              <div class="measure-list">
                <div
                  v-for="(dim, idx) in form.cubeQuery.dimensions"
                  :key="idx"
                  class="measure-row"
                >
                  <input
                    v-model="form.cubeQuery.dimensions[idx].key"
                    type="text"
                    class="form-input"
                    placeholder="Ej: Orders.status"
                    style="flex:2"
                  />
                  <input
                    v-model="form.cubeQuery.dimensions[idx].label"
                    type="text"
                    class="form-input"
                    placeholder="Etiqueta"
                    style="flex:1"
                  />
                  <button class="btn-icon" @click="removeDimension(idx)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
                <button class="btn btn-secondary btn-sm" @click="addDimension" style="align-self:flex-start">
                  + Añadir dimensión
                </button>
              </div>
            </div>

            <!-- Time Dimension -->
            <div class="form-group">
              <label class="form-label">Dimensión de tiempo (opcional)</label>
              <div class="measure-row">
                <input
                  v-model="timeDimKey"
                  type="text"
                  class="form-input"
                  placeholder="Ej: Orders.createdAt"
                  style="flex:2"
                />
                <select v-model="timeDimGranularity" class="form-input form-select" style="flex:1">
                  <option value="">Sin granularidad</option>
                  <option value="day">Día</option>
                  <option value="week">Semana</option>
                  <option value="month">Mes</option>
                  <option value="quarter">Trimestre</option>
                  <option value="year">Año</option>
                </select>
              </div>
            </div>

            <!-- Filters -->
            <div class="form-group">
              <label class="form-label">Filtros</label>
              <div class="measure-list">
                <div v-for="(filter, idx) in form.cubeQuery.filters" :key="idx" class="filter-row">
                  <input v-model="filter.member" class="form-input" placeholder="Miembro" style="flex:2" />
                  <select v-model="filter.operator" class="form-input form-select" style="flex:1">
                    <option value="equals">Igual</option>
                    <option value="notEquals">No igual</option>
                    <option value="contains">Contiene</option>
                    <option value="gt">Mayor que</option>
                    <option value="lt">Menor que</option>
                    <option value="gte">Mayor o igual</option>
                    <option value="lte">Menor o igual</option>
                  </select>
                  <input v-model="filter.values[0]" class="form-input" placeholder="Valor" style="flex:1" />
                  <button class="btn-icon" @click="removeFilter(idx)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
                <button class="btn btn-secondary btn-sm" @click="addFilter" style="align-self:flex-start">
                  + Añadir filtro
                </button>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Límite de filas</label>
              <input v-model.number="form.cubeQuery.limit" type="number" min="1" max="5000" class="form-input" style="width:120px" />
            </div>
          </div>
        </div>

        <!-- TAB: Visualización -->
        <div v-if="activeTab === 'visual'">
          <div class="config-grid">

            <!-- Color Palette -->
            <div class="form-group">
              <label class="form-label">Paleta de colores del widget</label>
              <div class="palette-grid">

                <!-- Inherit from dashboard (null) -->
                <div
                  class="palette-card palette-card--special"
                  :class="{ selected: form.colorPalette == null }"
                  @click="form.colorPalette = null"
                >
                  <div class="palette-swatches palette-swatches--inherit">
                    <svg width="20" height="14" viewBox="0 0 20 14" fill="none">
                      <rect x="0.5" y="0.5" width="19" height="13" rx="2.5" stroke="currentColor" stroke-dasharray="3 2"/>
                      <path d="M6 7h8M10 4l3 3-3 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="palette-label">Heredar</span>
                </div>

                <!-- No palette ('none') -->
                <div
                  class="palette-card palette-card--special"
                  :class="{ selected: form.colorPalette === 'none' }"
                  @click="form.colorPalette = 'none'"
                >
                  <div class="palette-swatches palette-swatches--none">
                    <span class="palette-swatch" style="background:#1890ff"/>
                    <span class="palette-swatch" style="background:#52c41a"/>
                    <span class="palette-swatch" style="background:#faad14"/>
                    <span class="palette-swatch" style="background:#f5222d"/>
                    <span class="palette-swatch" style="background:#722ed1"/>
                    <span class="palette-swatch" style="background:#13c2c2"/>
                  </div>
                  <span class="palette-label">Sin paleta</span>
                </div>

                <!-- Named palettes -->
                <div
                  v-for="palette in paletteStore.allPalettes"
                  :key="palette.id"
                  class="palette-card"
                  :class="{ selected: form.colorPalette === palette.id }"
                  @click="form.colorPalette = palette.id"
                >
                  <div class="palette-swatches">
                    <span
                      v-for="color in palette.colors.slice(0, 6)"
                      :key="color"
                      class="palette-swatch"
                      :style="{ background: color }"
                    ></span>
                  </div>
                  <span class="palette-label">{{ palette.label }}</span>
                </div>

              </div>
            </div>

            <!-- Pie-specific options -->
            <div v-if="form.chartType === 'pie'" class="form-group pie-options-group">
              <label class="form-label">Opciones del gráfico Pie</label>
              <div class="pie-options-row">
                <label class="pie-opt-toggle" :class="{ active: form.pieOptions.showValue }" @click="form.pieOptions.showValue = !form.pieOptions.showValue">
                  <span class="pie-opt-icon">{{ form.pieOptions.showValue ? '✓' : '' }}</span>
                  Mostrar valor
                </label>
                <label class="pie-opt-toggle" :class="{ active: form.pieOptions.showPercent }" @click="form.pieOptions.showPercent = !form.pieOptions.showPercent">
                  <span class="pie-opt-icon">{{ form.pieOptions.showPercent ? '✓' : '' }}</span>
                  Mostrar porcentaje
                </label>
                <label class="pie-opt-toggle" :class="{ active: form.pieOptions.showTotal }" @click="form.pieOptions.showTotal = !form.pieOptions.showTotal">
                  <span class="pie-opt-icon">{{ form.pieOptions.showTotal ? '✓' : '' }}</span>
                  Total al centro
                </label>
              </div>
            </div>

            <!-- Combined-specific options -->
            <div v-if="form.chartType === 'combined'" class="form-group pie-options-group">
              <label class="form-label">Opciones del gráfico Combinado</label>
              <div class="pie-options-row">
                <label
                  class="pie-opt-toggle"
                  :class="{ active: form.combinedOptions.showSecondaryYAxis }"
                  @click="form.combinedOptions.showSecondaryYAxis = !form.combinedOptions.showSecondaryYAxis"
                >
                  <span class="pie-opt-icon">{{ form.combinedOptions.showSecondaryYAxis ? '✓' : '' }}</span>
                  Eje Y secundario (derecho)
                </label>
              </div>
            </div>

            <!-- KPI-specific options -->
            <div v-if="form.chartType === 'kpi'" class="form-group kpi-options-group">
              <label class="form-label">Opciones del KPI</label>
              <div class="kpi-options-grid">
                <div class="kpi-opt-field">
                  <label class="kpi-opt-label">Ícono (Material Symbol o emoji)</label>
                  <input v-model="form.kpiOptions.icon" type="text" class="form-input" placeholder="Ej: trending_up, 💰, paid" />
                </div>
                <div class="kpi-opt-field">
                  <label class="kpi-opt-label">Color de acento</label>
                  <div style="display:flex;align-items:center;gap:8px">
                    <input v-model="form.kpiOptions.accentColor" type="color" class="color-picker" title="Color de acento del KPI" />
                    <input v-model="form.kpiOptions.accentColor" type="text" class="form-input" placeholder="#1890ff" style="flex:1" />
                    <button class="btn-icon" title="Restablecer" @click="form.kpiOptions.accentColor = ''">
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="kpi-opt-field">
                  <label class="kpi-opt-label">Etiqueta comparación</label>
                  <input v-model="form.kpiOptions.comparisonLabel" type="text" class="form-input" placeholder="vs período anterior" />
                </div>
                <div class="kpi-opt-toggles">
                  <label class="pie-opt-toggle" :class="{ active: form.kpiOptions.showComparison }" @click="form.kpiOptions.showComparison = !form.kpiOptions.showComparison">
                    <span class="pie-opt-icon">{{ form.kpiOptions.showComparison ? '✓' : '' }}</span>
                    Mostrar tendencia
                  </label>
                  <label class="pie-opt-toggle" :class="{ active: form.kpiOptions.invertTrend }" @click="form.kpiOptions.invertTrend = !form.kpiOptions.invertTrend">
                    <span class="pie-opt-icon">{{ form.kpiOptions.invertTrend ? '✓' : '' }}</span>
                    Invertir sentido (↑ = malo)
                  </label>
                </div>
              </div>
              <span class="form-hint">Medida 1 = valor actual · Medida 2 = valor de comparación (para calcular tendencia)</span>
            </div>

            <div class="form-group">
              <div class="visual-label-row">
                <label class="form-label">Opciones ECharts (JSON)</label>
                <button class="btn-ai-assist" :class="{ active: aiOpen }" @click="aiOpen = !aiOpen">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
                  </svg>
                  IA Assist
                </button>
              </div>
              <span class="form-hint">
                Estas opciones se fusionan con las predeterminadas del gráfico.
                <a href="https://echarts.apache.org/en/option.html" target="_blank" rel="noopener">Ver documentación →</a>
              </span>

              <!-- IA Assist Panel -->
              <div v-if="aiOpen" class="ai-panel">
                <div class="ai-panel-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
                  </svg>
                  <span>IA Assist — Generador de opciones ECharts</span>
                  <span v-if="llmStore.isConfigured" class="ai-model-badge">
                    {{ llmStore.configFor('chartAssist').providerLabel }} · {{ llmStore.configFor('chartAssist').modelLabel }}
                  </span>
                </div>

                <div class="ai-panel-body">
                  <div v-if="!llmStore.isConfigured" class="alert alert-error" style="margin:0">
                    Sin clave API configurada.
                    <router-link to="/settings" @click="$emit('close')" style="color:inherit;font-weight:600;margin-left:4px">
                      Ir a Configuración →
                    </router-link>
                  </div>

                  <div class="ai-context-chips">
                    <span class="ai-chip ai-chip-type">{{ form.chartType }}</span>
                    <span v-for="m in form.cubeQuery.measures" :key="m.key" class="ai-chip ai-chip-measure">{{ m.label || m.key }}</span>
                    <span v-for="d in form.cubeQuery.dimensions" :key="d.key" class="ai-chip ai-chip-dim">{{ d.label || d.key }}</span>
                  </div>

                  <div class="form-group" style="margin:0">
                    <label class="form-label">¿Qué quieres personalizar?</label>
                    <textarea
                      v-model="aiPrompt"
                      class="form-input"
                      rows="3"
                      placeholder="Ej: Muestra los valores encima de cada barra, usa colores degradados de azul a verde, añade líneas de referencia en 1000 y 2000"
                      @keydown.ctrl.enter="generateWithAI"
                    ></textarea>
                    <span class="form-hint">Ctrl+Enter para generar</span>
                  </div>

                  <button
                    class="btn btn-primary"
                    style="align-self:flex-start"
                    :disabled="!llmStore.isConfigured || !aiPrompt.trim() || aiLoading"
                    @click="generateWithAI"
                  >
                    <svg v-if="aiLoading" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                    </svg>
                    <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
                    </svg>
                    {{ aiLoading ? 'Generando...' : 'Generar opciones' }}
                  </button>

                  <div v-if="aiError" class="alert alert-error">{{ aiError }}</div>

                  <div v-if="aiResult" class="ai-result">
                    <div class="ai-result-header">
                      <span>Resultado</span>
                      <div style="display:flex;gap:6px">
                        <button class="btn btn-secondary btn-sm" @click="applyAIResult(false)">Fusionar con actual</button>
                        <button class="btn btn-primary btn-sm" @click="applyAIResult(true)">Reemplazar</button>
                      </div>
                    </div>
                    <textarea class="form-input json-editor" readonly :value="aiResult" rows="8"></textarea>
                  </div>
                </div>
              </div>

              <textarea
                v-model="chartOptionsJson"
                class="form-input json-editor"
                placeholder='{"tooltip": {"formatter": "{b}: {c}"}}'
                rows="12"
              ></textarea>
              <div v-if="jsonError" class="alert alert-error" style="margin-top:8px">
                {{ jsonError }}
              </div>
            </div>
          </div>
        </div>

        <!-- CubeJS meta -->
        <div v-if="activeTab === 'cubemeta'" class="cube-meta-tab">
          <div class="cube-meta-toolbar">
            <span class="cube-meta-count" v-if="cubeStore.cubes.length">
              {{ cubeStore.cubes.length }} cubos disponibles
            </span>
            <span v-else></span>
            <button
              class="btn btn-secondary btn-sm"
              :disabled="cubeStore.metaLoading"
              @click="refreshMeta"
            >
              <svg :class="{ spin: cubeStore.metaLoading }" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/>
              </svg>
              {{ cubeStore.metaLoading ? 'Cargando...' : 'Refrescar' }}
            </button>
          </div>

          <div v-if="cubeStore.metaLoading" class="loading-row">
            <div class="spinner"></div> Cargando esquema...
          </div>
          <div v-else-if="!cubeStore.connected" class="alert alert-error">
            No hay conexión con CubeJS. Configura la URL y token en Configuración.
          </div>
          <div v-else class="cube-list">
            <div v-for="cube in cubeStore.cubes" :key="cube.name" class="cube-block">
              <div class="cube-name" @click="toggleCubeMeta(cube.name)">
                {{ cube.name }}
                <span class="cube-meta-counts">
                  {{ cube.measures.length }}M · {{ cube.dimensions.length }}D
                </span>
                <svg
                  class="cube-chevron"
                  :class="{ open: openMetaCubes.includes(cube.name) }"
                  width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                >
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
              <div v-if="openMetaCubes.includes(cube.name)" class="cube-members">
                <div class="cube-member-group">
                  <div class="member-group-title">Medidas</div>
                  <div
                    v-for="m in cube.measures"
                    :key="m.name"
                    class="member-chip"
                    @click="insertMeasure(getMemberKey(cube.name, m.name))"
                    :title="m.description"
                  >
                    {{ getMemberKey(cube.name, m.name) }}
                    <span class="member-type">{{ m.type }}</span>
                  </div>
                </div>
                <div class="cube-member-group">
                  <div class="member-group-title">Dimensiones</div>
                  <div
                    v-for="d in cube.dimensions"
                    :key="d.name"
                    class="member-chip member-dim"
                    @click="insertDimension(getMemberKey(cube.name, d.name))"
                    :title="d.description"
                  >
                    {{ getMemberKey(cube.name, d.name) }}
                    <span class="member-type">{{ d.type }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary btn-icon-text" data-tooltip="Formato del widget" @click="$emit('open-layout')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
          </svg>
        </button>
        <div style="flex:1"></div>
        <button class="btn btn-secondary" @click="$emit('close')">Cancelar</button>
        <button class="btn btn-primary" @click="save">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
          </svg>
          Guardar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useCubeStore } from '@/stores/cubejs'
import { useLlmStore } from '@/stores/llm'
import { callLlm } from '@/composables/useLlmCall'
import { useColorPaletteStore } from '@/stores/colorPalettes'
import { useCurrencyStore } from '@/stores/currencies'

const paletteStore = useColorPaletteStore()
const currencyStore = useCurrencyStore()
currencyStore.loadFromBackend()

const props = defineProps({
  widget: { type: Object, required: true }
})

const emit = defineEmits(['close', 'save'])

const cubeStore = useCubeStore()
const llmStore = useLlmStore()

const tabs = [
  { id: 'general', label: 'General' },
  { id: 'data', label: 'Datos (CubeJS)' },
  { id: 'visual', label: 'Visualización' },
  { id: 'cubemeta', label: 'Esquema Cube' }
]

const activeTab = ref('general')
const jsonError = ref(null)

const chartTypes = [
  { value: 'bar',      label: 'Barras',    icon: '📊' },
  { value: 'line',     label: 'Líneas',    icon: '📈' },
  { value: 'pie',      label: 'Pastel',    icon: '🥧' },
  { value: 'gauge',    label: 'Gauge',     icon: '🎯' },
  { value: 'radar',    label: 'Radar',     icon: '🕸️' },
  { value: 'combined', label: 'Combinado', icon: '📉' },
  { value: 'table',    label: 'Tabla',     icon: '🗒️' },
  { value: 'kpi',      label: 'KPI',       icon: '🔢' }
]

const seriesTypes = [
  { value: 'bar',  label: 'Barra',  icon: 'Bar' },
  { value: 'line', label: 'Línea',  icon: 'Lin' },
  { value: 'area', label: 'Área',   icon: 'Are' }
]

// Deep clone widget for editing
const form = ref(JSON.parse(JSON.stringify(props.widget)))

// Ensure position exists with defaults
if (!form.value.position) {
  form.value.position = { x: 0, y: 0, w: 4, h: 3 }
}

// Ensure cubeQuery exists with defaults
if (!form.value.cubeQuery) {
  form.value.cubeQuery = {
    measures: [],
    dimensions: [],
    timeDimension: null,
    filters: [],
    limit: 100
  }
}

// Backfill format/currencyId for existing measures that predate this field
// Using map+replace to guarantee Vue 3 tracks the new properties reactively
form.value.cubeQuery.measures = form.value.cubeQuery.measures.map(m => ({
  ...m,
  format: m.format ?? 'numero',
  currencyId: m.currencyId ?? null
}))

// Ensure pieOptions exists with defaults
if (!form.value.pieOptions) {
  form.value.pieOptions = { showValue: false, showPercent: true, showTotal: false }
}

// Ensure combinedOptions exists with defaults
if (!form.value.combinedOptions) {
  form.value.combinedOptions = { showSecondaryYAxis: false }
}

// Ensure kpiOptions exists with defaults
if (!form.value.kpiOptions) {
  form.value.kpiOptions = { icon: '', accentColor: '', invertTrend: false, showComparison: true, comparisonLabel: 'vs período anterior' }
}

// Ensure gaugeOptions exists with defaults
if (!form.value.gaugeOptions) {
  form.value.gaugeOptions = { variant: 'semicircle', min: 0, max: 100, unit: '%', showZones: true, zones: [{ threshold: 0.3, color: '#f5222d' }, { threshold: 0.7, color: '#faad14' }, { threshold: 1.0, color: '#52c41a' }], arcWidth: 16, showPointer: true, showTicks: true }
}

// colorPalette: null = inherit dashboard, 'none' = no palette, <id> = specific palette

// Computed for time dimension
const timeDimKey = computed({
  get: () => form.value.cubeQuery.timeDimension?.dimension || '',
  set: (v) => {
    if (v) {
      if (!form.value.cubeQuery.timeDimension) {
        form.value.cubeQuery.timeDimension = { dimension: v, granularity: 'month' }
      } else {
        form.value.cubeQuery.timeDimension.dimension = v
      }
    } else {
      form.value.cubeQuery.timeDimension = null
    }
  }
})

const timeDimGranularity = computed({
  get: () => form.value.cubeQuery.timeDimension?.granularity || 'month',
  set: (v) => {
    if (form.value.cubeQuery.timeDimension) {
      form.value.cubeQuery.timeDimension.granularity = v
    }
  }
})

const chartOptionsJson = ref(
  Object.keys(form.value.chartOptions || {}).length
    ? JSON.stringify(form.value.chartOptions, null, 2)
    : ''
)

// ── IA Assist ─────────────────────────────────────────────────
const aiOpen    = ref(false)
const aiPrompt  = ref('')
const aiResult  = ref('')
const aiLoading = ref(false)
const aiError   = ref(null)

function buildAIPrompt() {
  const chartLabels = { bar:'Barras', line:'Líneas', pie:'Pastel', gauge:'Gauge', radar:'Radar', combined:'Combinado' }
  const measures = form.value.cubeQuery.measures.map(m => m.label || m.key).join(', ') || 'ninguna'
  const dimensions = form.value.cubeQuery.dimensions.map(d => d.label || d.key).join(', ') || 'ninguna'
  const current = chartOptionsJson.value.trim() || '{}'

  return `Eres un experto en Apache ECharts v5. Genera opciones de personalización para un gráfico.

CONTEXTO DEL GRÁFICO:
- Tipo: ${chartLabels[form.value.chartType] || form.value.chartType}
- Medidas (series): ${measures}
- Dimensiones (eje X / categorías): ${dimensions}
- Opciones actuales: ${current}

PETICIÓN:
${aiPrompt.value}

REGLAS:
1. Responde SOLO con un bloque de código JSON válido (\`\`\`json ... \`\`\`)
2. El JSON debe ser un objeto con propiedades estándar de ECharts option (tooltip, legend, xAxis, yAxis, series, color, grid, title, etc.)
3. Las opciones se fusionarán con las predeterminadas, no las reemplazarán
4. No incluyas explicaciones fuera del bloque de código
5. Si referencias series, usa arrays para afectar todas las series
6. IMPORTANTE: El JSON debe ser estrictamente válido. No uses saltos de línea literales dentro de las cadenas de texto (usa \\n si es necesario).`
}

async function generateWithAI() {
  if (!aiPrompt.value.trim()) return
  aiLoading.value = true
  aiError.value = null
  aiResult.value = ''

  try {
    const cfg = llmStore.configFor('chartAssist')
    const text = await callLlm({
      provider: cfg.provider,
      modelId:  cfg.modelId,
      apiKey:   cfg.apiKey,
      prompt:   buildAIPrompt(),
      maxTokens: 16384
    })

    // Extract JSON block from response
    let raw = text.trim()
    const match = raw.match(/```(?:json)?\s*([\s\S]*?)(?:```|$)/i)
    if (match) {
      raw = match[1].trim()
    }
    
    const startIdx = raw.indexOf('{')
    const endIdx = raw.lastIndexOf('}')
    if (startIdx !== -1 && endIdx !== -1 && endIdx >= startIdx) {
      raw = raw.substring(startIdx, endIdx + 1)
    }

    // Validate JSON before showing
    JSON.parse(raw)
    aiResult.value = JSON.stringify(JSON.parse(raw), null, 2)
  } catch (e) {
    aiError.value = e.message
  } finally {
    aiLoading.value = false
  }
}

function applyAIResult(replace) {
  if (!aiResult.value) return
  if (replace || !chartOptionsJson.value.trim()) {
    chartOptionsJson.value = aiResult.value
  } else {
    // Deep merge: parse both, merge, stringify
    try {
      const current = JSON.parse(chartOptionsJson.value)
      const incoming = JSON.parse(aiResult.value)
      chartOptionsJson.value = JSON.stringify(deepMerge(current, incoming), null, 2)
    } catch {
      chartOptionsJson.value = aiResult.value
    }
  }
  aiResult.value = ''
  aiOpen.value = false
}

function deepMerge(target, source) {
  const out = { ...target }
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key]) &&
        target[key] && typeof target[key] === 'object' && !Array.isArray(target[key])) {
      out[key] = deepMerge(target[key], source[key])
    } else {
      out[key] = source[key]
    }
  }
  return out
}

watch(chartOptionsJson, (v) => {
  if (!v.trim()) { jsonError.value = null; return }
  try {
    JSON.parse(v)
    jsonError.value = null
  } catch (e) {
    jsonError.value = 'JSON inválido: ' + e.message
  }
})

function addMeasure() {
  form.value.cubeQuery.measures.push({ key: '', label: '', color: '#1890ff', seriesType: 'bar', format: 'numero', currencyId: null })
}
function removeMeasure(idx) {
  form.value.cubeQuery.measures.splice(idx, 1)
}

function addDimension() {
  form.value.cubeQuery.dimensions.push({ key: '', label: '' })
}
function removeDimension(idx) {
  form.value.cubeQuery.dimensions.splice(idx, 1)
}

function addFilter() {
  form.value.cubeQuery.filters.push({ member: '', operator: 'equals', values: [''] })
}
function removeFilter(idx) {
  form.value.cubeQuery.filters.splice(idx, 1)
}

function getMemberKey(cubeName, memberName) {
  return memberName.startsWith(cubeName + '.') ? memberName : `${cubeName}.${memberName}`
}

function insertMeasure(key) {
  const label = key.split('.').pop()
  form.value.cubeQuery.measures.push({ key, label, color: '#1890ff', seriesType: 'bar', format: 'numero', currencyId: null })
  activeTab.value = 'data'
}
function insertDimension(key) {
  const label = key.split('.').pop()
  form.value.cubeQuery.dimensions.push({ key, label })
  activeTab.value = 'data'
}

function save() {
  if (chartOptionsJson.value.trim()) {
    if (jsonError.value) return
    try {
      form.value.chartOptions = JSON.parse(chartOptionsJson.value)
    } catch {
      return
    }
  } else {
    form.value.chartOptions = {}
  }

  emit('save', JSON.parse(JSON.stringify(form.value)))
}

// Cube meta collapsible state (all closed by default)
const openMetaCubes = ref([])

function toggleCubeMeta(name) {
  const idx = openMetaCubes.value.indexOf(name)
  if (idx === -1) openMetaCubes.value.push(name)
  else openMetaCubes.value.splice(idx, 1)
}

async function refreshMeta() {
  openMetaCubes.value = []
  await cubeStore.loadMeta()
}

// Load cube meta if not already loaded
if (cubeStore.token && !cubeStore.meta) {
  cubeStore.loadMeta()
}
</script>

<style scoped>
.config-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 4px;
}

.chart-type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border: 2px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  background: #fff;
}
.chart-type-card:hover { border-color: var(--primary); background: var(--primary-light); }
.chart-type-card.selected { border-color: var(--primary); background: var(--primary-light); }

.ct-icon { font-size: 24px; }
.ct-label { font-size: 13px; font-weight: 500; color: var(--text); }

.measure-list { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
.measure-row { display: flex; align-items: center; gap: 8px; }
.filter-row { display: flex; align-items: center; gap: 8px; }

.color-picker {
  width: 36px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  padding: 2px;
  flex-shrink: 0;
}

.json-editor {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  min-height: 200px;
}

/* Cube meta */
.cube-meta-tab { display: flex; flex-direction: column; gap: 12px; }
.cube-meta-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px;
}
.cube-meta-count { font-size: 12px; color: var(--text-secondary); }
.cube-list { display: flex; flex-direction: column; gap: 6px; }
.loading-row { display: flex; align-items: center; gap: 12px; color: var(--text-secondary); }
.cube-block { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.cube-name {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 12px;
  background: var(--bg);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  user-select: none;
}
.cube-name:hover { background: var(--primary-light); }
.cube-meta-counts { font-size: 11px; font-weight: 400; color: var(--text-secondary); }
.cube-chevron {
  margin-left: auto; flex-shrink: 0;
  transition: transform 0.2s; color: var(--text-secondary);
}
.cube-chevron.open { transform: rotate(180deg); }
.cube-members { padding: 12px; display: flex; flex-direction: column; gap: 12px; border-top: 1px solid var(--border); }
.cube-member-group { display: flex; flex-direction: column; gap: 6px; }
.member-group-title { font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.member-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  background: var(--primary-light);
  color: var(--primary);
  font-size: 12px;
  cursor: pointer;
  width: fit-content;
  transition: all 0.15s;
}
.member-chip:hover { background: var(--primary); color: #fff; }
.member-dim { background: #f6ffed; color: var(--success); }
.member-dim:hover { background: var(--success); color: #fff; }
.member-type { font-size: 10px; opacity: 0.7; }

/* ── IA Assist ─────────────────────────────────────── */
.visual-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.visual-label-row .form-label { margin: 0; }

.btn-ai-assist {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 20px;
  border: 1.5px solid #722ed1;
  background: #fff;
  color: #722ed1;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.btn-ai-assist:hover,
.btn-ai-assist.active { background: #722ed1; color: #fff; }

.ai-panel {
  border: 1.5px solid #d3adf7;
  border-radius: 10px;
  background: #fdf5ff;
  overflow: hidden;
  margin-bottom: 10px;
}
.ai-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #722ed1;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}
.ai-model-badge {
  margin-left: auto;
  font-size: 11px;
  font-weight: 500;
  background: rgba(255,255,255,0.2);
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.ai-panel-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-context-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.ai-chip {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 10px;
}
.ai-chip-type    { background: #722ed1; color: #fff; }
.ai-chip-measure { background: #e6f4ff; color: #1890ff; border: 1px solid #91caff; }
.ai-chip-dim     { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }

.ai-result {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 0.8s linear infinite; }

/* Color palette selector */
.palette-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  margin-top: 8px;
}
.palette-card {
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  background: #fff;
}
.palette-card:hover { border-color: var(--primary); }
.palette-card.selected { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light, #e6f4ff); }
.palette-swatches {
  display: flex;
  gap: 3px;
  margin-bottom: 6px;
}
.palette-swatch {
  flex: 1;
  height: 14px;
  border-radius: 3px;
}
.palette-label {
  font-size: 12px;
  color: var(--text-secondary, #666);
  display: block;
  text-align: center;
}
.palette-card.selected .palette-label { color: var(--primary); font-weight: 600; }
.palette-card--special .palette-swatches { justify-content: center; align-items: center; height: 14px; }
.palette-swatches--inherit { color: var(--text-secondary); }
.palette-card--special.selected .palette-swatches--inherit { color: var(--primary); }

/* Pie options */
.pie-options-group { border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background: #fafafa; }
.pie-options-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.pie-opt-toggle {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px;
  border: 1.5px solid var(--border); background: #fff;
  font-size: 12px; font-weight: 500; color: var(--text-secondary);
  cursor: pointer; transition: all 0.15s; user-select: none;
}
.pie-opt-toggle:hover { border-color: var(--primary); color: var(--primary); }
.pie-opt-toggle.active { border-color: var(--primary); background: var(--primary-light); color: var(--primary); font-weight: 600; }
.pie-opt-icon { font-size: 11px; width: 12px; text-align: center; }

/* KPI options */
.kpi-options-group { border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background: #fafafa; }
.kpi-options-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.kpi-opt-field { display: flex; flex-direction: column; gap: 4px; }
.kpi-opt-label { font-size: 12px; font-weight: 500; color: var(--text-secondary); }
.kpi-opt-toggles { display: flex; gap: 8px; flex-wrap: wrap; }

.measure-format-select {
  flex: 0 0 110px;
}

.measure-currency-select {
  flex: 0 0 100px;
}

.series-type-toggle {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}
.st-btn {
  min-width: 32px;
  height: 34px;
  padding: 0 6px;
  border: none;
  background: #fff;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all 0.15s;
  border-right: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
}
.st-btn:last-child { border-right: none; }
.st-btn:hover { background: var(--bg); color: var(--primary); }
.st-btn.active { background: var(--primary); color: #fff; }
</style>
