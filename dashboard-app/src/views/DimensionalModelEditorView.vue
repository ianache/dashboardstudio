<template>
  <div class="editor-view">
    <!-- Toolbar -->
    <div class="editor-toolbar card">
      <button class="btn btn-secondary btn-sm" @click="router.push('/models')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
        </svg>
        Volver
      </button>

      <div class="toolbar-title">
        <span v-if="!editingTitle" class="title-text" @dblclick="startEditTitle">
          {{ model?.name }}
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

      <div class="toolbar-actions">
        <!-- CubeJS / DDL / Import / Export -->
        <input ref="importInput" type="file" accept=".yaml,.yml" style="display:none" @change="handleImport" />
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Exportar Diagrama (.png)" @click="handleExportPNG">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </button>
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Exportar schema CubeJS (.js)" @click="handleExportCubeJS">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
        </button>
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Generar DDL/SQL" @click="handleGenerateDDL">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
        </button>
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Importar YAML" @click="importInput.click()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </button>
        <button class="btn btn-secondary btn-sm btn-icon-only" data-tooltip="Exportar YAML" @click="handleExport">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
        </button>

        <button class="btn-ai-assist" @click="aiAssistOpen = true">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
          </svg>
          IA Assist
        </button>

        <div class="toolbar-sep"></div>

        <button class="btn btn-secondary btn-sm" @click="addNode('fact')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Hecho
        </button>
        <button class="btn btn-secondary btn-sm" @click="addNode('dimension')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Dimensión
        </button>
        <button
          v-if="!model?.isGlobal && modelStore.globalModel"
          class="btn btn-secondary btn-sm"
          data-tooltip="Añadir dimensión del modelo Global"
          @click="showGlobalDimModal = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
          + Dim. Global
        </button>
      </div>
    </div>

    <!-- Canvas + Properties panel -->
    <div class="editor-body">
      <!-- Canvas -->
      <div
        ref="canvasEl"
        class="model-canvas"
        :class="{ 'dragging-field': !!dragField }"
        @click="onCanvasClick"
        @mousemove="onNodeDragMove"
      >
        <!-- SVG overlay for relationships + guide line -->
        <svg class="canvas-svg" :width="canvasSize.w" :height="canvasSize.h">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
            </marker>
            <marker id="arrowhead-key" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#52c41a"/>
            </marker>
          </defs>

          <!-- Relationships -->
          <g v-for="rel in model?.relationships" :key="rel.id">
            <line
              :x1="nodeCenter(rel.fromNodeId).x"
              :y1="nodeCenter(rel.fromNodeId).y"
              :x2="nodeCenter(rel.toNodeId).x"
              :y2="nodeCenter(rel.toNodeId).y"
              :stroke="selectedRel?.id === rel.id ? 'var(--primary)' : '#888'"
              stroke-width="2"
              marker-end="url(#arrowhead)"
              class="rel-line"
              @click.stop="selectRelationship(rel)"
            />
            <text
              :x="relMidpoint(rel).x"
              :y="relMidpoint(rel).y - 6"
              text-anchor="middle"
              class="rel-label"
              :fill="selectedRel?.id === rel.id ? 'var(--primary)' : '#555'"
              @click.stop="selectRelationship(rel)"
            >{{ rel.cardinality }}</text>
          </g>

          <!-- Field drag guide line -->
          <line
            v-if="dragField"
            :x1="dragField.startPos.x"
            :y1="dragField.startPos.y"
            :x2="mousePos.x"
            :y2="mousePos.y"
            stroke="#52c41a"
            stroke-width="2"
            stroke-dasharray="6 4"
            marker-end="url(#arrowhead-key)"
            pointer-events="none"
          />
        </svg>

        <!-- Nodes -->
        <div
          v-for="node in resolvedNodes"
          :key="node.id"
          class="model-node"
          :class="[
            node.type,
            { selected: selectedNode?.id === node.id },
            { 'drop-target': dragField && node.type === 'fact' && node.id === dropTargetId },
            { 'global-ref': node.globalRef }
          ]"
          :style="{ left: node.x + 'px', top: node.y + 'px' }"
          @click.stop="onNodeClick(node)"
          @mousedown.stop="startDrag(node, $event)"
        >
          <div class="node-header" :class="node.type">
            <span class="node-badge">{{ node.type === 'fact' ? 'HECHO' : 'DIM' }}</span>
            <span class="node-name">{{ node.name }}</span>
            <svg v-if="node.globalRef" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity:.7;flex-shrink:0">
              <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
          </div>
          <div class="node-fields">
            <div
              v-for="f in node.fields"
              :key="f.id"
              class="node-field"
              :class="{ 'is-key': f.isKey, 'is-fk': f.isFk }"
            >
              <!-- Drag handle: only on key field of dimension nodes -->
              <span
                v-if="node.type === 'dimension' && f.isKey"
                class="key-drag-handle"
                title="Arrastrar para vincular con tabla de hechos"
                @mousedown.stop="startFieldDrag(node, f, $event)"
              >⠿</span>
              <span v-else class="field-icon-placeholder"></span>

              <span class="field-icon">
                <span v-if="f.isKey" class="key-icon" title="Llave primaria">🔑</span>
                <span v-else-if="f.isFk" class="fk-icon" title="Llave foránea">🔗</span>
                <span v-else>{{ fieldIcon(node.type, f.dataType) }}</span>
              </span>
              <span class="field-name">{{ f.name }}</span>
              <span class="field-type">{{ dtStore.getById(f.dataType)?.name ?? f.dataType }}</span>
            </div>

            <!-- Hint for dimensions without key -->
            <div v-if="node.type === 'dimension' && node.fields.length && !node.fields.some(f => f.isKey)" class="node-warn">
              ⚠ Sin llave definida
            </div>
            <div v-if="!node.fields.length" class="node-empty">Sin campos</div>
          </div>
        </div>

        <!-- Empty canvas hint -->
        <div v-if="!model?.nodes.length" class="canvas-hint">
          <p>Usa los botones de la barra para añadir tablas de <strong>Hecho</strong> o <strong>Dimensión</strong></p>
        </div>

        <!-- Field drag floating label -->
        <div
          v-if="dragField"
          class="drag-pill"
          :style="{ left: mousePos.x + 16 + 'px', top: mousePos.y - 12 + 'px' }"
        >
          🔑 {{ dragField.fieldName }}
          <span v-if="dropTargetId" class="drag-pill-hint">→ soltar para vincular</span>
        </div>
      </div>

      <!-- Properties panel -->
      <div v-if="selectedNode || selectedRel" class="props-panel card">
        <!-- Node properties -->
        <template v-if="selectedNode">
          <div class="props-header">
            <span class="props-type-badge" :class="selectedNode.type">
              {{ selectedNode.type === 'fact' ? 'Tabla de Hecho' : 'Dimensión' }}
              <span v-if="selectedNode.globalRef" class="global-ref-tag">Global</span>
            </span>
            <button class="btn-icon" data-tooltip="Exportar cubo CubeJS" @click="exportSingleCube(resolveNode(selectedNode))">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
            </button>
            <button class="btn-icon" @click="selectedNode = null; selectedRel = null">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- Read-only panel for global-ref nodes -->
          <div v-if="selectedNode.globalRef" class="props-body global-ref-body">
            <div class="global-ref-notice">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
              Dimensión del modelo Global — solo lectura
            </div>
            <div class="props-section-title" style="margin-top:8px">Campos</div>
            <div class="global-ref-fields">
              <div v-for="f in resolveNode(selectedNode).fields" :key="f.id" class="global-ref-field">
                <span class="field-icon">
                  <span v-if="f.isKey">🔑</span>
                  <span v-else-if="f.isFk">🔗</span>
                  <span v-else>{{ fieldIcon('dimension', f.dataType) }}</span>
                </span>
                <span class="field-name">{{ f.name }}</span>
                <span class="field-type">{{ dtStore.getById(f.dataType)?.name ?? f.dataType }}</span>
              </div>
              <div v-if="!resolveNode(selectedNode).fields.length" class="node-empty">Sin campos</div>
            </div>
            <div class="props-divider"></div>
            <button class="btn btn-sm btn-danger-outline" @click="deleteNodeConfirm">
              Quitar del modelo
            </button>
          </div>

          <!-- Editable panel for local nodes -->
          <div v-else class="props-body">
            <div class="form-group">
              <label class="form-label">Nombre</label>
              <input
                :value="selectedNode.name"
                type="text"
                class="form-input"
                @change="updateNodeName($event.target.value)"
              />
            </div>

            <div class="props-section-title">
              Campos
              <button
                class="btn-icon desc-toggle"
                :class="{ active: showFieldDesc }"
                :title="showFieldDesc ? 'Ocultar descripciones' : 'Mostrar descripciones'"
                @click="showFieldDesc = !showFieldDesc"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="8" y1="6" x2="21" y2="6"/>
                  <line x1="8" y1="12" x2="21" y2="12"/>
                  <line x1="8" y1="18" x2="21" y2="18"/>
                  <line x1="3" y1="6" x2="3.01" y2="6"/>
                  <line x1="3" y1="12" x2="3.01" y2="12"/>
                  <line x1="3" y1="18" x2="3.01" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="fields-list">
              <div v-for="f in selectedNode.fields" :key="f.id" class="field-item">
                <!-- Row 1: key toggle · name · type · delete -->
                <div class="field-row1">
                  <button
                    class="key-toggle"
                    :class="{ active: f.isKey }"
                    :title="f.isKey ? 'Llave primaria' : 'Marcar como llave'"
                    @click="setKeyField(f.id)"
                  >🔑</button>
                  <input
                    :value="f.name"
                    type="text"
                    class="form-input field-name-input"
                    placeholder="Nombre"
                    @change="updateField(f.id, 'name', $event.target.value)"
                  />
                  <select
                    :value="f.dataType"
                    class="form-input form-select field-type-select"
                    @change="updateField(f.id, 'dataType', $event.target.value)"
                  >
                    <option v-for="dt in dtStore.allTypes" :key="dt.id" :value="dt.id">
                      {{ dt.name }}
                    </option>
                  </select>
                  <button class="btn-icon field-del-btn" @click="deleteField(f.id)">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
                <!-- Row 2: description (toggled) -->
                <div v-show="showFieldDesc" class="field-row2">
                  <input
                    :value="f.description"
                    type="text"
                    class="form-input field-desc-input"
                    placeholder="Descripción (opcional)"
                    @change="updateField(f.id, 'description', $event.target.value)"
                  />
                </div>
              </div>
            </div>

            <div v-if="selectedNode.type === 'dimension' && !selectedNode.fields.some(f => f.isKey)" class="props-warn">
              ⚠ Marca un campo como llave (🔑) para poder arrastrar relaciones
            </div>

            <button class="btn btn-secondary btn-sm add-field-btn" @click="addField">
              + Añadir campo
            </button>

            <div class="props-divider"></div>
            <button class="btn btn-sm btn-danger-outline" @click="deleteNodeConfirm">
              Eliminar tabla
            </button>
          </div><!-- end v-else editable props-body -->
        </template>

        <!-- Relationship properties -->
        <template v-if="selectedRel">
          <div class="props-header">
            <span class="props-type-badge rel">Relación</span>
            <button class="btn-icon" @click="selectedRel = null">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="props-body">
            <div class="rel-nodes-info">
              <span class="rel-node-tag">{{ nodeName(selectedRel.fromNodeId) }}</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
              <span class="rel-node-tag">{{ nodeName(selectedRel.toNodeId) }}</span>
            </div>

            <div class="form-group">
              <label class="form-label">Cardinalidad</label>
              <select
                :value="selectedRel.cardinality"
                class="form-input form-select"
                @change="updateRelCardinality($event.target.value)"
              >
                <option value="1:1">1:1 — Uno a uno</option>
                <option value="1:N">1:N — Uno a muchos</option>
                <option value="N:N">N:N — Muchos a muchos</option>
              </select>
            </div>

            <div class="props-divider"></div>
            <button class="btn btn-sm btn-danger-outline" @click="deleteRelationship">
              Eliminar relación
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Modal: AI Assist -->
    <div v-if="aiAssistOpen" class="modal-overlay" @click.self="aiAssistOpen = false">
      <div class="modal card ai-assist-modal">
        <div class="modal-header ai-assist-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
          </svg>
          <span>IA Assist — Diseñador de Tablas</span>
          <span v-if="llmStore.isConfigured" class="ai-model-label">
            {{ llmStore.configFor('modelAssist').providerLabel }} · {{ llmStore.configFor('modelAssist').modelLabel }}
          </span>
          <button class="btn-icon" style="margin-left:auto" @click="aiAssistOpen = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body ai-assist-body">
          <!-- No LLM configured -->
          <div v-if="!llmStore.isConfigured" class="alert alert-error">
            Sin clave API configurada.
            <router-link to="/settings" @click="aiAssistOpen = false" style="color:inherit;font-weight:600;margin-left:4px">
              Ir a Configuración →
            </router-link>
          </div>

          <!-- Context chips -->
          <div class="ai-context-row">
            <span class="ai-ctx-label">Modelo:</span>
            <span class="ai-chip ai-chip-model">{{ model?.name }}</span>
            <template v-if="model?.nodes.length">
              <span class="ai-ctx-label" style="margin-left:8px">Tablas existentes:</span>
              <span v-for="n in model.nodes.slice(0, 6)" :key="n.id"
                    class="ai-chip" :class="n.type === 'fact' ? 'ai-chip-fact' : 'ai-chip-dim'">
                {{ n.name }}
              </span>
              <span v-if="model.nodes.length > 6" class="ai-chip-more">+{{ model.nodes.length - 6 }}</span>
            </template>
          </div>

          <!-- Prompt -->
          <div class="form-group" style="margin:0">
            <label class="form-label">¿Qué tablas necesitas diseñar?</label>
            <textarea
              v-model="aiAssistPrompt"
              class="form-input"
              rows="4"
              :disabled="aiAssistLoading"
              placeholder="Ej: Necesito una tabla de hechos de Ventas con campos de monto, cantidad y descuento, y dimensiones de Cliente, Producto y Tiempo con sus campos principales."
              @keydown.ctrl.enter="runAIAssist"
            ></textarea>
            <span class="form-hint">Ctrl+Enter para generar</span>
          </div>

          <button
            class="btn btn-primary"
            style="align-self:flex-start"
            :disabled="!llmStore.isConfigured || !aiAssistPrompt.trim() || aiAssistLoading"
            @click="runAIAssist"
          >
            <svg v-if="aiAssistLoading" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
            </svg>
            {{ aiAssistLoading ? 'Generando...' : 'Generar tablas' }}
          </button>

          <div v-if="aiAssistError" class="alert alert-error">
            <div style="font-weight:600;margin-bottom:6px">{{ aiAssistError }}</div>
            <details v-if="aiRawJson" style="font-size:12px;background:rgba(0,0,0,0.05);padding:8px;border-radius:6px;cursor:pointer">
              <summary style="outline:none;font-weight:600">Ver respuesta original (Crudo)</summary>
              <pre style="margin-top:8px;white-space:pre-wrap;word-wrap:break-word">{{ aiRawJson }}</pre>
            </details>
          </div>

          <!-- Result preview -->
          <div v-if="aiAssistResult" class="ai-result-section">
            <div class="ai-result-title">
              <span>{{ aiAssistResult.length }} tabla(s) generada(s) — selecciona las que quieres añadir</span>
              <div style="display:flex;gap:6px">
                <button class="btn btn-secondary btn-sm" :class="{ 'btn-primary': aiViewMode === 'visual' }" @click="aiViewMode = 'visual'">Visor Visual</button>
                <button class="btn btn-secondary btn-sm" :class="{ 'btn-primary': aiViewMode === 'json' }" @click="aiViewMode = 'json'">JSON</button>
              </div>
            </div>

            <!-- JSON Viewer -->
            <div v-if="aiViewMode === 'json'" style="margin-top:12px">
              <div style="display:flex; justify-content:flex-end; margin-bottom:8px">
                <button class="btn btn-secondary btn-sm" @click="downloadAIAssistJSON">
                  ⬇ Descargar Artifact (.json)
                </button>
              </div>
              <textarea class="form-input json-editor" readonly :value="aiRawJson" rows="12"></textarea>
            </div>

            <!-- Visual View -->
            <div v-show="aiViewMode === 'visual'">
              <div style="display:flex;gap:6px;margin:12px 0 8px 0">
                <button class="btn btn-secondary btn-sm" @click="aiSelectAll(true)">Marcar Todas</button>
                <button class="btn btn-secondary btn-sm" @click="aiSelectAll(false)">Ninguna</button>
              </div>
              <div class="ai-tables-list">
              <div
                v-for="(table, idx) in aiAssistResult"
                :key="idx"
                class="ai-table-card"
                :class="{ selected: aiSelectedTables.includes(idx), fact: table.type === 'fact', dim: table.type === 'dimension' }"
                @click="aiToggleTable(idx)"
              >
                <div class="ai-table-header">
                  <input type="checkbox" :checked="aiSelectedTables.includes(idx)" @click.stop="aiToggleTable(idx)" />
                  <span class="ai-table-badge" :class="table.type">
                    {{ table.type === 'fact' ? 'HECHO' : 'DIM' }}
                  </span>
                  <span class="ai-table-name">{{ table.name }}</span>
                  <span class="ai-table-count">{{ table.fields.length }} campos</span>
                </div>
                <div class="ai-table-fields">
                  <span v-for="f in table.fields" :key="f.name" class="ai-field-chip" :class="{ 'is-key': f.isKey }">
                    <span v-if="f.isKey">🔑</span>{{ f.name }}
                    <span class="ai-field-type">{{ f.dataTypeLabel }}</span>
                  </span>
                </div>
                <div v-if="table.description" class="ai-table-desc">{{ table.description }}</div>
              </div>
            </div>
            </div><!-- /visual view -->
          </div>
        </div>

        <div v-if="aiAssistResult" class="modal-footer">
          <button class="btn btn-secondary" @click="aiAssistOpen = false">Cancelar</button>
          <button
            class="btn btn-primary"
            :disabled="!aiSelectedTables.length"
            @click="applyAITables"
          >
            Añadir {{ aiSelectedTables.length }} tabla(s) al canvas
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Add Global Dimensions -->
    <div v-if="showGlobalDimModal" class="modal-overlay" @click.self="showGlobalDimModal = false">
      <div class="modal card">
        <div class="modal-header">
          <h3>Añadir Dimensiones Globales</h3>
          <button class="btn-icon" @click="showGlobalDimModal = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p v-if="!availableGlobalDims.length" class="modal-empty">
            No hay dimensiones globales disponibles para añadir.
          </p>
          <div v-else class="global-dim-list">
            <label
              v-for="n in availableGlobalDims"
              :key="n.id"
              class="global-dim-option"
              :class="{ selected: selectedGlobalDims.includes(n.id) }"
            >
              <input
                type="checkbox"
                :value="n.id"
                v-model="selectedGlobalDims"
                style="display:none"
              />
              <span class="global-dim-icon">🌐</span>
              <span class="global-dim-name">{{ n.name }}</span>
              <span class="global-dim-fields">{{ n.fields.length }} campos</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showGlobalDimModal = false">Cancelar</button>
          <button
            class="btn btn-primary"
            :disabled="!selectedGlobalDims.length"
            @click="addSelectedGlobalDims"
          >Añadir ({{ selectedGlobalDims.length }})</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDimensionalModelStore } from '@/stores/dimensionalModel'
import { useDataTypeStore } from '@/stores/dataTypes'
import { useUIStore } from '@/stores/ui'
import { useLlmStore } from '@/stores/llm'
import { callLlm } from '@/composables/useLlmCall'
import yaml from 'js-yaml'
import JSZip from 'jszip'
import html2canvas from 'html2canvas'

const router = useRouter()
const route = useRoute()
const modelStore = useDimensionalModelStore()
const dtStore = useDataTypeStore()
const uiStore = useUIStore()

const llmStore = useLlmStore()

const modelId = route.params.id
const model = computed(() => modelStore.getModel(modelId))

// ── Title editing ────────────────────────────────────────────
const editingTitle = ref(false)
const editTitleValue = ref('')
const titleInput = ref(null)

function startEditTitle() {
  editTitleValue.value = model.value?.name || ''
  editingTitle.value = true
  nextTick(() => titleInput.value?.focus())
}
function saveTitle() {
  if (editTitleValue.value.trim()) modelStore.updateModel(modelId, { name: editTitleValue.value.trim() })
  editingTitle.value = false
}

// ── Import / Export ──────────────────────────────────────────
const importInput = ref(null)

async function handleExportPNG() {
  if (!canvasEl.value) return
  
  const el = canvasEl.value
  
  // Guardamos el scroll original y forzamos a 0,0 para que no recorte la imagen
  const oldScrollX = el.scrollLeft
  const oldScrollY = el.scrollTop
  const oldOverflow = el.style.overflow

  try {
    el.scrollLeft = 0
    el.scrollTop = 0
    el.style.overflow = 'visible'

    const canvas = await html2canvas(el, {
      backgroundColor: '#ffffff',
      scale: 2, // Alta resolución
      width: el.scrollWidth,
      height: el.scrollHeight,
      windowWidth: el.scrollWidth,
      windowHeight: el.scrollHeight
    })
    
    const dataUrl = canvas.toDataURL('image/png')
    const fileName = (model.value?.name || 'modelo')
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '-') + '.png'
      
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = fileName
    a.click()
  } catch (err) {
    alert('Error al generar la imagen PNG: ' + err.message)
  } finally {
    // Restaurar los valores visuales en el DOM
    el.style.overflow = oldOverflow
    el.scrollLeft = oldScrollX
    el.scrollTop = oldScrollY
  }
}

function handleExport() {
  if (!model.value) return
  const doc = {
    name: model.value.name,
    description: model.value.description,
    nodes: model.value.nodes.map(n => ({
      id: n.id, type: n.type, name: n.name, x: n.x, y: n.y,
      fields: n.fields.map(f => ({
        id: f.id, name: f.name, description: f.description,
        dataType: f.dataType, isKey: !!f.isKey, isFk: !!f.isFk
      }))
    })),
    relationships: model.value.relationships.map(r => ({
      id: r.id, fromNodeId: r.fromNodeId, toNodeId: r.toNodeId, cardinality: r.cardinality
    }))
  }
  const content = yaml.dump(doc, { indent: 2, lineWidth: 120 })
  const slug = model.value.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'modelo'
  const blob = new Blob([content], { type: 'text/yaml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${slug}.yaml`; a.click()
  URL.revokeObjectURL(url)
}

function handleImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const doc = yaml.load(ev.target.result)
      if (!doc || typeof doc !== 'object') throw new Error('Formato inválido')
      modelStore.updateModel(modelId, {
        name: doc.name || model.value.name,
        description: doc.description ?? model.value.description
      })
      const m = modelStore.getModel(modelId)
      if (!m) return
      m.nodes = Array.isArray(doc.nodes) ? doc.nodes : []
      m.relationships = Array.isArray(doc.relationships) ? doc.relationships : []
      modelStore.persist()
      selectedNode.value = null; selectedRel.value = null
    } catch (err) {
      alert(`Error al importar: ${err.message}`)
    } finally {
      e.target.value = ''
    }
  }
  reader.readAsText(file)
}

// ── DDL Generation ───────────────────────────────────────────
function toSqlName(s) {
  return s.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
}

// Normalize a raw type string to a valid uppercase PostgreSQL type
function normalizePgType(raw) {
  if (!raw) return 'VARCHAR(255)'
  const map = {
    'integer': 'INTEGER', 'int': 'INTEGER', 'int4': 'INTEGER',
    'bigint': 'BIGINT', 'int8': 'BIGINT', 'smallint': 'SMALLINT', 'int2': 'SMALLINT',
    'serial': 'SERIAL', 'bigserial': 'BIGSERIAL',
    'numeric': 'NUMERIC', 'decimal': 'DECIMAL', 'money': 'MONEY',
    'real': 'REAL', 'double precision': 'DOUBLE PRECISION', 'float8': 'DOUBLE PRECISION',
    'varchar': 'VARCHAR(255)', 'character varying': 'VARCHAR(255)',
    'char': 'CHAR(1)', 'character': 'CHAR(1)', 'text': 'TEXT',
    'boolean': 'BOOLEAN', 'bool': 'BOOLEAN',
    'date': 'DATE', 'time': 'TIME',
    'timestamp': 'TIMESTAMP', 'timestamp without time zone': 'TIMESTAMP',
    'timestamptz': 'TIMESTAMPTZ', 'timestamp with time zone': 'TIMESTAMPTZ',
    'uuid': 'UUID', 'jsonb': 'JSONB', 'json': 'JSON', 'bytea': 'BYTEA',
  }
  return map[raw.toLowerCase()] ?? raw.toUpperCase()
}

// Resolve PostgreSQL column type from a model field.
// SERIAL/BIGSERIAL are auto-increment sequences — invalid for FK columns.
function pgTypeForCol(field) {
  const dt = dtStore.getById(field.dataType)
  if (dt) {
    if (field.isFk) {
      if (dt.baseType === 'SERIAL')    return 'INTEGER'
      if (dt.baseType === 'BIGSERIAL') return 'BIGINT'
    }
    return dtStore.sqlOf(field.dataType)
  }
  // Fallback for legacy raw-string dataType values
  return normalizePgType(field.dataType)
}

function handleGenerateDDL() {
  if (!model.value) return
  const m = model.value
  const lines = []

  // Header
  lines.push(`-- ============================================================`)
  lines.push(`-- Modelo Dimensional: ${m.name}`)
  if (m.description) lines.push(`-- ${m.description}`)
  lines.push(`-- Generado: ${new Date().toISOString()}`)
  lines.push(`-- ============================================================`)
  lines.push('')

  // Use resolved nodes so global-ref nodes show their actual fields
  const allNodes = resolvedNodes.value

  // Separate dimensions and facts
  const dims  = allNodes.filter(n => n.type === 'dimension')
  const facts = allNodes.filter(n => n.type === 'fact')

  // Map nodeId → sql table name (needed for FK references)
  const tableOf = {}
  allNodes.forEach(n => { tableOf[n.id] = toSqlName(n.name) })

  // Helper: build relationship lookup dim→fact
  // rel.fromNodeId = dim, rel.toNodeId = fact (as created by drag-drop)
  const relsByDim = {}
  m.relationships.forEach(r => {
    const fromNode = allNodes.find(n => n.id === r.fromNodeId)
    if (fromNode?.type === 'dimension') {
      if (!relsByDim[r.fromNodeId]) relsByDim[r.fromNodeId] = []
      relsByDim[r.fromNodeId].push(r)
    }
  })

  // 1. DIMENSION tables
  if (dims.length) {
    lines.push('-- ------------------------------------------------------------')
    lines.push('-- TABLAS DE DIMENSIONES')
    lines.push('-- ------------------------------------------------------------')
    lines.push('')
  }

  dims.forEach(node => {
    const tbl = tableOf[node.id]
    lines.push(`CREATE TABLE ${tbl} (`)

    // Each entry: { def: 'sql definition', cmt: '  -- comment or empty' }
    const colDefs = node.fields.map(f => {
      const col = toSqlName(f.name)
      const type = pgTypeForCol(f)
      const pk  = f.isKey ? ' PRIMARY KEY' : ''
      return {
        def: `    ${col.padEnd(30)} ${(type + pk).trimEnd()}`,
        cmt: f.description ? `  -- ${f.description}` : ''
      }
    })

    if (!colDefs.length) {
      lines.push('    -- (sin campos definidos)')
    } else {
      // Comma goes between definition and comment so it never lands inside the comment
      const formatted = colDefs.map((item, i) =>
        item.def + (i < colDefs.length - 1 ? ',' : '') + item.cmt
      )
      lines.push(formatted.join('\n'))
    }
    lines.push(');')
    lines.push('')
  })

  // 2. FACT tables
  if (facts.length) {
    lines.push('-- ------------------------------------------------------------')
    lines.push('-- TABLAS DE HECHOS')
    lines.push('-- ------------------------------------------------------------')
    lines.push('')
  }

  facts.forEach(node => {
    const tbl = tableOf[node.id]
    lines.push(`CREATE TABLE ${tbl} (`)

    // FK CONSTRAINT clauses collected separately (no inline comment)
    const fkConstraints = []

    const colDefs = node.fields.map(f => {
      const col  = toSqlName(f.name)
      const type = pgTypeForCol(f)

      // Resolve REFERENCES constraint from FK description
      if (f.isFk && f.description) {
        // description format: "FK → DimName.fieldName"
        const match = f.description.match(/FK → (.+)\.(.+)/)
        if (match) {
          const dimNode = allNodes.find(n => n.name === match[1] && n.type === 'dimension')
          if (dimNode) {
            const refTbl = tableOf[dimNode.id]
            const refCol = toSqlName(match[2])
            fkConstraints.push(
              `    CONSTRAINT fk_${tbl}_${col} FOREIGN KEY (${col}) REFERENCES ${refTbl}(${refCol})`
            )
          }
        }
      }

      const pk = f.isKey ? ' PRIMARY KEY' : ''
      return {
        def: `    ${col.padEnd(30)} ${(type + pk).trimEnd()}`,
        cmt: f.description && !f.isKey ? `  -- ${f.description}` : ''
      }
    })

    // Merge columns + FK constraints; constraints have no inline comment
    const allDefs = [
      ...colDefs,
      ...fkConstraints.map(sql => ({ def: sql, cmt: '' }))
    ]

    if (!allDefs.length) {
      lines.push('    -- (sin campos definidos)')
    } else {
      // Comma goes between definition and comment so it never lands inside the comment
      const formatted = allDefs.map((item, i) =>
        item.def + (i < allDefs.length - 1 ? ',' : '') + item.cmt
      )
      lines.push(formatted.join('\n'))
    }
    lines.push(');')
    lines.push('')
  })

  // 3. RELATIONSHIP comments (for N:N or non-FK rels)
  const nonFkRels = m.relationships.filter(r => {
    const from = allNodes.find(n => n.id === r.fromNodeId)
    return r.cardinality === 'N:N' || !from || from.type !== 'dimension'
  })
  if (nonFkRels.length) {
    lines.push('-- ------------------------------------------------------------')
    lines.push('-- RELACIONES ADICIONALES')
    lines.push('-- ------------------------------------------------------------')
    nonFkRels.forEach(r => {
      lines.push(`-- ${tableOf[r.fromNodeId] || r.fromNodeId} [${r.cardinality}] ${tableOf[r.toNodeId] || r.toNodeId}`)
    })
    lines.push('')
  }

  const content = lines.join('\n')
  const slug = m.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'modelo'
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${slug}.ddl`; a.click()
  URL.revokeObjectURL(url)
}

// ── CubeJS Export ────────────────────────────────────────────
function toPascalCase(s) {
  return s.trim().split(/[\s_]+/).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('')
}
function toCamelCase(s) {
  const p = toPascalCase(s); return p.charAt(0).toLowerCase() + p.slice(1)
}

// Strip leading table prefix (dim_, fct_, fact_, stg_, dbo_, …) then PascalCase
function cubeNameFrom(node) {
  const tbl = toSqlName(node.name)
  const stripped = tbl.replace(/^[a-z]{2,6}_/, '')
  return stripped.split('_').filter(Boolean)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('')
}

function cubeJsDimType(field) {
  const dt = dtStore.getById(field.dataType)
  const base = dt?.baseType ?? normalizePgType(field.dataType)
  if (['DATE', 'TIME', 'TIMESTAMP', 'TIMESTAMPTZ'].includes(base)) return 'time'
  if (base === 'BOOLEAN') return 'boolean'
  if (['VARCHAR', 'CHAR', 'TEXT', 'UUID', 'JSONB', 'JSON', 'BYTEA'].some(t => base.startsWith(t))) return 'string'
  return 'number'
}

function cubeJsMeasureType(field) {
  const dt = dtStore.getById(field.dataType)
  const base = dt?.baseType ?? normalizePgType(field.dataType)
  return ['INTEGER', 'BIGINT', 'SMALLINT', 'SERIAL', 'BIGSERIAL',
          'NUMERIC', 'DECIMAL', 'REAL', 'DOUBLE PRECISION', 'MONEY'].includes(base)
    ? 'sum' : 'count'
}

// Build the JS content for a single node (dimension or fact cube)
// rNodes: resolved nodes array (so global-ref dims are found with real names/fields)
function buildCubeJS(node, m, tableOf, cubeOf, rNodes) {
  const out = []
  const cube = cubeOf[node.id]
  const ts   = new Date().toISOString()

  out.push(`// ${'='.repeat(60)}`)
  out.push(`// CubeJS cube: ${cube}`)
  out.push(`// Tabla: ${tableOf[node.id]}  |  Modelo: ${m.name}`)
  out.push(`// Generado: ${ts}`)
  out.push(`// ${'='.repeat(60)}`)
  out.push('')
  out.push(`cube(\`${cube}\`, {`)
  out.push(`  sql_table: \`${tableOf[node.id]}\`,`)
  out.push('')

  if (node.type === 'dimension') {
    // measures — count always present
    out.push('  measures: {')
    out.push('    count: {')
    out.push('      type: `count`,')
    out.push('    },')
    out.push('  },')
    out.push('')

    // dimensions
    if (node.fields.length) {
      out.push('  dimensions: {')
      node.fields.forEach(f => {
        const name = toCamelCase(f.name)
        const sql  = toSqlName(f.name)
        const type = cubeJsDimType(f)
        out.push(`    ${name}: {`)
        out.push(`      sql: \`\${CUBE}.${sql}\`,`)
        out.push(`      type: \`${type}\`,`)
        if (f.isKey) out.push(`      primary_key: true,`)
        if (f.description && !f.isKey) out.push(`      title: \`${f.description}\`,`)
        out.push(`    },`)
      })
      out.push('  },')
    }

  } else {
    // fact cube
    // Build join map from FK field descriptions
    const joinMap = {}
    node.fields.filter(f => f.isFk && f.description).forEach(f => {
      const match = f.description.match(/FK → (.+)\.(.+)/)
      if (!match) return
      const dimNode = (rNodes || m.nodes).find(n => n.name === match[1] && n.type === 'dimension')
      if (!dimNode || joinMap[dimNode.id]) return
      joinMap[dimNode.id] = {
        dimCube: cubeOf[dimNode.id],
        dimNode,
        factCol: toSqlName(f.name),
        dimCol:  toSqlName(match[2])
      }
    })

    const joinEntries = Object.values(joinMap)
    if (joinEntries.length) {
      out.push('  joins: {')
      joinEntries.forEach(j => {
        out.push(`    ${j.dimCube}: {`)
        out.push(`      sql: \`\${CUBE}.${j.factCol} = \${${j.dimCube}}.${j.dimCol}\`,`)
        out.push(`      relationship: \`many_to_one\`,`)
        out.push(`    },`)
      })
      out.push('  },')
      out.push('')
    }

    // measures — count + numeric fields
    const measureFields = node.fields.filter(f => !f.isFk && !f.isKey)
    out.push('  measures: {')
    out.push('    count: {')
    out.push('      type: `count`,')
    out.push('    },')
    measureFields.forEach(f => {
      const name = toCamelCase(f.name)
      const sql  = toSqlName(f.name)
      const type = cubeJsMeasureType(f)
      out.push(`    ${name}: {`)
      out.push(`      sql: \`\${CUBE}.${sql}\`,`)
      out.push(`      type: \`${type}\`,`)
      if (f.description) out.push(`      title: \`${f.description}\`,`)
      out.push(`    },`)
    })
    out.push('  },')
    out.push('')

    // dimensions — FK cols + explicit key fields for filtering / grouping
    const dimFields = node.fields.filter(f => f.isFk || f.isKey)
    if (dimFields.length) {
      out.push('  dimensions: {')
      dimFields.forEach(f => {
        const name = toCamelCase(f.name)
        const sql  = toSqlName(f.name)
        out.push(`    ${name}: {`)
        out.push(`      sql: \`\${CUBE}.${sql}\`,`)
        out.push(`      type: \`${cubeJsDimType(f)}\`,`)
        if (f.isKey) out.push(`      primary_key: true,`)
        out.push(`    },`)
      })
      out.push('  },')
      out.push('')
    }

    // pre_aggregations — rollup with all measures + detected time dimension
    let timeDimRef = null
    for (const j of joinEntries) {
      const timeField = j.dimNode.fields.find(f => cubeJsDimType(f) === 'time' && !f.isKey)
      if (timeField) { timeDimRef = `${j.dimCube}.${toCamelCase(timeField.name)}`; break }
    }
    const measureRefs = ['CUBE.count', ...measureFields.map(f => `CUBE.${toCamelCase(f.name)}`)]
    out.push('  pre_aggregations: {')
    out.push('    main: {')
    out.push('      type: `rollup`,')
    out.push(`      measures: [${measureRefs.join(', ')}],`)
    if (timeDimRef) {
      out.push(`      time_dimension: ${timeDimRef},`)
      out.push('      granularity: `day`,')
    }
    out.push('      refresh_key: {')
    out.push('        every: `1 hour`,')
    out.push('      },')
    out.push('    },')
    out.push('  },')
  }

  out.push('});')
  return out.join('\n')
}

// Download a single node as its own .js file
function exportSingleCube(node) {
  if (!model.value || !node) return
  const m = model.value
  const rNodes = resolvedNodes.value
  const tableOf = {}; rNodes.forEach(n => { tableOf[n.id] = toSqlName(n.name) })
  const cubeOf  = {}; rNodes.forEach(n => { cubeOf[n.id]  = cubeNameFrom(n) })

  const content = buildCubeJS(node, m, tableOf, cubeOf, rNodes)
  const fileName = `${cubeOf[node.id]}.js`
  const blob = new Blob([content], { type: 'application/javascript' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = fileName; a.click()
  URL.revokeObjectURL(url)
  uiStore.addAlert({ message: `Cubo ${cubeOf[node.id]} exportado`, type: 'success' })
}

// Export all nodes as individual .js files bundled in a ZIP
async function handleExportCubeJS() {
  if (!model.value) return
  const m = model.value
  const rNodes = resolvedNodes.value
  const tableOf = {}; rNodes.forEach(n => { tableOf[n.id] = toSqlName(n.name) })
  const cubeOf  = {}; rNodes.forEach(n => { cubeOf[n.id]  = cubeNameFrom(n) })

  const zip = new JSZip()
  rNodes.forEach(node => {
    zip.file(`${cubeOf[node.id]}.js`, buildCubeJS(node, m, tableOf, cubeOf, rNodes))
  })

  const slug = m.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'schema'
  const zipBlob = await zip.generateAsync({ type: 'blob' })
  const url = URL.createObjectURL(zipBlob)
  const a = document.createElement('a'); a.href = url; a.download = `${slug}_cubejs.zip`; a.click()
  URL.revokeObjectURL(url)
  uiStore.addAlert({ message: `${rNodes.length} cubos exportados en ${slug}_cubejs.zip`, type: 'success' })
}

// ── Canvas ───────────────────────────────────────────────────
const canvasEl = ref(null)

const canvasSize = computed(() => {
  const nodes = model.value?.nodes || []
  const maxX = Math.max(900, ...nodes.map(n => n.x + 240))
  const maxY = Math.max(600, ...nodes.map(n => n.y + nodeHeight(n) + 60))
  return { w: maxX, h: maxY }
})

function canvasPos(clientX, clientY) {
  const rect = canvasEl.value.getBoundingClientRect()
  return {
    x: clientX - rect.left + canvasEl.value.scrollLeft,
    y: clientY - rect.top + canvasEl.value.scrollTop
  }
}

// ── Selection ────────────────────────────────────────────────
const selectedNode = ref(null)
const selectedRel = ref(null)
const showFieldDesc = ref(false)

// ── Node drag state ──────────────────────────────────────────
const dragging = ref(null)  // { nodeId, startX, startY, origX, origY }

// ── Field drag state ─────────────────────────────────────────
// Active when user drags the 🔑 handle from a dimension key field
const dragField = ref(null)  // { nodeId, nodeName, fieldId, fieldName, startPos:{x,y} }
const dropTargetId = ref(null)
const mousePos = ref({ x: 0, y: 0 })

// ── Lifecycle ────────────────────────────────────────────────
onMounted(() => {
  if (!model.value) { router.push('/models'); return }
  uiStore.setBreadcrumbs(['Modelos', model.value.name])
  // Global listeners capture mouse events even outside the component
  document.addEventListener('mousemove', onGlobalMouseMove)
  document.addEventListener('mouseup', onGlobalMouseUp)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onGlobalMouseMove)
  document.removeEventListener('mouseup', onGlobalMouseUp)
})

watch(() => model.value?.name, name => { if (name) uiStore.setBreadcrumbs(['Modelos', name]) })

// ── Geometry helpers ─────────────────────────────────────────
const NODE_WIDTH = 200

function nodeHeight(node) {
  const warn = node?.type === 'dimension' && node?.fields?.length > 0 && !node?.fields?.some(f => f.isKey)
  return 40 + (node?.fields?.length || 0) * 28 + 8 + (warn ? 24 : 0)
}

function nodeCenter(nodeId) {
  const node = model.value?.nodes.find(n => n.id === nodeId)
  if (!node) return { x: 0, y: 0 }
  return { x: node.x + NODE_WIDTH / 2, y: node.y + nodeHeight(node) / 2 }
}

function relMidpoint(rel) {
  const a = nodeCenter(rel.fromNodeId), b = nodeCenter(rel.toNodeId)
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }
}

function nodeName(nodeId) {
  return model.value?.nodes.find(n => n.id === nodeId)?.name || nodeId
}

function keyFieldStartPos(dimNode, field) {
  const idx = dimNode.fields.findIndex(f => f.id === field.id)
  return { x: dimNode.x + NODE_WIDTH, y: dimNode.y + 44 + idx * 28 }
}

function factNodeAt(pos) {
  return model.value?.nodes.find(n => {
    if (n.type !== 'fact') return false
    const h = nodeHeight(n)
    return pos.x >= n.x && pos.x <= n.x + NODE_WIDTH && pos.y >= n.y && pos.y <= n.y + h
  }) || null
}

function fieldIcon(nodeType, dataType) {
  if (nodeType === 'fact') return { integer: '#', decimal: '~', currency: '$', percentage: '%' }[dataType] || '#'
  return { string: 'A', date: '📅', boolean: '?', integer: '#' }[dataType] || 'A'
}

// ── Add node ─────────────────────────────────────────────────
let nodeCounter = 0
function addNode(type) {
  const offset = nodeCounter++ * 30
  const node = modelStore.addNode(modelId, {
    type,
    name: type === 'fact' ? 'Nueva tabla de hechos' : 'Nueva dimensión',
    x: 60 + offset, y: 60 + offset
  })
  selectedRel.value = null
  selectedNode.value = node
}

// ── Node drag ────────────────────────────────────────────────
function startDrag(node, e) {
  if (dragField.value) return
  e.preventDefault()
  dragging.value = { nodeId: node.id, startX: e.clientX, startY: e.clientY, origX: node.x, origY: node.y }
}

// Handles only node drag (called from canvas @mousemove to update node position)
function onNodeDragMove(e) {
  if (!dragging.value) return
  const dx = e.clientX - dragging.value.startX
  const dy = e.clientY - dragging.value.startY
  modelStore.updateNode(modelId, dragging.value.nodeId, {
    x: Math.max(0, dragging.value.origX + dx),
    y: Math.max(0, dragging.value.origY + dy)
  })
}

// ── Field drag start ─────────────────────────────────────────
function startFieldDrag(dimNode, field, e) {
  if (!field.isKey) return
  e.preventDefault()
  e.stopPropagation()   // prevent startDrag on parent node div
  dragging.value = null // clear any node drag

  if (!canvasEl.value) return
  const pos = canvasPos(e.clientX, e.clientY)
  dragField.value = {
    nodeId: dimNode.id,
    nodeName: dimNode.name,
    fieldId: field.id,
    fieldName: field.name,
    startPos: keyFieldStartPos(dimNode, field)
  }
  mousePos.value = pos
}

// ── Global mouse move (field drag tracking) ──────────────────
function onGlobalMouseMove(e) {
  if (!dragField.value || !canvasEl.value) return
  const pos = canvasPos(e.clientX, e.clientY)
  mousePos.value = pos
  // Highlight fact node under cursor
  const target = factNodeAt(pos)
  dropTargetId.value = target?.id || null
}

// ── Global mouse up ───────────────────────────────────────────
function onGlobalMouseUp(e) {
  if (dragField.value && canvasEl.value) {
    const pos = canvasPos(e.clientX, e.clientY)
    const factNode = factNodeAt(pos)
    if (factNode) handleFieldDrop(factNode)
  }
  dragField.value = null
  dropTargetId.value = null
  dragging.value = null
}

// ── Drop: link dim key → fact ─────────────────────────────────
function handleFieldDrop(factNode) {
  const dimNode = model.value?.nodes.find(n => n.id === dragField.value.nodeId)
  if (!dimNode) return

  const toSnake = s => s.toLowerCase().trim().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
  const fkName = `${toSnake(dimNode.name)}_${toSnake(dragField.value.fieldName)}`

  // Add FK field if not present
  if (!factNode.fields.find(f => f.name === fkName)) {
    // Match key field type but SERIAL→INTEGER and BIGSERIAL→BIGINT (FK cols can't be sequences)
    const dimKeyField = dimNode.fields.find(f => f.isKey)
    let fkDataType
    if (dimKeyField) {
      const keyDt = dtStore.getById(dimKeyField.dataType)
      if (keyDt?.baseType === 'SERIAL') {
        fkDataType = dtStore.allTypes.find(t => t.baseType === 'INTEGER')?.id ?? 'dt-int'
      } else if (keyDt?.baseType === 'BIGSERIAL') {
        fkDataType = dtStore.allTypes.find(t => t.baseType === 'BIGINT')?.id ?? 'dt-bigint'
      } else {
        fkDataType = dimKeyField.dataType
      }
    } else {
      fkDataType = dtStore.allTypes.find(t => t.id === 'dt-int')?.id
               ?? dtStore.allTypes.find(t => t.baseType === 'INTEGER')?.id
               ?? dtStore.allTypes[0]?.id
    }
    modelStore.addField(modelId, factNode.id, {
      name: fkName,
      description: `FK → ${dimNode.name}.${dragField.value.fieldName}`,
      dataType: fkDataType,
      isFk: true
    })
  }

  // Create relationship if not already exists
  const relExists = model.value?.relationships.some(
    r => (r.fromNodeId === dimNode.id && r.toNodeId === factNode.id) ||
         (r.fromNodeId === factNode.id && r.toNodeId === dimNode.id)
  )
  if (!relExists) {
    modelStore.addRelationship(modelId, {
      fromNodeId: dimNode.id,
      toNodeId: factNode.id,
      cardinality: '1:N'
    })
  }
}

// ── Node click / selection ────────────────────────────────────
function onNodeClick(node) {
  selectedNode.value = model.value?.nodes.find(n => n.id === node.id) || null
  selectedRel.value = null
}

function selectRelationship(rel) {
  selectedRel.value = model.value?.relationships.find(r => r.id === rel.id) || null
  selectedNode.value = null
}

function onCanvasClick() {
  selectedNode.value = null
  selectedRel.value = null
}

// ── Node property updates ─────────────────────────────────────
function refreshSelectedNode() {
  if (!selectedNode.value) return
  selectedNode.value = model.value?.nodes.find(n => n.id === selectedNode.value.id) || null
}

function updateNodeName(name) {
  if (!selectedNode.value) return
  modelStore.updateNode(modelId, selectedNode.value.id, { name })
  refreshSelectedNode()
}

function addField() {
  if (!selectedNode.value) return
  const isDim = selectedNode.value.type === 'dimension'
  const autoKey = isDim && selectedNode.value.fields.length === 0
  // Pick sensible default type IDs from store, fallback to first available
  const allTypes = dtStore.allTypes
  const defaultDimKey  = allTypes.find(t => t.id === 'dt-serial') ?? allTypes.find(t => t.baseType === 'SERIAL') ?? allTypes[0]
  const defaultDimText = allTypes.find(t => t.id === 'dt-varchar') ?? allTypes.find(t => t.baseType === 'VARCHAR') ?? allTypes[0]
  const defaultFact    = allTypes.find(t => t.id === 'dt-numeric') ?? allTypes.find(t => t.baseType === 'NUMERIC') ?? allTypes[0]
  const defaultType = autoKey ? defaultDimKey?.id : (isDim ? defaultDimText?.id : defaultFact?.id)
  modelStore.addField(modelId, selectedNode.value.id, {
    name: autoKey ? 'id' : 'nuevo_campo',
    description: '',
    dataType: defaultType ?? (allTypes[0]?.id ?? 'dt-int'),
    isKey: autoKey
  })
  refreshSelectedNode()
}

function setKeyField(fieldId) {
  if (!selectedNode.value) return
  modelStore.setKeyField(modelId, selectedNode.value.id, fieldId)
  refreshSelectedNode()
}

function updateField(fieldId, key, value) {
  if (!selectedNode.value) return
  modelStore.updateField(modelId, selectedNode.value.id, fieldId, { [key]: value })
  refreshSelectedNode()
}

function deleteField(fieldId) {
  if (!selectedNode.value) return
  modelStore.deleteField(modelId, selectedNode.value.id, fieldId)
  refreshSelectedNode()
}

function deleteNodeConfirm() {
  if (!selectedNode.value) return
  if (!confirm(`¿Eliminar "${selectedNode.value.name}" y todas sus relaciones?`)) return
  modelStore.deleteNode(modelId, selectedNode.value.id)
  selectedNode.value = null
}

// ── Relationship updates ──────────────────────────────────────
function updateRelCardinality(cardinality) {
  if (!selectedRel.value) return
  modelStore.updateRelationship(modelId, selectedRel.value.id, { cardinality })
  selectedRel.value = model.value?.relationships.find(r => r.id === selectedRel.value.id) || null
}

function deleteRelationship() {
  if (!selectedRel.value) return
  modelStore.deleteRelationship(modelId, selectedRel.value.id)
  selectedRel.value = null
}

// ── AI Assist ─────────────────────────────────────────────────
const aiAssistOpen    = ref(false)
const aiAssistPrompt  = ref('')
const aiAssistLoading = ref(false)
const aiAssistError   = ref(null)
const aiAssistResult  = ref(null)   // array of { type, name, description, fields }
const aiSelectedTables = ref([])
const aiViewMode      = ref('visual') // 'visual' | 'json'
const aiRawJson       = ref('')

function buildModelAssistPrompt() {
  const existing = (model.value?.nodes || [])
    .map(n => `  - ${n.type === 'fact' ? '[HECHO]' : '[DIM]'} ${n.name} (${n.fields.length} campos)`)
    .join('\n') || '  (ninguna)'

  const availableTypes = dtStore.allTypes
    .map(t => `${t.id} → ${t.name} (${dtStore.sqlOf(t.id)})`)
    .join('\n')

  return `Eres un experto en modelado dimensional (star schema / snowflake). Tu tarea es diseñar tablas de hechos y dimensiones.

MODELO ACTUAL: "${model.value?.name}"
${model.value?.description ? `DESCRIPCIÓN: ${model.value.description}` : ''}

TABLAS YA EXISTENTES EN EL MODELO:
${existing}

TIPOS DE DATOS DISPONIBLES (usa exactamente estos IDs en el campo "dataTypeId"):
${availableTypes}

PETICIÓN DEL DISEÑADOR:
${aiAssistPrompt.value}

INSTRUCCIONES:
1. Responde SOLO con un bloque JSON válido (\`\`\`json ... \`\`\`)
2. El JSON debe ser un array de objetos tabla con este formato EXACTO:
[
  {
    "type": "fact" | "dimension", // USA EXACTAMENTE UNA DE ESTAS DOS PALABRAS (NO TRADUCIR)
    "name": "NombreTabla",
    "description": "descripción breve",
    "fields": [
      { "name": "nombre_campo", "dataTypeId": "dt-serial", "isKey": true, "description": "descripción" },
      { "name": "otro_campo", "dataTypeId": "dt-varchar", "isKey": false, "description": "" }
    ]
  }
]
3. Cada tabla de dimensión DEBE tener exactamente un campo con "isKey": true (la llave primaria)
4. Los nombres de campo deben estar en snake_case
5. Usa los dataTypeId exactos de la lista proporcionada
6. No incluyas texto fuera del bloque JSON
7. IMPORTANTE: El JSON debe ser estrictamente válido. No uses saltos de línea literales dentro de las cadenas de texto (usa \\n si es necesario).`
}

async function runAIAssist() {
  if (!aiAssistPrompt.value.trim() || !llmStore.isConfigured) return
  aiAssistLoading.value = true
  aiAssistError.value = null
  aiAssistResult.value = null
  aiSelectedTables.value = []

  try {
    const cfg = llmStore.configFor('modelAssist')
    const text = await callLlm({ provider: cfg.provider, modelId: cfg.modelId, apiKey: cfg.apiKey, prompt: buildModelAssistPrompt() })

    let tables = null;
    let extractedText = text.trim();

    // 1. Try raw directly
    try {
      const p = JSON.parse(extractedText);
      if (Array.isArray(p)) { tables = p; }
      else if (p.tables && Array.isArray(p.tables)) { tables = p.tables; }
    } catch (e1) {
      // 2. Try Markdown block
      const match = extractedText.match(/```(?:json)?\s*([\s\S]*?)(?:```|$)/i)
      const block = match ? match[1].trim() : extractedText;
      try {
        const p = JSON.parse(block);
        if (Array.isArray(p)) { tables = p; }
        else if (p.tables && Array.isArray(p.tables)) { tables = p.tables; }
      } catch (e2) {
        // 3. Try fallback array extraction
        const startIdx = block.indexOf('[');
        const endIdx = block.lastIndexOf(']');
        if (startIdx !== -1 && endIdx !== -1 && endIdx >= startIdx) {
          const arrStr = block.substring(startIdx, endIdx + 1);
          try {
            const p = JSON.parse(arrStr);
            if (Array.isArray(p)) { tables = p; }
          } catch (e3) {
            aiRawJson.value = extractedText;
            throw new Error(`Error de sintaxis JSON: ${e3.message}`);
          }
        } else {
          aiRawJson.value = extractedText;
          throw new Error('No se pudo encontrar un array JSON válido en la respuesta.');
        }
      }
    }

    if (!tables) {
       aiRawJson.value = extractedText;
       throw new Error('La respuesta de la IA no contiene el formato de tablas esperado.');
    }

    // Normalizar el tipo por si el LLM usa "hecho", "hechos", "fact_table", etc.
    tables.forEach(t => {
      if (typeof t.type === 'string') {
        const typeStr = t.type.toLowerCase()
        t.type = (typeStr.includes('fact') || typeStr.includes('hecho')) ? 'fact' : 'dimension'
      } else {
        t.type = 'dimension'
      }
    })

    aiRawJson.value = JSON.stringify(tables, null, 2)
    aiViewMode.value = 'visual'

    // Enrich with resolved dataType labels for display
    aiAssistResult.value = tables.map(t => ({
      ...t,
      fields: t.fields.map(f => ({
        ...f,
        dataTypeLabel: dtStore.getById(f.dataTypeId)?.name ?? f.dataTypeId
      }))
    }))
    // Pre-select all
    aiSelectedTables.value = tables.map((_, i) => i)
  } catch (e) {
    aiAssistError.value = e.message
  } finally {
    aiAssistLoading.value = false
  }
}

function aiToggleTable(idx) {
  const pos = aiSelectedTables.value.indexOf(idx)
  if (pos === -1) aiSelectedTables.value.push(idx)
  else aiSelectedTables.value.splice(pos, 1)
}

function aiSelectAll(select) {
  aiSelectedTables.value = select ? (aiAssistResult.value || []).map((_, i) => i) : []
}

function downloadAIAssistJSON() {
  if (!aiRawJson.value) return
  const blob = new Blob([aiRawJson.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ai_generated_tables_${new Date().getTime()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function applyAITables() {
  if (!aiAssistResult.value) return
  const allTypes = dtStore.allTypes
  const fallbackType = allTypes.find(t => t.id === 'dt-varchar')?.id ?? allTypes[0]?.id

  let offsetX = 60
  const offsetY = 80
  const spacing = 240

  aiSelectedTables.value.forEach(idx => {
    const table = aiAssistResult.value[idx]
    const node = modelStore.addNode(modelId, {
      type: table.type,
      name: table.name,
      x: offsetX,
      y: table.type === 'fact' ? offsetY + 200 : offsetY
    })
    offsetX += spacing

    table.fields.forEach(f => {
      modelStore.addField(modelId, node.id, {
        name: f.name,
        description: f.description || '',
        dataType: allTypes.find(t => t.id === f.dataTypeId)?.id ?? fallbackType,
        isKey: !!f.isKey,
        isFk: false
      })
    })
  })

  uiStore.addAlert({ message: `${aiSelectedTables.value.length} tabla(s) añadidas al canvas`, type: 'success' })
  aiAssistOpen.value = false
  aiAssistResult.value = null
  aiAssistPrompt.value = ''
  aiSelectedTables.value = []
  aiViewMode.value = 'visual'
}

// ── Global Model ──────────────────────────────────────────────
const showGlobalDimModal = ref(false)
const selectedGlobalDims = ref([])

function resolveNode(node) {
  if (!node.globalRef) return node
  const gNode = modelStore.globalModel?.nodes.find(n => n.id === node.globalRef.nodeId)
  if (!gNode) return node
  return { ...gNode, id: node.id, x: node.x, y: node.y, globalRef: node.globalRef }
}

const resolvedNodes = computed(() => (model.value?.nodes || []).map(resolveNode))

const availableGlobalDims = computed(() => {
  const gModel = modelStore.globalModel
  if (!gModel || model.value?.isGlobal) return []
  const alreadyReferenced = new Set(
    (model.value?.nodes || []).filter(n => n.globalRef).map(n => n.globalRef.nodeId)
  )
  return gModel.nodes.filter(n => n.type === 'dimension' && !alreadyReferenced.has(n.id))
})

function addSelectedGlobalDims() {
  selectedGlobalDims.value.forEach((nodeId, i) => {
    modelStore.addGlobalDimRef(modelId, nodeId, { x: 60 + i * 220, y: 60 })
  })
  selectedGlobalDims.value = []
  showGlobalDimModal.value = false
}
</script>

<style scoped>
.editor-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0;
  user-select: none;
}

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  flex-shrink: 0;
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.toolbar-title { flex: 1; min-width: 0; display: flex; align-items: center; }
.title-text {
  font-size: 16px; font-weight: 600; color: var(--text);
  cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.edit-hint { color: var(--text-secondary); opacity: 0.5; }
.title-text:hover .edit-hint { opacity: 1; }
.title-edit-input { font-size: 15px; font-weight: 600; max-width: 300px; }
.toolbar-actions { display: flex; gap: 6px; flex-shrink: 0; flex-wrap: wrap; align-items: center; }
.btn-icon-only { width: 30px; padding: 0; justify-content: center; }
.toolbar-sep { width: 1px; height: 20px; background: var(--border); margin: 0 2px; flex-shrink: 0; }

/* Editor body */
.editor-body {
  display: flex; flex: 1; min-height: 0;
  background: #f5f5f5;
  border: 1px solid var(--border); border-top: none;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

/* Canvas */
.model-canvas {
  flex: 1;
  position: relative;
  overflow: auto;
  min-height: 500px;
}
.model-canvas.dragging-field { cursor: crosshair; }

.canvas-svg {
  position: absolute; top: 0; left: 0;
  pointer-events: none;
}
.canvas-svg .rel-line { pointer-events: stroke; cursor: pointer; }
.canvas-svg .rel-label { font-size: 12px; font-weight: 600; pointer-events: all; cursor: pointer; }

.canvas-hint {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  pointer-events: none;
}
.canvas-hint p {
  font-size: 14px; color: var(--text-secondary);
  text-align: center; max-width: 320px; line-height: 1.6;
  background: rgba(255,255,255,0.7); padding: 16px 24px; border-radius: 8px;
}

.json-editor {
  font-family: monospace;
  font-size: 13px;
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 6px;
  padding: 12px;
  resize: vertical;
}

/* Floating drag pill */
.drag-pill {
  position: absolute;
  background: #52c41a;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  z-index: 10;
}
.drag-pill-hint { font-weight: 400; opacity: 0.85; margin-left: 4px; }

/* Nodes */
.model-node {
  position: absolute;
  width: 200px;
  background: #fff;
  border-radius: 8px;
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  cursor: move;
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
}
.model-node:hover { box-shadow: var(--shadow-md); }
.model-node.selected { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(24,144,255,0.2); }
.model-node.drop-target { border-color: #52c41a; box-shadow: 0 0 0 3px rgba(82,196,26,0.35); }

.node-header {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 10px;
  font-size: 13px; font-weight: 600; color: #fff;
  cursor: move;
}
.node-header.fact { background: var(--primary); }
.node-header.dimension { background: #52c41a; }

.node-badge {
  font-size: 10px; font-weight: 700;
  background: rgba(255,255,255,0.25);
  padding: 1px 5px; border-radius: 3px; letter-spacing: 0.5px; flex-shrink: 0;
}
.node-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.node-fields { padding: 6px 0; }

.node-field {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 8px 3px 4px;
  font-size: 12px; color: var(--text);
  border-bottom: 1px solid var(--border);
  min-height: 28px;
}
.node-field:last-child { border-bottom: none; }
.node-field.is-key { background: #f6ffed; }
.node-field.is-fk { background: #e6f7ff; }

/* Drag handle for key field */
.key-drag-handle {
  flex-shrink: 0;
  width: 18px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #52c41a;
  cursor: grab;
  border-radius: 3px;
  opacity: 0.5;
  transition: opacity 0.15s, background 0.15s;
  user-select: none;
}
.key-drag-handle:hover { opacity: 1; background: rgba(82,196,26,0.12); }
.key-drag-handle:active { cursor: grabbing; opacity: 1; }
.field-icon-placeholder { flex-shrink: 0; width: 18px; }

.field-icon { flex-shrink: 0; width: 16px; text-align: center; font-size: 11px; }
.key-icon, .fk-icon { font-size: 11px; }
.field-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.field-type { font-size: 10px; color: var(--text-secondary); flex-shrink: 0; }

.node-empty { padding: 6px 10px; font-size: 12px; color: var(--text-secondary); font-style: italic; }
.node-warn { padding: 4px 10px; font-size: 11px; color: #d46b08; background: #fff7e6; }

/* Properties panel */
.props-panel {
  width: 290px; flex-shrink: 0;
  border-radius: 0; border: none; border-left: 1px solid var(--border);
  display: flex; flex-direction: column;
  overflow-y: auto; background: #fff;
}
.props-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.props-type-badge {
  font-size: 11px; font-weight: 700;
  padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px; color: #fff;
}
.props-type-badge.fact { background: var(--primary); }
.props-type-badge.dimension { background: #52c41a; }
.props-type-badge.rel { background: #722ed1; }

.props-body { padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; flex: 1; }

.props-section-title {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.6px; margin-top: 4px;
}

.props-warn {
  font-size: 12px; color: #d46b08;
  background: #fff7e6; padding: 8px 10px; border-radius: 6px; line-height: 1.4;
}

.fields-list { display: flex; flex-direction: column; gap: 6px; }

.field-item { display: flex; flex-direction: column; gap: 0; padding-bottom: 4px; border-bottom: 1px solid var(--border-light, #f0f0f0); }
.field-item:last-child { border-bottom: none; }

/* Key toggle button */
.key-toggle {
  flex-shrink: 0;
  width: 24px; height: 24px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  opacity: 0.35;
  transition: all 0.15s;
  padding: 0;
}
.key-toggle:hover { opacity: 0.7; border-color: #52c41a; }
.key-toggle.active { opacity: 1; background: #f6ffed; border-color: #52c41a; }

.field-row1 { display: flex; align-items: center; gap: 4px; }
.field-row2 { padding-left: 28px; margin-top: 3px; }

.desc-toggle {
  width: 22px; height: 22px; border-radius: 4px;
  color: var(--text-secondary); opacity: 0.6;
  text-transform: none; letter-spacing: 0;
}
.desc-toggle:hover { opacity: 1; background: var(--bg); color: var(--primary); }
.desc-toggle.active { opacity: 1; color: var(--primary); background: #e6f4ff; }
.field-name-input { flex: 1; min-width: 0; font-size: 12px; padding: 4px 6px; height: 28px; }
.field-type-select { width: 86px; flex-shrink: 0; font-size: 12px; padding: 4px 4px; height: 28px; }
.field-desc-input { width: 100%; font-size: 11px; padding: 3px 6px; height: 24px; color: var(--text-secondary); }
.field-del-btn { flex-shrink: 0; color: var(--text-secondary); }
.field-del-btn:hover { color: var(--error); background: #fff2f0; }

.add-field-btn { align-self: flex-start; font-size: 12px; }
.props-divider { height: 1px; background: var(--border); margin: 4px 0; }

.btn-danger-outline {
  background: transparent; color: var(--error); border: 1px solid var(--error);
  padding: 5px 12px; border-radius: var(--border-radius);
  cursor: pointer; font-size: 12px; font-weight: 500; transition: background 0.15s;
}
.btn-danger-outline:hover { background: #fff2f0; }

.rel-nodes-info {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; background: var(--bg); border-radius: 6px; font-size: 13px;
}
.rel-node-tag {
  flex: 1; text-align: center; font-weight: 600; color: var(--text);
  font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 12px; font-weight: 500; color: var(--text); }

/* Global-ref nodes */
.model-node.global-ref { border-style: dashed; border-color: #722ed1; opacity: 0.9; }
.model-node.global-ref .node-header.dimension { background: #722ed1; }

/* Global-ref properties panel */
.global-ref-body { padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; flex: 1; }
.global-ref-notice {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #722ed1; background: #f9f0ff;
  padding: 8px 10px; border-radius: 6px; line-height: 1.4;
}
.global-ref-fields { display: flex; flex-direction: column; gap: 2px; }
.global-ref-field {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 6px; font-size: 12px; color: var(--text);
  border-bottom: 1px solid var(--border);
}
.global-ref-field:last-child { border-bottom: none; }
.global-ref-tag {
  font-size: 9px; font-weight: 700; background: #722ed1; color: #fff;
  padding: 1px 5px; border-radius: 3px; margin-left: 6px; vertical-align: middle;
}

/* Global dim modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  width: 420px; max-width: 95vw;
  padding: 0; overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid var(--border);
}
.modal-header h3 { font-size: 15px; font-weight: 600; color: var(--text); margin: 0; }
.modal-body { padding: 16px 20px; max-height: 60vh; overflow-y: auto; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px; border-top: 1px solid var(--border); background: #fafafa;
}
.modal-empty { font-size: 13px; color: var(--text-secondary); }
.global-dim-list { display: flex; flex-direction: column; gap: 6px; }
.global-dim-option {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 6px; border: 2px solid var(--border);
  cursor: pointer; transition: border-color 0.15s, background 0.15s;
}
.global-dim-option:hover { border-color: #722ed1; background: #f9f0ff; }
.global-dim-option.selected { border-color: #722ed1; background: #f0e6ff; }
.global-dim-icon { font-size: 16px; flex-shrink: 0; }
.global-dim-name { flex: 1; font-size: 13px; font-weight: 600; color: var(--text); }
.global-dim-fields { font-size: 11px; color: var(--text-secondary); }
/* ── IA Assist toolbar button (mismo estilo que ChartConfigModal) ── */
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

/* ── AI Assist modal ──────────────────────────────────────── */
.ai-assist-modal { max-width: 680px; width: 96vw; max-height: 88vh; display: flex; flex-direction: column; }
.ai-assist-header {
  display: flex; align-items: center; gap: 8px;
  background: #722ed1; color: #fff; padding: 12px 16px;
  border-radius: 8px 8px 0 0;
  font-size: 14px; font-weight: 600;
}
.ai-model-label {
  font-size: 11px; font-weight: 400;
  background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px;
}
.ai-assist-body {
  padding: 16px; overflow-y: auto; flex: 1;
  display: flex; flex-direction: column; gap: 14px;
}

/* Context chips */
.ai-context-row { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.ai-ctx-label { font-size: 11px; font-weight: 600; color: var(--text-secondary); white-space: nowrap; }
.ai-chip { font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 10px; }
.ai-chip-model  { background: #722ed1; color: #fff; }
.ai-chip-fact   { background: #e6f4ff; color: #1890ff; border: 1px solid #91caff; }
.ai-chip-dim    { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.ai-chip-more   { font-size: 11px; color: var(--text-secondary); }

/* Result section */
.ai-result-section { display: flex; flex-direction: column; gap: 10px; }
.ai-result-title {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 13px; font-weight: 600; color: var(--text);
}
.ai-tables-list { display: flex; flex-direction: column; gap: 8px; }
.ai-table-card {
  border: 2px solid var(--border); border-radius: 8px;
  overflow: hidden; cursor: pointer; transition: border-color 0.15s;
}
.ai-table-card:hover { border-color: #d3adf7; }
.ai-table-card.selected { border-color: #722ed1; }
.ai-table-card.selected.fact { border-color: var(--primary); }
.ai-table-card.selected.dim  { border-color: #52c41a; }
.ai-table-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: var(--bg);
  font-size: 13px;
}
.ai-table-header input[type=checkbox] { flex-shrink: 0; cursor: pointer; }
.ai-table-badge {
  font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px;
  flex-shrink: 0;
}
.ai-table-badge.fact { background: #e6f4ff; color: #1890ff; }
.ai-table-badge.dimension { background: #f6ffed; color: #52c41a; }
.ai-table-name { font-weight: 600; color: var(--text); flex: 1; }
.ai-table-count { font-size: 11px; color: var(--text-secondary); white-space: nowrap; }
.ai-table-fields {
  display: flex; flex-wrap: wrap; gap: 4px; padding: 8px 12px;
  border-top: 1px solid var(--border);
}
.ai-field-chip {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 11px; padding: 2px 7px; border-radius: 8px;
  background: #f5f5f5; color: var(--text);
}
.ai-field-chip.is-key { background: #fff7e6; color: #d48806; }
.ai-field-type { color: var(--text-secondary); font-size: 10px; }
.ai-table-desc { padding: 0 12px 8px; font-size: 12px; color: var(--text-secondary); font-style: italic; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 0.8s linear infinite; }
</style>
