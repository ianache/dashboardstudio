<!--
  FlowEditorCanvas — Reusable visual diagram editor.

  Props (config):
    diagramType  : String  — ID of the diagram type being designed (e.g. 'data-integration')
    tools        : Array   — Tool objects already filtered for this diagram type

  Prop (data):
    diagramData  : Object  — Initial diagram { nodes: [], connections: [], metadata: {} }

  Emits:
    save(diagramData) — full diagram state when user clicks Save
-->
<template>
  <div class="fec-root" :class="{ 'fec-root--readonly': readOnly }" @mousemove="onGlobalMousemove" @mouseup="onGlobalMouseup">

    <!-- ── Left Panel: Components Toolbar ─────────────────────────────────── -->
    <aside v-if="!readOnly" class="fec-left" :class="{ 'fec-left--collapsed': leftCollapsed }">
      <button class="fec-toggle fec-toggle--left" @click="leftCollapsed = !leftCollapsed" :title="leftCollapsed ? 'Expandir' : 'Contraer'">
        <span class="msi">{{ leftCollapsed ? 'chevron_right' : 'chevron_left' }}</span>
      </button>

      <div class="fec-left-inner">
        <div v-if="!leftCollapsed" class="fec-left-head">
          <span class="msi" style="font-size:15px;color:#2563eb">widgets</span>
          <span class="fec-panel-label">Componentes</span>
          <span class="fec-diagram-tag">{{ diagramTypeLabel }}</span>
        </div>

        <template v-for="cat in toolsByCategory" :key="cat.key">
          <div class="fec-cat">
            <div class="fec-cat-hdr" @click="!leftCollapsed && toggleCat(cat.key)" :title="cat.label">
              <div class="fec-cat-hdr-l">
                <div class="fec-cat-dot" :style="{ background: cat.color }"></div>
                <span v-if="!leftCollapsed" class="fec-cat-name">{{ cat.label }}</span>
              </div>
              <span v-if="!leftCollapsed" class="msi fec-cat-arr" :class="{ 'fec-cat-arr--open': openCats[cat.key] }" style="font-size:15px;color:#94a3b8">expand_more</span>
            </div>

            <!-- Expanded list -->
            <div v-if="!leftCollapsed && openCats[cat.key]" class="fec-comp-list">
              <div
                v-for="tool in cat.items" :key="tool.id"
                class="fec-comp-item"
                draggable="true"
                @dragstart="onCompDragStart($event, tool)"
                :title="tool.name">
                <div class="fec-comp-ico" :style="{ background: cat.bg, color: cat.color }">
                  <span class="msi" style="font-size:14px">{{ tool.icon }}</span>
                </div>
                <div class="fec-comp-text">
                  <span class="fec-comp-name">{{ tool.name }}</span>
                  <span class="fec-comp-sub">{{ tool.subtitle }}</span>
                </div>
              </div>
            </div>

            <!-- Collapsed: only icons -->
            <div v-if="leftCollapsed" class="fec-comp-icons">
              <div
                v-for="tool in cat.items" :key="tool.id"
                class="fec-comp-ico fec-comp-ico--sm"
                :style="{ background: cat.bg, color: cat.color }"
                draggable="true"
                @dragstart="onCompDragStart($event, tool)"
                :title="tool.name">
                <span class="msi" style="font-size:13px">{{ tool.icon }}</span>
              </div>
            </div>
          </div>
        </template>

        <div v-if="toolsByCategory.length === 0 && !leftCollapsed" class="fec-no-tools">
          <span class="msi" style="font-size:28px;color:#cbd5e1">construction</span>
          <span>Sin herramientas<br>para este diagrama</span>
        </div>
      </div>
    </aside>

    <!-- ── Canvas Area ─────────────────────────────────────────────────────── -->
    <main
      class="fec-canvas-area"
      ref="canvasAreaRef"
      @wheel.prevent="onWheel"
      @mousedown="onCanvasMousedown"
      @dragover.prevent="onDragOver"
      @dragleave="isDragOver = false"
      @drop.prevent="onDrop"
      @click="onCanvasClick">

      <!-- Floating Toolbar (draggable) -->
      <div
        v-if="!readOnly"
        class="fec-float-bar"
        :style="{ left: fbarPos.x + 'px', top: fbarPos.y + 'px' }"
        @mousedown.stop="onFbarMousedown">
        <span class="msi fec-fbar-handle" style="font-size:17px;color:#94a3b8;cursor:grab">drag_indicator</span>
        <div class="fec-fsep"></div>
        <button class="fec-tbtn" @click.stop="zoomIn" title="Zoom In"><span class="msi" style="font-size:18px">zoom_in</span></button>
        <span class="fec-zoom-pct">{{ Math.round(zoom * 100) }}%</span>
        <button class="fec-tbtn" @click.stop="zoomOut" title="Zoom Out"><span class="msi" style="font-size:18px">zoom_out</span></button>
        <div class="fec-fsep"></div>
        <button class="fec-tbtn" :class="{ 'fec-tbtn--on': snapToGrid }" @click.stop="snapToGrid = !snapToGrid" title="Snap to grid">
          <span class="msi" style="font-size:18px">grid_on</span>
        </button>
        <button class="fec-tbtn" @click.stop="centerView" title="Centrar vista">
          <span class="msi" style="font-size:18px">center_focus_strong</span>
        </button>
        <button class="fec-tbtn" @click.stop="fitView" title="Ajustar a pantalla">
          <span class="msi" style="font-size:18px">fit_screen</span>
        </button>
      </div>

      <!-- Drop hint overlay -->
      <div v-if="isDragOver" class="fec-drop-hint">
        <span class="msi" style="font-size:32px;color:#2563eb">add_circle</span>
        <span>Soltar herramienta aquí</span>
      </div>

      <!-- Canvas container (pan + zoom transform) -->
      <div
        class="fec-canvas"
        ref="canvasRef"
        :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})`, transformOrigin: '0 0', width: CANVAS_W + 'px', height: CANVAS_H + 'px' }">

        <!-- Notes (Background Layer) -->
        <div
          v-for="note in notes" :key="note.id"
          class="fec-node fec-node--annotations"
          :class="{ 'fec-node--sel': selectedNote?.id === note.id }"
          :style="{
            left: note.x + 'px',
            top: note.y + 'px',
            width: (note.props.width || 240) + 'px',
            height: (note.props.height || 120) + 'px',
            background: note.props.color || '#fef9c3',
            borderColor: darkenColor(note.props.color || '#fef9c3'),
            zIndex: selectedNote?.id === note.id ? 10 : 1,
            pointerEvents: 'auto'
          }"
          @mousedown.stop="onNoteMousedown($event, note)"
          @click.stop="selectNote(note)">
          
          <div class="fec-note-body">
            <!-- Styling Toolbar -->
            <div v-if="(selectedNote?.id === note.id || editingNoteId === note.id) && !readOnly" class="fec-note-toolbar" @mousedown.stop @click.stop>
              <div class="fec-note-palette">
                <button v-for="c in ['#fef9c3', '#dbeafe', '#dcfce7', '#fce7f3', '#f1f5f9']" 
                  :key="c" class="fec-note-color" :style="{ background: c, borderColor: darkenColor(c) }"
                  @click="changeNoteColor(note, c)"></button>
              </div>
              <div class="fec-note-tsep"></div>
              <button class="fec-note-tbtn" @click="changeNoteFontSize(note, -1)"><span class="msi" style="font-size:14px">remove</span></button>
              <span class="fec-note-tsize">{{ parseInt(note.props.fontSize || 13) }}</span>
              <button class="fec-note-tbtn" @click="changeNoteFontSize(note, 1)"><span class="msi" style="font-size:14px">add</span></button>
              <div class="fec-note-tsep"></div>
              <button class="fec-note-tbtn fec-note-tbtn--del" @click="deleteSelectedNote" title="Eliminar nota"><span class="msi" style="font-size:14px">delete</span></button>
            </div>

            <textarea
              v-if="editingNoteId === note.id"
              v-model="note.props.content"
              class="fec-note-ta"
              :style="{ fontSize: note.props.fontSize || '13px' }"
              @blur="editingNoteId = null"
              @mousedown.stop
              v-focus
            ></textarea>
            <div
              v-else
              class="fec-note-content"
              :style="{ fontSize: note.props.fontSize || '13px' }"
              v-html="renderMarkdown(note.props.content || '')"
              @dblclick="editingNoteId = note.id"
            ></div>

            <!-- Resize Handle -->
            <div v-if="!readOnly" class="fec-note-resizer" @mousedown.stop="onNoteResizeStart($event, note)">
              <span class="msi">south_east</span>
            </div>
          </div>
        </div>

        <!-- SVG layer: connections -->
        <svg :width="CANVAS_W" :height="CANVAS_H" style="position:absolute;top:0;left:0;overflow:visible">
          <defs>
            <marker id="fec-arr" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L0,8 L10,4 z" fill="#94a3b8" />
            </marker>
            <marker id="fec-arr-sel" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L0,8 L10,4 z" fill="#2563eb" />
            </marker>
            <marker id="fec-arr-active" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L0,8 L10,4 z" fill="#22c55e" />
            </marker>
          </defs>
          <!-- Connections -->
          <path
            v-for="conn in connections"
            :key="conn.id"
            :d="connPath(conn)"
            class="fec-conn"
            :class="{ 'fec-conn--active': (readOnly ? nodeLogsMap[conn.from]?.status : nodeExecStatus[conn.from]) === 'success' }"
            :stroke="selectedConn === conn.id || hoveredConn === conn.id ? '#2563eb' : ((readOnly ? nodeLogsMap[conn.from]?.status : nodeExecStatus[conn.from]) === 'success' ? '#22c55e' : '#94a3b8')"
            :stroke-width="selectedConn === conn.id ? 2.5 : ((readOnly ? nodeLogsMap[conn.from]?.status : nodeExecStatus[conn.from]) === 'success' ? 3 : 2)"
            fill="none"
            :marker-end="selectedConn === conn.id || hoveredConn === conn.id ? 'url(#fec-arr-sel)' : ((readOnly ? nodeLogsMap[conn.from]?.status : nodeExecStatus[conn.from]) === 'success' ? 'url(#fec-arr-active)' : 'url(#fec-arr)')"
            style="cursor:pointer"
            @mouseenter="hoveredConn = conn.id"
            @mouseleave="hoveredConn = null"
            @click.stop="selectedConn = selectedConn === conn.id ? null : conn.id"
          />
          <!-- Temp connection while drawing -->
          <path
            v-if="tempConn"
            :d="tempConn"
            stroke="#2563eb"
            stroke-width="2"
            stroke-dasharray="6 3"
            fill="none"
            pointer-events="none"
          />
        </svg>

        <!-- Nodes -->
        <div
          v-for="node in nodes" :key="node.id"
          class="fec-node"
          :class="[
            `fec-node--${node.category}`, 
            { 
              'fec-node--sel': selectedNode?.id === node.id,
              'fec-node--executing': (readOnly ? nodeLogsMap[node.id]?.status : nodeExecStatus[node.id]) === 'running',
              'fec-node--success':   (readOnly ? nodeLogsMap[node.id]?.status : nodeExecStatus[node.id]) === 'success',
              'fec-node--error':     (readOnly ? nodeLogsMap[node.id]?.status : nodeExecStatus[node.id]) === 'error'
            }
          ]"
          :style="{ 
            left: node.x + 'px', 
            top: node.y + 'px', 
            '--nc': getCatColor(node.category), 
            '--nb': getCatBg(node.category)
          }"
          @mousedown.stop="onNodeMousedown($event, node)"
          @mouseenter="hoveredNode = node"
          @mouseleave="hoveredNode = null"
          @click.stop="selectNode(node)">

          <!-- Node status badge -->
          <div v-if="(readOnly ? nodeLogsMap[node.id]?.status : nodeExecStatus[node.id]) && (readOnly ? nodeLogsMap[node.id]?.status : nodeExecStatus[node.id]) !== 'running'" 
               class="fec-node-badge" 
               :class="`fec-node-badge--${readOnly ? nodeLogsMap[node.id]?.status : nodeExecStatus[node.id]}`">
            <span class="msi">{{ (readOnly ? nodeLogsMap[node.id]?.status : nodeExecStatus[node.id]) === 'success' ? 'check_circle' : 'cancel' }}</span>
          </div>

          <!-- Node duration badge (left) -->
          <div v-if="readOnly && nodeLogsMap[node.id]" class="fec-node-badge--left" title="Tiempo de ejecución">
            {{ formatDuration(nodeLogsMap[node.id].duration) }}
          </div>

          <!-- Node Tooltip (Ficha) -->
          <div v-if="readOnly && hoveredNode?.id === node.id && nodeLogsMap[node.id]" class="fec-node-tooltip">
            <div class="fec-tooltip-hdr">Detalles de Ejecución</div>
            <div class="fec-tooltip-title">{{ node.label }}</div>
            
            <div class="fec-tooltip-status">
              <span :class="['fec-status-badge', nodeLogsMap[node.id].status]">
                <span class="msi">{{ nodeLogsMap[node.id].status === 'success' ? 'check_circle' : 'cancel' }}</span>
                {{ nodeLogsMap[node.id].status === 'success' ? 'Completado' : 'Fallido' }}
              </span>
            </div>

            <div class="fec-tooltip-grid">
              <div class="fec-tooltip-row">
                <span class="msi start">play_arrow</span>
                <div>
                  <p class="fec-tooltip-label">Inicio</p>
                  <p class="fec-tooltip-val">{{ formatDateTime(nodeLogsMap[node.id].start_time) }}</p>
                </div>
              </div>
              <div class="fec-tooltip-row">
                <span class="msi end">stop</span>
                <div>
                  <p class="fec-tooltip-label">Fin</p>
                  <p class="fec-tooltip-val">{{ formatDateTime(nodeLogsMap[node.id].end_time) }}</p>
                </div>
              </div>
            </div>

            <div class="fec-tooltip-footer">
              <span class="msi">timer</span>
              <span>Duración: <strong>{{ formatDuration(nodeLogsMap[node.id].duration) }}</strong></span>
            </div>
          </div>

          <div v-if="!readOnly && node.category !== 'source'" class="fec-port fec-port--in"
            @mousedown.stop="onPortMousedown($event, node, 'in')"
            @mouseup="onPortMouseup($event, node, 'in')">
          </div>

          <div class="fec-node-hdr">
            <div class="fec-node-hdr-ico">
              <span class="msi" style="font-size:13px">{{ getToolByType(node.toolType)?.icon || 'circle' }}</span>
            </div>
            <span class="fec-node-lbl" :title="node.label">{{ node.label }}</span>
          </div>
          <div class="fec-node-bdy">
            <span class="fec-node-tag">{{ node.toolType }}</span>
            <span v-if="node.props?.table || node.props?.schema" class="fec-node-meta">
              {{ [node.props.schema, node.props.table].filter(Boolean).join('.') }}
            </span>
            <span v-else-if="node.props?.url" class="fec-node-meta">{{ node.props.url }}</span>
          </div>

          <div v-if="!readOnly && node.category !== 'destination' && node.category !== 'notification'" class="fec-port fec-port--out"
            @mousedown.stop="onPortMousedown($event, node, 'out')"
            @mouseup="onPortMouseup($event, node, 'out')">
          </div>
        </div>
      </div>

      <!-- Connection action bar -->
      <div v-if="selectedConn" class="fec-conn-bar">
        <span class="fec-conn-lbl">Conexión seleccionada</span>
        <button class="fec-conn-del" @click="deleteConn(selectedConn)">
          <span class="msi" style="font-size:15px">delete</span>Eliminar
        </button>
      </div>
    </main>

    <!-- ── Right Panel: Properties ─────────────────────────────────────────── -->
    <aside v-if="!readOnly" class="fec-right" :class="{ 'fec-right--collapsed': rightCollapsed, 'fec-right--resizing': isResizingRight }" :style="{ width: rightCollapsed ? '24px' : (hasWideMode ? Math.max(500, rightWidth) : rightWidth) + 'px' }">
      <div v-if="!rightCollapsed" class="fec-resizer" @mousedown.stop="onResizeMousedown"></div>
      <button class="fec-toggle fec-toggle--right" @click="rightCollapsed = !rightCollapsed" :title="rightCollapsed ? 'Expandir' : 'Contraer'">
        <span class="msi">{{ rightCollapsed ? 'chevron_left' : 'chevron_right' }}</span>
      </button>

      <div v-if="!rightCollapsed" class="fec-right-inner">

        <!-- Tab Switcher -->
        <div class="fec-tabs" v-if="!selectedNode">
          <button class="fec-tab" :class="{ active: rightTab === 'props' }" @click="rightTab = 'props'">
            <span class="msi" style="font-size:16px">settings</span>Propiedades
          </button>
          <button class="fec-tab" :class="{ active: rightTab === 'history' }" @click="loadHistory">
            <span class="msi" style="font-size:16px">history</span>Historial
          </button>
        </div>

        <!-- ── Flow properties ── -->
        <template v-if="!selectedNode && rightTab === 'props'">
          <div class="fec-props-hdr">
            <span class="msi" style="font-size:20px;color:#2563eb">settings</span>
            <div>
              <p class="fec-props-title">Propiedades del Diagrama</p>
              <p class="fec-props-sub">{{ diagramTypeLabel }}</p>
            </div>
          </div>

          <div class="fec-prop-g">
            <label class="fec-prop-l">Nombre</label>
            <input v-model="metadata.name" class="fec-prop-i" />
          </div>
          <div class="fec-prop-g">
            <label class="fec-prop-l">Descripción</label>
            <textarea v-model="metadata.description" class="fec-prop-ta" rows="3"></textarea>
          </div>
          <div class="fec-prop-g">
            <label class="fec-prop-l">Estado</label>
            <div class="fec-sel-wrap">
              <select v-model="metadata.status" class="fec-prop-sel">
                <option value="active">Activo</option>
                <option value="scheduled">Programado</option>
                <option value="paused">Pausado</option>
                <option value="draft">Draft</option>
              </select>
              <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
            </div>
          </div>

          <template v-for="(def, key) in diagramMetaPropDefs" :key="key">
            <div class="fec-prop-g">
              <label class="fec-prop-l">{{ def.label }}</label>
              <div v-if="def.type === 'select'" class="fec-sel-wrap">
                <select v-model="metadata[key]" class="fec-prop-sel">
                  <option v-for="o in def.options" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
                <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
              </div>
              <input v-else v-model="metadata[key]" class="fec-prop-i" :placeholder="def.placeholder || ''" />
            </div>
          </template>

          <div class="fec-flow-stats">
            <div class="fec-stat-row"><span class="msi" style="font-size:15px;color:#64748b">hub</span><span>{{ nodes.length }} nodos</span></div>
            <div class="fec-stat-row"><span class="msi" style="font-size:15px;color:#64748b">device_hub</span><span>{{ connections.length }} conexiones</span></div>
          </div>
        </template>

        <!-- ── History ── -->
        <template v-if="!selectedNode && rightTab === 'history'">
          <div class="fec-history">
            <div v-if="historyLoading" class="fec-history-loading">
              <span class="msi spin">sync</span> Cargando historial...
            </div>
            <div v-else-if="history.length === 0" class="fec-history-empty">
              No hay ejecuciones registradas.
            </div>
            <div v-else class="fec-history-list">
              <div v-for="exec in history" :key="exec.id" class="fec-history-item" @click="loadExecutionLogs(exec.id)">
                <div class="fec-hi-header">
                  <span class="fec-hi-status" :class="`fec-hi-status--${exec.status}`"></span>
                  <span class="fec-hi-date">{{ formatDateTime(exec.created_at) }}</span>
                  <span class="fec-hi-duration">{{ exec.duration_ms }}ms</span>
                </div>
                <div class="fec-hi-footer">
                  <span class="fec-hi-id">{{ exec.id }}</span>
                  <span class="msi" style="font-size:14px">chevron_right</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Note properties ── -->
        <template v-else-if="selectedNote">
          <div class="fec-props-hdr">
            <div class="fec-props-node-ico" style="background:#fef9c3;color:#854d0e">
              <span class="msi" style="font-size:18px">sticky_note_2</span>
            </div>
            <div style="flex:1">
              <p class="fec-props-title">Propiedades de Nota</p>
              <p class="fec-props-sub">Anotación de canvas</p>
            </div>
            <button class="fec-close-btn" @click="selectedNote = null"><span class="msi" style="font-size:15px">close</span></button>
          </div>
          
          <div class="fec-prop-g">
            <label class="fec-prop-l">Color</label>
            <div class="fec-note-palette" style="padding: 4px 0;">
              <button v-for="c in ['#fef9c3', '#dbeafe', '#dcfce7', '#fce7f3', '#f1f5f9']" 
                :key="c" class="fec-note-color" 
                :style="{ background: c, borderColor: darkenColor(c), transform: selectedNote.props.color === c ? 'scale(1.2)' : 'none' }"
                @click="changeNoteColor(selectedNote, c)"></button>
            </div>
          </div>
          
          <div class="fec-prop-g">
            <label class="fec-prop-l">Tamaño de Fuente</label>
            <div style="display:flex;align-items:center;gap:8px;">
              <button class="fec-note-tbtn" style="border:1px solid #e2e8f0;background:#fff;" @click="changeNoteFontSize(selectedNote, -1)"><span class="msi" style="font-size:14px">remove</span></button>
              <span class="fec-note-tsize">{{ parseInt(selectedNote.props.fontSize || 13) }}px</span>
              <button class="fec-note-tbtn" style="border:1px solid #e2e8f0;background:#fff;" @click="changeNoteFontSize(selectedNote, 1)"><span class="msi" style="font-size:14px">add</span></button>
            </div>
          </div>

          <div class="fec-prop-g">
            <label class="fec-prop-l">Contenido (Markdown)</label>
            <textarea v-model="selectedNote.props.content" class="fec-prop-ta" rows="8" placeholder="# Titulo..."></textarea>
          </div>

          <div class="fec-node-del-wrap">
            <button class="fec-node-del-btn" @click="deleteSelectedNote">
              <span class="msi" style="font-size:15px">delete</span>Eliminar nota
            </button>
          </div>
        </template>

        <!-- ── Node properties ── -->
        <template v-else-if="selectedNode">
          <div class="fec-props-hdr">
            <div class="fec-props-node-ico" :style="{ background: getCatBg(selectedNode.category), color: getCatColor(selectedNode.category) }">
              <span class="msi" style="font-size:18px">{{ getToolByType(selectedNode.toolType)?.icon || 'circle' }}</span>
            </div>
            <div style="flex:1;min-width:0">
              <p class="fec-props-title" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ selectedNode.label }}</p>
              <p class="fec-props-sub">{{ getToolByType(selectedNode.toolType)?.name || selectedNode.toolType }}</p>
            </div>
            <button class="fec-close-btn" @click="selectedNode = null"><span class="msi" style="font-size:15px">close</span></button>
          </div>

          <div class="fec-prop-g">
            <label class="fec-prop-l">Etiqueta</label>
            <input v-model="selectedNode.label" class="fec-prop-i" />
          </div>

          <!-- ── Connection binding (source & destination nodes only) ── -->
          <template v-if="isConnectable(selectedNode.category)">
            <div class="fec-divider"><span>Conexión de Datos</span></div>

            <!-- Connection Type -->
            <div class="fec-prop-g">
              <label class="fec-prop-l">Tipo de Conexión</label>
              <div class="fec-sel-wrap">
                <select
                  v-model="selectedNode.props.connection_type"
                  class="fec-prop-sel"
                  @change="onConnectionTypeChange"
                >
                  <option value="">— Seleccionar tipo —</option>
                  <option v-for="ct in CONN_TYPES" :key="ct.value" :value="ct.value">{{ ct.label }}</option>
                </select>
                <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
              </div>
            </div>

            <!-- Connection -->
            <div class="fec-prop-g">
              <label class="fec-prop-l">
                Conexión
                <span v-if="dataSrcLoading" class="fec-conn-spin">
                  <span class="msi spin" style="font-size:12px">sync</span>
                </span>
              </label>
              <div class="fec-sel-wrap">
                <select
                  v-model="selectedNode.props.connection_id"
                  class="fec-prop-sel"
                  :disabled="!selectedNode.props.connection_type || dataSrcLoading"
                  @change="onConnectionSelect"
                >
                  <option value="">— Seleccionar conexión —</option>
                  <option v-for="ds in filteredDataSources" :key="ds.id" :value="ds.id">{{ ds.name }}</option>
                </select>
                <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
              </div>
              <p v-if="selectedNode.props.connection_type && !dataSrcLoading && filteredDataSources.length === 0"
                 class="fec-conn-hint">
                Sin conexiones de tipo "{{ connTypeLabel(selectedNode.props.connection_type) }}"
              </p>
              <p v-if="selectedNode.props.connection_id" class="fec-conn-filled">
                <span class="msi" style="font-size:12px">check_circle</span>
                Propiedades completadas
              </p>
            </div>
          </template>

          <div class="fec-divider"><span>Propiedades del componente</span></div>

          <template v-for="(def, key) in visiblePropDefs" :key="key">
            <div class="fec-prop-g">
              <label class="fec-prop-l">
                {{ def.label }}
                <span v-if="dynamicLoading[key]" class="fec-conn-spin">
                  <span class="msi spin" style="font-size:12px">sync</span>
                </span>
              </label>
              
              <!-- Code Editor -->
              <CodeEditor 
                v-if="def.type === 'code'"
                v-model="selectedNode.props[key]"
                :language="def.language || 'javascript'"
                height="320px"
              />

              <!-- Textarea -->
              <textarea v-else-if="def.type === 'textarea'" v-model="selectedNode.props[key]" class="fec-prop-ta" :rows="def.rows || 3" :placeholder="def.placeholder || ''"></textarea>
              
              <!-- Select -->
              <div v-else-if="def.type === 'select'" class="fec-sel-wrap">
                <select v-model="selectedNode.props[key]" class="fec-prop-sel">
                  <option value="">— {{ def.placeholder || 'Seleccionar' }} —</option>
                  <option v-for="o in getSelectOptions(def)" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
                <span class="msi fec-sel-arr" style="font-size:17px">expand_more</span>
              </div>
              
              <!-- Dynamic Select with Refresh -->
              <div v-else-if="def.type === 'dynamic_select'" class="fec-dynamic-sel-wrap">
                <div class="fec-sel-with-refresh">
                  <select 
                    v-model="selectedNode.props[key]" 
                    class="fec-prop-sel"
                    :disabled="!canFetchDynamic(def) || dynamicLoading[key]"
                  >
                    <option value="">— {{ def.placeholder || 'Seleccionar' }} —</option>
                    <option v-for="opt in getOptionsForDef(def, key)" :key="typeof opt === 'string' ? opt : opt.name" :value="typeof opt === 'string' ? opt : opt.name">{{ typeof opt === 'string' ? opt : opt.name }}</option>
                  </select>
                  <button 
                    v-if="def.refreshable"
                    class="fec-refresh-btn"
                    :disabled="!canFetchDynamic(def) || dynamicLoading[key]"
                    @click="refreshDynamicOptions(def, key)"
                    :title="'Actualizar ' + def.label"
                  >
                    <span class="msi" :class="{ spin: dynamicLoading[key] }">refresh</span>
                  </button>
                </div>
                <p v-if="!canFetchDynamic(def)" class="fec-conn-hint">
                  Complete los campos requeridos primero
                </p>
              </div>
              
              <!-- Multi Select (for identity fields) -->
              <div v-else-if="def.type === 'multi_select'" class="fec-multi-sel-wrap">
                <div class="fec-sel-with-refresh" style="margin-bottom: 8px;">
                  <button
                    v-if="def.refreshable"
                    class="fec-refresh-btn"
                    :disabled="!canFetchDynamic(def) || dynamicLoading[key]"
                    @click="refreshDynamicOptions(def, key)"
                    :title="'Actualizar ' + def.label"
                  >
                    <span class="msi" :class="{ spin: dynamicLoading[key] }">refresh</span>
                  </button>
                </div>
                <p v-if="!canFetchDynamic(def)" class="fec-conn-hint">
                  Seleccione una tabla primero
                </p>
                <div v-else-if="getOptionsForDef(def, key).length === 0 && !dynamicLoading[key]" class="fec-conn-hint">
                  No hay columnas disponibles. Haga clic en refresh.
                </div>
                <div v-else class="fec-checkbox-list">
                  <label 
                    v-for="opt in getOptionsForDef(def, key)" 
                    :key="typeof opt === 'string' ? opt : opt.name"
                    class="fec-checkbox-item"
                  >
                    <input 
                      type="checkbox" 
                      :value="typeof opt === 'string' ? opt : opt.name"
                      v-model="selectedNode.props[key]"
                      class="fec-checkbox"
                    />
                    <span class="fec-checkbox-label">
                      {{ typeof opt === 'string' ? opt : opt.name }}
                      <span v-if="opt.type" class="fec-checkbox-meta">({{ opt.type }})</span>
                    </span>
                  </label>
                </div>
              </div>
              
              <!-- Default input -->
              <input v-else v-model="selectedNode.props[key]" class="fec-prop-i" :placeholder="def.placeholder || ''" />
            </div>
          </template>

          <div class="fec-node-del-wrap">
            <button class="fec-node-del-btn" @click="deleteSelectedNode">
              <span class="msi" style="font-size:15px">delete</span>Eliminar nodo
            </button>
          </div>
        </template>

      </div>
    </aside>

    <!-- ── Execution Console (Bottom Panel) ────────────────────────────────── -->
    <div v-if="showConsole" class="fec-bottom" :class="{ 'fec-bottom--resizing': isResizingBottom }" :style="{ height: bottomHeight + 'px' }">
      <div class="fec-resizer-v" @mousedown.stop="onResizeBottomMousedown"></div>
      <ExecutionConsole 
        :logs="execLogs" 
        :status="execStatus" 
        @close="showConsole = false"
        @clear="execLogs = []"
      />
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { CAT_META } from '@/stores/toolCatalog'
import { useAuthStore } from '@/stores/auth'
import CodeEditor from './CodeEditor.vue'
import ExecutionConsole from './ExecutionConsole.vue'
import { dataSourcesApi } from '@/services/api'
import keycloak from '@/services/keycloak'
import { CONN_TYPES, connTypeLabel as _connTypeLabel } from '@/constants/connectionTypes'

// ─── Markdown Configuration ───────────────────────────────────────────────────
marked.setOptions({
  gfm: true,
  breaks: true,
  headerIds: false,
  mangle: false
})

function renderMarkdown(content) {
  if (!content) return ''
  const rawHtml = marked.parse(content)
  return DOMPurify.sanitize(rawHtml)
}

function changeNoteColor(node, color) {
  if (!node.props) node.props = {}
  node.props.color = color
}

function changeNoteFontSize(node, delta) {
  if (!node.props) node.props = {}
  const current = parseInt(node.props.fontSize || 13)
  const next = Math.min(48, Math.max(8, current + delta))
  node.props.fontSize = next + 'px'
}

function darkenColor(hex) {
  if (!hex || hex[0] !== '#') return hex
  let r = parseInt(hex.slice(1, 3), 16)
  let g = parseInt(hex.slice(3, 5), 16)
  let b = parseInt(hex.slice(5, 7), 16)
  r = Math.max(0, Math.floor(r * 0.9))
  g = Math.max(0, Math.floor(g * 0.9))
  b = Math.max(0, Math.floor(b * 0.9))
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}

// ─── Props & Emits ────────────────────────────────────────────────────────────
const props = defineProps({
  diagramType:   { type: String,  required: true },
  tools:         { type: Array,   default: () => [] },
  diagramData:   { type: Object,  default: () => ({ nodes: [], connections: [], metadata: {} }) },
  flowId:        { type: String,  default: null },
  readOnly:      { type: Boolean, default: false },
  executionData: { type: Object,  default: null }
})
const emit = defineEmits(['save', 'dirty-change'])

const vFocus = {
  mounted: (el) => el.focus()
}

const authStore = useAuthStore()

// ─── Constants ────────────────────────────────────────────────────────────────
const CANVAS_W = 4000
const CANVAS_H = 3000
const NODE_W   = 210
const NODE_H   = 82
const GRID     = 20

// Extra metadata props per diagram type
const DIAGRAM_META_PROPS = {
  'data-integration': {
    type:     { label: 'Tipo',                  type: 'select', options: [{ value: 'Batch ETL', label: 'Batch ETL' }, { value: 'Real-time Stream', label: 'Real-time Stream' }, { value: 'CDC', label: 'CDC' }, { value: 'API Pull', label: 'API Pull' }] },
    cron_expression: { label: 'Programación (Cron)',    type: 'text',   placeholder: '0 6 * * *' },
    source:   { label: 'Sistema Origen',         type: 'text',   placeholder: 'ERP SAP' },
    target:   { label: 'Sistema Destino',        type: 'text',   placeholder: 'ODS PostgreSQL' },
  },
  'process-flow': {
    owner:    { label: 'Responsable',            type: 'text',   placeholder: 'Área / persona' },
    version:  { label: 'Versión',               type: 'text',   placeholder: '1.0' },
  },
  'data-quality': {
    severity: { label: 'Severidad por defecto',  type: 'select', options: [{ value: 'low', label: 'Baja' }, { value: 'medium', label: 'Media' }, { value: 'high', label: 'Alta' }, { value: 'critical', label: 'Crítica' }] },
    cron_expression: { label: 'Programación (Cron)',    type: 'text',   placeholder: '0 * * * *' },
  },
}

// ─── Diagram type helpers ─────────────────────────────────────────────────────
const diagramTypeLabel = computed(() => {
  const map = {
    'data-integration': 'Data Integration Flow',
    'process-flow':     'Process Flow',
    'data-quality':     'Data Quality',
  }
  return map[props.diagramType] || props.diagramType
})

const diagramMetaPropDefs = computed(() => DIAGRAM_META_PROPS[props.diagramType] || {})

// ─── Tool helpers ─────────────────────────────────────────────────────────────
function getToolByType(toolType) {
  const tool = props.tools.find(t => t.type === toolType) || null
  if (!tool) return null
  
  // Parse prop_defs and default_props if they are JSON strings
  const parsedTool = { ...tool }
  if (typeof parsedTool.prop_defs === 'string') {
    try {
      parsedTool.prop_defs = JSON.parse(parsedTool.prop_defs)
    } catch (e) {
      console.warn('Failed to parse prop_defs for tool:', tool.type, e)
      parsedTool.prop_defs = {}
    }
  }
  if (typeof parsedTool.default_props === 'string') {
    try {
      parsedTool.default_props = JSON.parse(parsedTool.default_props)
    } catch (e) {
      console.warn('Failed to parse default_props for tool:', tool.type, e)
      parsedTool.default_props = {}
    }
  }
  
  return parsedTool
}
function getNodePropDefs(toolType) {
  const tool = getToolByType(toolType)
  if (!tool?.prop_defs) return {}
  
  // Parse prop_defs if it's a JSON string
  return typeof tool.prop_defs === 'string' 
    ? JSON.parse(tool.prop_defs) 
    : tool.prop_defs
}
function hasCodeProp(toolType) {
  const defs = getNodePropDefs(toolType)
  return Object.values(defs).some(d => d.type === 'code')
}
function getCatColor(cat) { return CAT_META[cat?.toLowerCase()]?.color || '#64748b' }
function getCatBg(cat)    { return CAT_META[cat?.toLowerCase()]    || '#f8fafc' }

// ─── Data-source connection binding ──────────────────────────────────────────
// CONN_TYPES imported from @/constants/connectionTypes

const dataSources    = ref([])
const dataSrcLoading = ref(false)
const dataSrcLoaded  = ref(false)

// ─── Dynamic selector state ───────────────────────────────────────────────────
const dynamicOptionsCache = ref({})  // key: endpoint, value: options[]
const dynamicLoading = ref({})       // key: propKey, value: boolean

async function loadDataSources() {
  if (dataSrcLoaded.value) return
  dataSrcLoading.value = true
  try {
    dataSources.value = await dataSourcesApi.getAll()
    dataSrcLoaded.value = true
  } catch (e) {
    console.error('[FlowEditor] Failed to load data sources:', e)
  } finally {
    dataSrcLoading.value = false
  }
}

function isConnectable(cat) { return cat === 'source' || cat === 'destination' }
function connTypeLabel(v)   { return _connTypeLabel(v) }

const filteredDataSources = computed(() => {
  const type = selectedNode.value?.props?.connection_type
  if (!type) return []
  return dataSources.value.filter(ds => ds.type === type)
})

function onConnectionTypeChange() {
  if (!selectedNode.value) return
  selectedNode.value.props.connection_id = ''
  _clearConnFields()
}

function onConnectionSelect() {
  const node = selectedNode.value
  if (!node) return
  const ds = dataSources.value.find(d => d.id === node.props.connection_id)
  if (!ds) return
  const cfg = ds.connection_config || {}
  const FILL = ['host', 'port', 'username', 'password', 'database', 'schema', 'url', 'email', 'api_key', 'token']
  for (const key of FILL) {
    if (cfg[key] !== undefined && key in (node.props || {})) {
      node.props[key] = cfg[key]
    }
  }
}

function _clearConnFields() {
  const node = selectedNode.value
  if (!node) return
  const FILL = ['host', 'port', 'username', 'password', 'database', 'schema', 'url', 'email', 'api_key', 'token']
  for (const key of FILL) {
    if (key in (node.props || {})) node.props[key] = ''
  }
}

// ─── Dynamic selector helpers ────────────────────────────────────────────────

/**
 * Check if a property should be shown based on show_if condition
 */
function shouldShowProp(def) {
  if (!def.show_if) return true
  const { field, equals, not_equals } = def.show_if
  const nodeVal = selectedNode.value?.props?.[field]
  if (equals !== undefined) return nodeVal === equals
  if (not_equals !== undefined) return nodeVal !== not_equals
  return true
}

/**
 * Computed property definitions filtered by show_if conditions
 */
const visiblePropDefs = computed(() => {
  const defs = getNodePropDefs(selectedNode.value?.toolType)
  const visible = {}
  for (const [key, def] of Object.entries(defs)) {
    if (shouldShowProp(def)) {
      visible[key] = def
    }
  }
  return visible
})

/**
 * Get select options - handles options_source for data sources
 */
function getSelectOptions(def) {
  if (def.options_source === 'data_sources') {
    return dataSources.value
      .filter(ds => !def.filter_by_type || ds.type === def.filter_by_type)
      .map(ds => ({ value: ds.id, label: ds.name }))
  }
  return def.options || []
}

/**
 * Check if all dependencies are met for a dynamic selector
 */
function canFetchDynamic(def) {
  if (!selectedNode.value) return false
  const deps = Array.isArray(def.depends_on) ? def.depends_on : [def.depends_on]
  return deps.every(dep => {
    const val = selectedNode.value.props?.[dep]
    return val !== undefined && val !== '' && val !== null
  })
}

/**
 * Build endpoint URL with variable substitution
 */
function buildEndpoint(def) {
  if (!def.fetch_endpoint || !selectedNode.value) return null
  
  let endpoint = def.fetch_endpoint
  const deps = Array.isArray(def.depends_on) ? def.depends_on : [def.depends_on]
  
  for (const dep of deps) {
    const value = selectedNode.value.props?.[dep]
    if (!value) return null
    endpoint = endpoint.replace(`{${dep}}`, encodeURIComponent(value))
  }
  
  return endpoint
}

/**
 * Get options for a dynamic selector - triggers fetch if needed
 */
function getOptionsForDef(def, key) {
  // Trigger async fetch if conditions are met
  const endpoint = buildEndpoint(def)
  if (endpoint && !dynamicOptionsCache.value[endpoint] && !dynamicLoading.value[key]) {
    fetchDynamicOptions(def, key)
  }
  return dynamicOptionsCache.value[endpoint] || []
}

/**
 * Get dynamic options - returns cached or triggers fetch
 */
async function getDynamicOptions(def, key) {
  if (!canFetchDynamic(def)) return []
  
  const endpoint = buildEndpoint(def)
  if (!endpoint) return []
  
  // Auto-fetch on first view if not cached and not loading
  if (!dynamicOptionsCache.value[endpoint] && !dynamicLoading.value[key]) {
    await fetchDynamicOptions(def, key)
  }
  
  return dynamicOptionsCache.value[endpoint] || []
}

/**
 * Fetch dynamic options from API
 */
async function fetchDynamicOptions(def, key) {
  const endpoint = buildEndpoint(def)
  if (!endpoint) return
  
  // Check if keycloak is initialized and has a token
  if (!keycloak.token) {
    console.error(`Cannot fetch options for ${key}: No authentication token available`)
    dynamicOptionsCache.value[endpoint] = []
    return
  }
  
  // Refresh token if it will expire in less than 30 seconds
  if (keycloak.isTokenExpired(30)) {
    try {
      await keycloak.updateToken(30)
    } catch (err) {
      console.error('Failed to refresh token:', err)
      dynamicOptionsCache.value[endpoint] = []
      return
    }
  }
  
  dynamicLoading.value[key] = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}${endpoint}`, {
      headers: { 
        'Authorization': `Bearer ${keycloak.token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      console.error(`Failed to fetch options for ${key}: ${response.status}`)
      dynamicOptionsCache.value[endpoint] = []
      return
    }
    
    const data = await response.json()
    // Handle different response formats (tables vs columns)
    dynamicOptionsCache.value[endpoint] = data
  } catch (e) {
    console.error(`Error fetching options for ${key}:`, e)
    dynamicOptionsCache.value[endpoint] = []
  } finally {
    dynamicLoading.value[key] = false
  }
}

/**
 * Force refresh of dynamic options
 */
async function refreshDynamicOptions(def, key) {
  const endpoint = buildEndpoint(def)
  if (!endpoint) return
  
  // Clear cache to force refetch
  delete dynamicOptionsCache.value[endpoint]
  await fetchDynamicOptions(def, key)
}


// Group tools by category for left panel
const toolsByCategory = computed(() => {
  const map = {}
  for (const tool of props.tools) {
    if (!map[tool.category]) map[tool.category] = []
    map[tool.category].push(tool)
  }
  return Object.entries(map).map(([cat, items]) => ({
    key: cat,
    label: CAT_META[cat]?.label || cat,
    color: CAT_META[cat]?.color || '#64748b',
    bg:    CAT_META[cat]?.bg    || '#f8fafc',
    icon:  CAT_META[cat]?.icon  || 'category',
    items,
  }))
})

// ─── Diagram state (owned by this component) ──────────────────────────────────
const nodes       = ref([])
const connections = ref([])
const notes       = ref([])
const metadata    = ref({})

// ─── Dirty tracking ───────────────────────────────────────────────────────────
let savedSnapshot      = ''
let initializingFromProp = false

function takeSnapshot() {
  return JSON.stringify({ nodes: nodes.value, connections: connections.value, notes: notes.value, metadata: metadata.value })
}

// Initialize from prop
watch(() => props.diagramData, (data) => {
  initializingFromProp = true
  
  const rawNodes = data?.nodes ? JSON.parse(JSON.stringify(data.nodes)) : []
  // Separate nodes from notes if mixed (backward compatibility)
  const parsedNodes = rawNodes.filter(n => n.category?.toLowerCase() !== 'annotations')
  const legacyNotes = rawNodes.filter(n => n.category?.toLowerCase() === 'annotations')

  connections.value = data?.connections ? JSON.parse(JSON.stringify(data.connections)) : []
  notes.value       = data?.notes       ? JSON.parse(JSON.stringify(data.notes))       : []
  
  if (legacyNotes.length > 0) {
    notes.value.push(...legacyNotes)
  }

  metadata.value    = data?.metadata    ? JSON.parse(JSON.stringify(data.metadata))    : {}
  
  // Merge node props with tool defaults for backward compatibility
  for (const node of parsedNodes) {
    const tool = props.tools.find(t => t.type === node.toolType)
    if (tool?.default_props) {
      const defaults = typeof tool.default_props === 'string' 
        ? JSON.parse(tool.default_props) 
        : tool.default_props
      
      if (!node.props) node.props = {}
      for (const [key, value] of Object.entries(defaults)) {
        if (!(key in node.props)) {
          node.props[key] = value
        }
      }
    }
  }
  nodes.value = parsedNodes
  
  nextTick(() => {
    savedSnapshot = takeSnapshot()
    initializingFromProp = false
    emit('dirty-change', false)
  })
}, { immediate: true })

watch([nodes, connections, notes, metadata], () => {
  if (initializingFromProp) return
  const dirty = takeSnapshot() !== savedSnapshot
  emit('dirty-change', dirty)
}, { deep: true })

// ─── UI state ─────────────────────────────────────────────────────────────────
const leftCollapsed  = ref(false)
const rightCollapsed = ref(false)
const rightWidth     = ref(272)
const isResizingRight = ref(false)
const bottomHeight    = ref(240)
const isResizingBottom = ref(false)
const isResizingNote   = ref(false)
const resizingNote     = ref(null)
const openCats       = ref(Object.fromEntries(Object.keys(CAT_META).map(k => [k, true])))
const editingNoteId  = ref(null)
const selectedNode   = ref(null)
const selectedNote   = ref(null)
const selectedConn   = ref(null)
const hoveredNode    = ref(null)
const hoveredConn    = ref(null)

// Flag to prevent cascading clears during initial node selection
let isInitializingNodeSelection = false

function onResizeMousedown(e) {
  isResizingRight.value = true
}

function onResizeBottomMousedown(e) {
  isResizingBottom.value = true
}

function onNoteResizeStart(e, note) {
  isResizingNote.value = true
  resizingNote.value = note
  const pos = getCanvasPos(e.clientX, e.clientY)
  nodeDragStart = { 
    sx: pos.x, 
    sy: pos.y, 
    nw: note.props.width || 240, 
    nh: note.props.height || 120 
  }
}

const hasWideMode = computed(() => selectedNode.value && hasCodeProp(selectedNode.value.toolType))

// Lazy-load data sources + ensure connection props exist when a connectable node is selected
watch(selectedNode, (node) => {
  if (!node) return
  
  // Set flag to prevent cascading watchers from clearing values during initialization
  isInitializingNodeSelection = true
  
  // Initialize props object if missing
  if (!node.props) node.props = {}
  
  // Merge with tool's default_props to ensure all properties exist
  const tool = getToolByType(node.toolType)
  if (tool?.default_props) {
    const defaults = typeof tool.default_props === 'string' 
      ? JSON.parse(tool.default_props) 
      : tool.default_props
    
    for (const [key, value] of Object.entries(defaults)) {
      if (!(key in node.props)) {
        node.props[key] = value
      }
    }
  }
  
  // Load data sources for connectable nodes
  if (isConnectable(node.category)) {
    loadDataSources()
    if (!('connection_type' in node.props)) node.props.connection_type = ''
    if (!('connection_id'   in node.props)) node.props.connection_id   = ''
  }
  
  // Clear flag after initialization is complete
  nextTick(() => {
    isInitializingNodeSelection = false
  })
})

// ─── Cascading clear watchers ─────────────────────────────────────────────────

// Watch for connection_id changes - clears table and identity_fields
watch(() => selectedNode.value?.props?.connection_id, (newVal, oldVal) => {
  // Skip if we're initializing the node selection (loading saved values)
  if (isInitializingNodeSelection) return
  // Skip on initial watch (when oldVal is undefined and newVal is the saved value)
  if (oldVal === undefined) return
  if (newVal !== oldVal && selectedNode.value) {
    selectedNode.value.props.table = ''
    selectedNode.value.props.identity_fields = []
    // Clear cache for table options
    Object.keys(dynamicOptionsCache.value).forEach(key => {
      if (key.includes('/tables?')) {
        delete dynamicOptionsCache.value[key]
      }
    })
  }
})

// Watch for table changes - clears identity_fields
watch(() => selectedNode.value?.props?.table, (newVal, oldVal) => {
  // Skip if we're initializing the node selection (loading saved values)
  if (isInitializingNodeSelection) return
  // Skip on initial watch (when oldVal is undefined and newVal is the saved value)
  if (oldVal === undefined) return
  if (newVal !== oldVal && selectedNode.value) {
    selectedNode.value.props.identity_fields = []
    // Clear cache for column options
    Object.keys(dynamicOptionsCache.value).forEach(key => {
      if (key.includes('/columns')) {
        delete dynamicOptionsCache.value[key]
      }
    })
  }
})

// Watch for schema changes - clears table and identity_fields
watch(() => selectedNode.value?.props?.schema, (newVal, oldVal) => {
  // Skip if we're initializing the node selection (loading saved values)
  if (isInitializingNodeSelection) return
  // Skip on initial watch (when oldVal is undefined and newVal is the saved value)
  if (oldVal === undefined) return
  if (newVal !== oldVal && selectedNode.value) {
    selectedNode.value.props.table = ''
    selectedNode.value.props.identity_fields = []
    // Clear all table/column caches
    Object.keys(dynamicOptionsCache.value).forEach(key => {
      delete dynamicOptionsCache.value[key]
    })
  }
})
const snapToGrid     = ref(true)
const isDragOver     = ref(false)
const zoom           = ref(1)
const panX           = ref(40)
const panY           = ref(40)
const fbarPos        = ref({ x: 16, y: 16 })
const tempConn       = ref(null)
const canvasAreaRef  = ref(null)

// ─── Execution State ──────────────────────────────────────────────────────────
const showConsole    = ref(false)
const execLogs       = ref([])
const execStatus     = ref('idle')
const nodeExecStatus = ref({}) // mapping of node_id -> status
let ws               = null

const nodeLogsMap = computed(() => {
  if (!props.executionData?.logs) return {}
  return Object.fromEntries(props.executionData.logs.map(log => [log.node_id, log]))
})

function formatDuration(ms) {
  if (ms === undefined || ms === null) return ''
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const rightTab       = ref('props') // props, history
const history        = ref([])
const historyLoading = ref(false)

async function loadHistory() {
  if (!props.flowId) return
  rightTab.value = 'history'
  historyLoading.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/integration-flows/${props.flowId}/executions`, {
      headers: { 'Authorization': `Bearer ${window.keycloak?.token}` }
    })
    history.value = await response.json()
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    historyLoading.value = false
  }
}

async function loadExecutionLogs(execId) {
  showConsole.value = true
  execStatus.value = 'idle'
  execLogs.value = [{ type: 'info', message: `Cargando logs de ejecución ${execId}...` }]
  
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/integration-flows/executions/${execId}/logs`, {
      headers: { 'Authorization': `Bearer ${window.keycloak?.token}` }
    })
    const data = await response.json()
    execLogs.value = data.logs.map(l => ({ ...l, timestamp: new Date(data.created_at) }))
    if (data.result_data) {
      execLogs.value.push({ type: 'result', data: data.result_data, timestamp: new Date() })
    }
    execStatus.value = data.status
  } catch (e) {
    execLogs.value.push({ type: 'error', message: 'Error al cargar logs' })
  }
}

function formatDateTime(val) {
  if (!val) return '—'
  const date = new Date(val)
  if (isNaN(date.getTime())) return val
  return date.toLocaleString()
}

function runFlow() {
  if (!props.flowId) {
    alert('Guarde el flujo antes de ejecutarlo')
    return
  }
  
  showConsole.value    = true
  execStatus.value     = 'running'
  nodeExecStatus.value = {}
  execLogs.value       = [{ type: 'info', message: 'Iniciando conexión...', timestamp: new Date() }]
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  let host = 'localhost:8000'

  if (import.meta.env.VITE_API_URL) {
    // Remove protocol and trailing slashes
    host = import.meta.env.VITE_API_URL
      .replace('http://', '')
      .replace('https://', '')
      .replace('/api/v1', '')
    
    // Ensure no trailing slash
    if (host.endsWith('/')) host = host.slice(0, -1)
  } else {
    // Fallback to current location but different port if we are on dev port 3000
    host = window.location.host.replace(':3000', ':8000')
  }
    
  console.log(`[WebSocket] Connecting to: ${protocol}//${host}/api/v1/integration-flows/${props.flowId}/logs`)
  ws = new WebSocket(`${protocol}//${host}/api/v1/integration-flows/${props.flowId}/logs`)
  
  ws.onopen = () => {
    console.log('[WebSocket] Connection opened')
    execLogs.value.push({ type: 'info', message: 'Ejecución iniciada', timestamp: new Date() })
    ws.send(JSON.stringify({ 
      payload: {},
      user_id: authStore.user?.id
    }))
  }
  
  ws.onmessage = (event) => {
    console.log('[WebSocket] Message received:', event.data)
    const data = JSON.parse(event.data)
    
    if (data.type === 'node_status') {
      nodeExecStatus.value[data.node_id] = data.status
    } else if (data.type === 'status') {
      execStatus.value = data.success ? 'success' : 'error'
      execLogs.value.push({ 
        type: data.success ? 'info' : 'error', 
        message: `Fin de ejecución (Código: ${data.exit_code})`, 
        timestamp: new Date() 
      })
    } else {
      execLogs.value.push({
        ...data,
        timestamp: new Date()
      })
    }
  }
  
  ws.onerror = (err) => {
    console.error('[WebSocket] Error detected:', err)
    execStatus.value = 'error'
    execLogs.value.push({ type: 'error', message: 'Error de conexión WebSocket', timestamp: new Date() })
  }
  
  ws.onclose = (event) => {
    console.log(`[WebSocket] Connection closed (Code: ${event.code}, Reason: ${event.reason})`)
    if (execStatus.value === 'running') {
      execStatus.value = 'error'
      const reason = event.reason ? `: ${event.reason}` : ''
      execLogs.value.push({ 
        type: 'error', 
        message: `Conexión cerrada inesperadamente (Código ${event.code}${reason})`, 
        timestamp: new Date() 
      })
    }
  }
}

onBeforeUnmount(() => {
  if (ws) ws.close()
})

function toggleCat(key) { openCats.value[key] = !openCats.value[key] }

// ─── Drag state (non-reactive, performance-critical) ─────────────────────────
let isPanning       = false, panStart       = null
let isDraggingNode  = false, isDraggingNote = false, draggedNode = null, nodeDragStart = null
let isDraggingFbar  = false, fbarDragStart  = null
let hasDragged      = false
let isConnecting    = false, connectFrom    = null
let dragTool        = null  // tool being dragged from left panel

// ─── Helpers ──────────────────────────────────────────────────────────────────
function snapPos(x, y) {
  if (!snapToGrid.value) return { x, y }
  return { x: Math.round(x / GRID) * GRID, y: Math.round(y / GRID) * GRID }
}
function getCanvasPos(clientX, clientY) {
  const r = canvasAreaRef.value.getBoundingClientRect()
  return {
    x: (clientX - r.left - panX.value) / zoom.value,
    y: (clientY - r.top  - panY.value) / zoom.value,
  }
}

// ─── Connection paths ─────────────────────────────────────────────────────────
function connPath(conn) {
  const f = nodes.value.find(n => n.id === conn.from)
  const t = nodes.value.find(n => n.id === conn.to)
  if (!f || !t) return ''
  const x1 = f.x + NODE_W, y1 = f.y + NODE_H / 2
  const x2 = t.x,          y2 = t.y + NODE_H / 2
  const dx = Math.max(60, Math.abs(x2 - x1) * 0.45)
  return `M ${x1} ${y1} C ${x1+dx} ${y1}, ${x2-dx} ${y2}, ${x2} ${y2}`
}
function tempConnPath(fromNode, mx, my) {
  const r  = canvasAreaRef.value.getBoundingClientRect()
  const tx = (mx - r.left - panX.value) / zoom.value
  const ty = (my - r.top  - panY.value) / zoom.value
  const x1 = fromNode.x + NODE_W, y1 = fromNode.y + NODE_H / 2
  const dx = Math.max(40, Math.abs(tx - x1) * 0.4)
  return `M ${x1} ${y1} C ${x1+dx} ${y1}, ${tx-dx} ${ty}, ${tx} ${ty}`
}

// ─── Zoom / Pan ───────────────────────────────────────────────────────────────
function zoomIn()  { setZoom(zoom.value * 1.15) }
function zoomOut() { setZoom(zoom.value * 0.87) }
function setZoom(v) { zoom.value = Math.min(2.5, Math.max(0.15, v)) }

function onWheel(e) {
  const r = canvasAreaRef.value.getBoundingClientRect()
  const mx = e.clientX - r.left, my = e.clientY - r.top
  const f  = e.deltaY < 0 ? 1.1 : 0.9
  const nz = Math.min(2.5, Math.max(0.15, zoom.value * f))
  panX.value = mx - (mx - panX.value) * (nz / zoom.value)
  panY.value = my - (my - panY.value) * (nz / zoom.value)
  zoom.value = nz
}
function centerView() {
  if (!canvasAreaRef.value || nodes.value.length === 0) return
  const r = canvasAreaRef.value.getBoundingClientRect()
  const xs = nodes.value.map(n => n.x), ys = nodes.value.map(n => n.y)
  panX.value = r.width  / 2 - ((Math.min(...xs) + Math.max(...xs) + NODE_W) / 2) * zoom.value
  panY.value = r.height / 2 - ((Math.min(...ys) + Math.max(...ys) + NODE_H) / 2) * zoom.value
}
function fitView() {
  if (!canvasAreaRef.value || nodes.value.length === 0) return
  const r    = canvasAreaRef.value.getBoundingClientRect()
  const xs   = nodes.value.map(n => n.x), ys = nodes.value.map(n => n.y)
  const minX = Math.min(...xs), minY = Math.min(...ys)
  const maxX = Math.max(...xs) + NODE_W, maxY = Math.max(...ys) + NODE_H
  const pad  = 60
  const nz   = Math.min(1.5, Math.max(0.15, Math.min((r.width - pad*2) / (maxX - minX), (r.height - pad*2) / (maxY - minY))))
  zoom.value = nz
  panX.value = pad - minX * nz
  panY.value = pad - minY * nz
}

// ─── Canvas events ────────────────────────────────────────────────────────────
function onCanvasMousedown(e) {
  if (e.button !== 0) return
  isPanning  = true
  hasDragged = false
  panStart   = { mx: e.clientX, my: e.clientY, px: panX.value, py: panY.value }
}
function onCanvasClick() {
  if (!hasDragged) {
    selectedNode.value = null
    selectedNote.value = null
    selectedConn.value = null
  }
  hasDragged = false
}

// ─── Global move / up (on root element) ──────────────────────────────────────
function onGlobalMousemove(e) {
  if (isResizingRight.value) {
    const newWidth = window.innerWidth - e.clientX
    rightWidth.value = Math.max(272, Math.min(newWidth, window.innerWidth * 0.5))
    return
  }
  if (isResizingBottom.value) {
    const newHeight = window.innerHeight - e.clientY
    bottomHeight.value = Math.max(100, Math.min(newHeight, window.innerHeight * 0.8))
    return
  }
  if (isResizingNote.value && resizingNote.value) {
    const pos = getCanvasPos(e.clientX, e.clientY)
    const dw = pos.x - nodeDragStart.sx
    const dh = pos.y - nodeDragStart.sy
    resizingNote.value.props.width = Math.max(100, nodeDragStart.nw + dw)
    resizingNote.value.props.height = Math.max(100, nodeDragStart.nh + dh)
    return
  }
  if ((isDraggingNode || isDraggingNote) && draggedNode) {
    hasDragged = true
    const pos = getCanvasPos(e.clientX, e.clientY)
    const { x, y } = snapPos(nodeDragStart.nx + pos.x - nodeDragStart.sx, nodeDragStart.ny + pos.y - nodeDragStart.sy)
    draggedNode.x = Math.max(0, x)
    draggedNode.y = Math.max(0, y)
    return
  }
  if (isPanning && panStart) {
    const dx = e.clientX - panStart.mx, dy = e.clientY - panStart.my
    if (Math.abs(dx) + Math.abs(dy) > 3) hasDragged = true
    panX.value = panStart.px + dx
    panY.value = panStart.py + dy
    return
  }
  if (isDraggingFbar && fbarDragStart) {
    fbarPos.value = { x: fbarDragStart.tx + e.clientX - fbarDragStart.mx, y: fbarDragStart.ty + e.clientY - fbarDragStart.my }
    return
  }
  if (isConnecting && connectFrom && canvasAreaRef.value) {
    tempConn.value = tempConnPath(connectFrom, e.clientX, e.clientY)
  }
}
function onGlobalMouseup() {
  isResizingRight.value = false
  isResizingBottom.value = false
  isResizingNote.value = false
  resizingNote.value = null
  isDraggingNode = false; isDraggingNote = false; draggedNode = null; nodeDragStart = null
  isPanning = false; panStart = null
  isDraggingFbar = false; fbarDragStart = null
  isConnecting = false; connectFrom = null; tempConn.value = null
}

// ─── Node events ──────────────────────────────────────────────────────────────
function onNodeMousedown(e, node) {
  if (props.readOnly) return
  if (e.button !== 0) return
  isDraggingNode = true; draggedNode = node; hasDragged = false
  const pos = getCanvasPos(e.clientX, e.clientY)
  nodeDragStart = { sx: pos.x, sy: pos.y, nx: node.x, ny: node.y }
}
function onNoteMousedown(e, note) {
  if (props.readOnly) return
  if (e.button !== 0) return
  isDraggingNote = true; draggedNode = note; hasDragged = false
  const pos = getCanvasPos(e.clientX, e.clientY)
  nodeDragStart = { sx: pos.x, sy: pos.y, nx: note.x, ny: note.y }
}
function selectNode(node) {
  if (props.readOnly) return
  if (!hasDragged) { 
    selectedNode.value = node
    selectedNote.value = null
    selectedConn.value = null
    rightCollapsed.value = false 
  }
  hasDragged = false
}
function selectNote(note) {
  if (props.readOnly) return
  if (!hasDragged) {
    selectedNote.value = note
    selectedNode.value = null
    selectedConn.value = null
    rightCollapsed.value = false
  }
  hasDragged = false
}
function deleteSelectedNode() {
  if (props.readOnly) return
  if (!selectedNode.value) return
  const id = selectedNode.value.id
  nodes.value = nodes.value.filter(n => n.id !== id)
  connections.value = connections.value.filter(c => c.from !== id && c.to !== id)
  selectedNode.value = null
}
function deleteSelectedNote() {
  if (props.readOnly) return
  if (!selectedNote.value) return
  const id = selectedNote.value.id
  notes.value = notes.value.filter(n => n.id !== id)
  selectedNote.value = null
}

// ─── Port events ──────────────────────────────────────────────────────────────
function onPortMousedown(e, node, portType) {
  if (props.readOnly) return
  if (portType !== 'out') return
  isConnecting = true; connectFrom = node
  tempConn.value = tempConnPath(node, e.clientX, e.clientY)
}
function onPortMouseup(e, node, portType) {
  if (props.readOnly) return
  if (portType !== 'in' || !isConnecting || !connectFrom || connectFrom.id === node.id) return
  if (!connections.value.find(c => c.from === connectFrom.id && c.to === node.id)) {
    connections.value.push({ id: `c${Date.now()}`, from: connectFrom.id, to: node.id })
  }
  // cleanup happens in onGlobalMouseup (event bubbles there)
}

// ─── Floating toolbar drag ────────────────────────────────────────────────────
function onFbarMousedown(e) {
  isDraggingFbar = true
  fbarDragStart = { mx: e.clientX, my: e.clientY, tx: fbarPos.value.x, ty: fbarPos.value.y }
}

// ─── Connections ──────────────────────────────────────────────────────────────
function deleteConn(id) { connections.value = connections.value.filter(c => c.id !== id); selectedConn.value = null }

// ─── Drag & drop from left panel ─────────────────────────────────────────────
function onCompDragStart(e, tool) {
  dragTool = tool
  e.dataTransfer.effectAllowed = 'copy'
}
function onDragOver() { isDragOver.value = true }
function onDrop(e) {
  isDragOver.value = false
  if (!dragTool || !canvasAreaRef.value) return
  const pos = getCanvasPos(e.clientX, e.clientY)
  const { x, y } = snapPos(pos.x - NODE_W / 2, pos.y - NODE_H / 2)
  // Parse default_props if it's a JSON string
  const defaultProps = dragTool.default_props
    ? (typeof dragTool.default_props === 'string' ? JSON.parse(dragTool.default_props) : dragTool.default_props)
    : {}
  
  const newItem = {
    id:       `n${Date.now()}`,
    toolType: dragTool.type,
    category: dragTool.category,
    label:    dragTool.name,
    x: Math.max(0, x),
    y: Math.max(0, y),
    props: Object.fromEntries(Object.keys(dragTool.prop_defs || {}).map(k => [k, defaultProps[k] ?? ''])),
  }
  
  if (dragTool.category?.toLowerCase() === 'annotations') {
    if (!newItem.props.width) newItem.props.width = 240
    if (!newItem.props.height) newItem.props.height = 120
    notes.value.push(newItem)
  } else {
    nodes.value.push(newItem)
  }
  
  dragTool = null
}

// ─── Save ─────────────────────────────────────────────────────────────────────
function getCurrentDiagramData() {
  return {
    nodes:       JSON.parse(JSON.stringify(nodes.value)),
    connections: JSON.parse(JSON.stringify(connections.value)),
    notes:       JSON.parse(JSON.stringify(notes.value)),
    metadata:    JSON.parse(JSON.stringify(metadata.value)),
  }
}

function markSaved() {
  savedSnapshot = takeSnapshot()
  emit('dirty-change', false)
}

function save() {
  const data = getCurrentDiagramData()
  emit('save', data)
  markSaved()
}

defineExpose({ save, getCurrentDiagramData, markSaved, fitView, centerView, runFlow, execStatus })

onMounted(() => { setTimeout(fitView, 80) })
</script>

<style scoped>
/* Root */
.fec-root { display: flex; height: 100%; overflow: hidden; }

/* ── Left Panel ────────────────────────────────────────────────── */
.fec-left {
  width: 240px; background: #fff; border-right: 1px solid #e2e8f0;
  display: flex; flex-direction: column; flex-shrink: 0;
  transition: width 0.22s ease; position: relative; overflow: hidden;
}
.fec-left--collapsed { width: 52px; }

.fec-toggle {
  position: absolute; top: 12px; right: -12px; z-index: 10;
  width: 24px; height: 24px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: #64748b; box-shadow: 0 1px 4px rgba(15,23,42,0.1); transition: all 0.15s;
}
.fec-toggle:hover { background: #eff6ff; color: #2563eb; }
.fec-toggle .msi { font-size: 13px; }
.fec-toggle--right { right: auto; left: -12px; }

.fec-left-inner { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 4px 0 12px; }
.fec-left-inner::-webkit-scrollbar { width: 4px; }
.fec-left-inner::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }

.fec-left-head {
  display: flex; align-items: center; gap: 7px;
  padding: 10px 14px 8px;
}
.fec-panel-label { font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.07em; flex: 1; }
.fec-diagram-tag {
  font-size: 9px; font-weight: 600; color: #2563eb;
  background: #eff6ff; border-radius: 4px; padding: 2px 6px; white-space: nowrap;
}

.fec-cat { margin-bottom: 1px; }
.fec-cat-hdr {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 14px; cursor: pointer; transition: background 0.12s;
}
.fec-cat-hdr:hover { background: #f8fafc; }
.fec-cat-hdr-l { display: flex; align-items: center; gap: 8px; }
.fec-cat-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.fec-cat-name { font-size: 11px; font-weight: 600; color: #334155; }
.fec-cat-arr { transition: transform 0.2s; }
.fec-cat-arr--open { transform: rotate(180deg); }

.fec-comp-list { padding: 2px 8px 4px; }
.fec-comp-item {
  display: flex; align-items: center; gap: 8px; padding: 6px 8px;
  border-radius: 7px; cursor: grab; transition: background 0.12s; user-select: none;
}
.fec-comp-item:hover { background: #f1f5f9; }
.fec-comp-icons { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 4px 0; }
.fec-comp-ico {
  width: 28px; height: 28px; border-radius: 7px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.fec-comp-ico--sm { cursor: grab; }
.fec-comp-ico--sm:hover { filter: brightness(0.9); }
.fec-comp-name { display: block; font-size: 12px; font-weight: 500; color: #1e293b; line-height: 1.3; }
.fec-comp-sub  { display: block; font-size: 10px; color: #94a3b8; }
.fec-no-tools  { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 32px 16px; text-align: center; font-size: 12px; color: #94a3b8; }

/* ── Canvas Area ──────────────────────────────────────────────── */
.fec-canvas-area {
  flex: 1; position: relative; overflow: hidden;
  background-color: #f1f5f9;
  background-image: radial-gradient(circle, #cbd5e1 1.2px, transparent 1.2px);
  background-size: 20px 20px;
  cursor: default; user-select: none;
}
.fec-canvas { position: absolute; top: 0; left: 0; }

/* Floating bar */
.fec-float-bar {
  position: absolute; display: flex; align-items: center; gap: 2px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 4px 8px; box-shadow: 0 4px 16px rgba(15,23,42,0.1); z-index: 20;
}
.fec-fbar-handle { padding: 0 4px; }
.fec-fsep { width: 1px; height: 18px; background: #e2e8f0; margin: 0 4px; }
.fec-tbtn {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border: none; background: transparent; border-radius: 6px; cursor: pointer;
  color: #64748b; transition: all 0.12s;
}
.fec-tbtn:hover { background: #f1f5f9; color: #2563eb; }
.fec-tbtn--on { background: #eff6ff; color: #2563eb; }
.fec-zoom-pct { font-size: 11px; font-weight: 600; color: #475569; min-width: 34px; text-align: center; }

/* Drop hint */
.fec-drop-hint {
  position: absolute; inset: 0; z-index: 15; pointer-events: none;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
  background: rgba(37,99,235,0.05); border: 2px dashed #2563eb; border-radius: 12px; margin: 12px;
  font-size: 15px; font-weight: 600; color: #2563eb;
}

/* Nodes */
.fec-node {
  position: absolute; width: 210px; min-height: 82px;
  border: 1.5px solid #e2e8f0; border-radius: 10px;
  background: #fff; box-shadow: 0 2px 8px rgba(15,23,42,0.07);
  cursor: pointer; transition: box-shadow 0.15s, border-color 0.15s; overflow: visible;
}
.fec-node:hover { box-shadow: 0 4px 16px rgba(15,23,42,0.12); border-color: #cbd5e1; }
.fec-node--sel  { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }

/* Execution visual states */
.fec-node--executing { border-color: #22c55e !important; border-width: 3px !important; box-shadow: 0 0 15px rgba(34,197,94,0.3); }
.fec-node--success   { border-color: #22c55e !important; }
.fec-node--error     { border-color: #ef4444 !important; }

/* Status Badges */
.fec-node-badge {
  position: absolute; top: -10px; right: -10px; width: 22px; height: 22px;
  border-radius: 50%; background: #fff; z-index: 5;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}
.fec-node-badge .msi { font-size: 18px; }
.fec-node-badge--success { color: #22c55e; }
.fec-node-badge--error   { color: #ef4444; }

.fec-node-badge--left {
  position: absolute; top: -10px; left: -10px; min-width: 22px; height: 22px;
  padding: 0 6px; background: #fff; color: #475569; border-radius: 11px;
  font-size: 10px; font-weight: 800; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(15,23,42,0.12); border: 1.5px solid #e2e8f0; z-index: 5;
}

/* Tooltip (Ficha) */
.fec-node-tooltip {
  position: absolute; bottom: calc(100% + 12px); left: 50%; transform: translateX(-50%);
  width: 200px; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  padding: 14px; z-index: 100; pointer-events: none;
  animation: fec-tooltip-fade 0.15s ease-out;
}
.fec-node-tooltip::after {
  content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
  border-width: 6px; border-style: solid; border-color: #e2e8f0 transparent transparent transparent;
}
.fec-tooltip-hdr { font-size: 9px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
.fec-tooltip-title { font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }

.fec-tooltip-status { margin-bottom: 12px; }
.fec-status-badge {
  display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px;
  border-radius: 12px; font-size: 9px; font-weight: 800; text-transform: uppercase;
}
.fec-status-badge.success { background: #ecfdf5; color: #059669; }
.fec-status-badge.error   { background: #fef2f2; color: #dc2626; }
.fec-status-badge .msi { font-size: 13px; }

.fec-tooltip-grid { display: grid; gap: 8px; margin-bottom: 12px; }
.fec-tooltip-row { display: flex; align-items: flex-start; gap: 10px; }
.fec-tooltip-row .msi { font-size: 16px; margin-top: 2px; }
.fec-tooltip-row .msi.start { color: #10b981; }
.fec-tooltip-row .msi.end { color: #ef4444; }

.fec-tooltip-label { font-size: 9px; font-weight: 700; color: #64748b; margin: 0; }
.fec-tooltip-val   { font-size: 11px; font-weight: 600; color: #1e293b; margin: 1px 0 0; }

.fec-tooltip-footer {
  display: flex; align-items: center; gap: 6px; padding-top: 10px;
  border-top: 1px solid #f1f5f9; font-size: 10px; color: #64748b;
}
.fec-tooltip-footer .msi { font-size: 15px; color: #6366f1; }

@keyframes fec-tooltip-fade {
  from { opacity: 0; transform: translateX(-50%) translateY(4px); }
  to   { opacity: 1; transform: translateX(-50%) translateY(0); }
}

.fec-node-hdr {
  display: flex; align-items: center; gap: 7px; padding: 8px 10px;
  background: var(--nb); border-radius: 8px 8px 0 0; border-bottom: 1px solid rgba(0,0,0,0.05);
}
.fec-node-hdr-ico {
  width: 22px; height: 22px; border-radius: 5px;
  background: var(--nc); color: #fff;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.fec-node-lbl { font-size: 12px; font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.fec-node-bdy  { padding: 8px 10px; display: flex; flex-direction: column; gap: 3px; }
.fec-node-tag  { font-size: 10px; font-weight: 500; color: #64748b; background: #f1f5f9; border-radius: 4px; padding: 1px 5px; display: inline-block; max-width: fit-content; }
.fec-node-meta { font-size: 10px; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Ports */
.fec-port {
  position: absolute; width: 12px; height: 12px; border-radius: 50%;
  background: #fff; border: 2px solid #94a3b8; top: 50%; transform: translateY(-50%);
  cursor: crosshair; transition: border-color 0.12s, transform 0.12s; z-index: 2;
}
.fec-port:hover { border-color: #2563eb; transform: translateY(-50%) scale(1.3); }
.fec-port--in  { left: -6px; }
.fec-port--out { right: -6px; }

/* Connection action bar */
.fec-conn-bar {
  position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 12px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 16px;
  box-shadow: 0 4px 16px rgba(15,23,42,0.1); z-index: 20;
}
.fec-conn-lbl { font-size: 12px; color: #64748b; }
.fec-conn-del {
  display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 500;
  background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; cursor: pointer; transition: all 0.12s;
}
.fec-conn-del:hover { background: #fee2e2; }

/* Connection visual states */
.fec-conn { transition: stroke 0.3s, stroke-width 0.3s; }
.fec-conn--active { stroke: #22c55e !important; stroke-width: 3 !important; }

/* ── Right Panel ──────────────────────────────────────────────── */
.fec-right {
  width: 272px; background: #fff; border-left: 1px solid #e2e8f0;
  display: flex; flex-shrink: 0; transition: width 0.22s ease;
  position: relative; overflow: hidden;
}
.fec-right--wide { width: 500px; }
.fec-right--collapsed { width: 24px; }
.fec-right--resizing { transition: none !important; }

.fec-resizer {
  position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  cursor: col-resize; z-index: 50; transition: background 0.2s;
}
.fec-resizer:hover { background: rgba(37, 99, 235, 0.2); }

.fec-right-inner { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 16px; display: flex; flex-direction: column; }
.fec-right-inner::-webkit-scrollbar { width: 4px; }
.fec-right-inner::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }

/* Properties */
.fec-props-hdr { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 16px; }
.fec-props-title { font-size: 13px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; }
.fec-props-sub { font-size: 11px; color: #94a3b8; margin-top: 1px; }
.fec-props-node-ico { width: 34px; height: 34px; border-radius: 8px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.fec-close-btn {
  margin-left: auto; flex-shrink: 0; width: 22px; height: 22px;
  border: none; background: transparent; cursor: pointer; border-radius: 5px;
  color: #94a3b8; display: flex; align-items: center; justify-content: center; transition: all 0.12s;
}
.fec-close-btn:hover { background: #f1f5f9; color: #475569; }

/* Form fields */
.fec-prop-g  { margin-bottom: 12px; }
.fec-prop-l  { display: block; font-size: 10px; font-weight: 700; color: #475569; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.05em; }
.fec-prop-i, .fec-prop-ta, .fec-prop-sel {
  width: 100%; box-sizing: border-box; padding: 7px 10px; font-size: 12px;
  border: 1px solid #e2e8f0; border-radius: 7px; background: #fff; outline: none;
  transition: border-color 0.15s, box-shadow 0.15s; font-family: inherit;
}
.fec-prop-i::placeholder, .fec-prop-ta::placeholder { color: #cbd5e1; }
.fec-prop-i:focus, .fec-prop-ta:focus, .fec-prop-sel:focus {
  border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.fec-prop-ta { resize: vertical; min-height: 60px; }
.fec-sel-wrap { position: relative; }
.fec-prop-sel { padding-right: 28px; appearance: none; cursor: pointer; }
.fec-sel-arr  { position: absolute; right: 7px; top: 50%; transform: translateY(-50%); color: #64748b; pointer-events: none; }

.fec-divider {
  display: flex; align-items: center; gap: 8px; margin: 4px 0 12px;
  font-size: 9px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em;
}
.fec-divider::before, .fec-divider::after { content: ''; flex: 1; height: 1px; background: #f1f5f9; }

.fec-flow-stats { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 7px; }
.fec-stat-row  { display: flex; align-items: center; gap: 7px; font-size: 12px; color: #64748b; }

.fec-node-del-wrap { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f1f5f9; }
.fec-node-del-btn {
  display: flex; align-items: center; gap: 6px; width: 100%; padding: 7px 12px;
  background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; border-radius: 8px;
  font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.12s;
}
.fec-node-del-btn:hover { background: #fee2e2; }

/* Tabs */
.fec-tabs { display: flex; gap: 4px; border-bottom: 1px solid #f1f5f9; margin-bottom: 16px; padding-bottom: 8px; }
.fec-tab {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 6px 4px; border: none; background: transparent; cursor: pointer;
  font-size: 11px; font-weight: 600; color: #94a3b8; border-radius: 6px; transition: all 0.15s;
}
.fec-tab:hover { background: #f8fafc; color: #475569; }
.fec-tab.active { background: #eff6ff; color: #2563eb; }

/* History */
.fec-history-list { display: flex; flex-direction: column; gap: 8px; }
.fec-history-item {
  padding: 10px; border: 1px solid #e2e8f0; border-radius: 10px; cursor: pointer;
  transition: all 0.15s; background: #fff;
}
.fec-history-item:hover { border-color: #2563eb; box-shadow: 0 2px 8px rgba(37,99,235,0.08); }
.fec-hi-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.fec-hi-status { width: 8px; height: 8px; border-radius: 50%; }
.fec-hi-status--success { background: #10b981; box-shadow: 0 0 6px #10b98144; }
.fec-hi-status--error { background: #ef4444; }
.fec-hi-date { font-size: 11px; font-weight: 600; color: #1e293b; flex: 1; }
.fec-hi-duration { font-size: 10px; color: #94a3b8; }
.fec-hi-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 4px; }
.fec-hi-id { font-size: 10px; color: #cbd5e1; font-family: monospace; }
.fec-history-loading, .fec-history-empty { padding: 32px 16px; text-align: center; font-size: 12px; color: #94a3b8; }
.spin { animation: spin 2s linear infinite; }

.fec-run-wrap { margin-top: auto; padding-top: 24px; }
.fec-run-btn {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 10px; border-radius: 8px; border: none; cursor: pointer;
  background: #2563eb; color: #fff; font-size: 13px; font-weight: 600;
  transition: all 0.15s;
}
.fec-run-btn:hover:not(:disabled) { background: #1d4ed8; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37,99,235,0.2); }
.fec-run-btn:disabled { background: #94a3b8; cursor: not-allowed; opacity: 0.7; }
.fec-run-btn .msi { animation: none; }
.exec-status-running .fec-run-btn .msi { animation: spin 2s linear infinite; }

@keyframes spin { 100% { transform: rotate(360deg); } }

/* ── Bottom Panel ─────────────────────────────────────────────── */
.fec-bottom {
  position: absolute; bottom: 0; left: 0; right: 0; z-index: 30;
  border-top: 1px solid #e2e8f0;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.05);
  background: #fff;
}
.fec-bottom--resizing { transition: none !important; }

.fec-resizer-v {
  position: absolute; top: 0; left: 0; right: 0; height: 4px;
  cursor: row-resize; z-index: 50; transition: background 0.2s;
}
.fec-resizer-v:hover { background: rgba(37, 99, 235, 0.2); }

/* Connection binding helpers */
.fec-conn-hint   { font-size: 11px; color: #94a3b8; margin-top: 4px; }
.fec-conn-spin   { margin-left: 6px; vertical-align: middle; }
.fec-conn-filled { font-size: 11px; color: #16a34a; margin-top: 4px; display: flex; align-items: center; gap: 4px; }

/* ── Notes (Annotations) ───────────────────────────────────────── */
.fec-node--annotations {
  width: 240px; min-height: 120px; padding: 0;
  background: #fef9c3; border-color: #fde047;
  display: flex; flex-direction: column;
}
.fec-note-body { flex: 1; display: flex; flex-direction: column; padding: 12px; position: relative; }

/* Styling Toolbar */
.fec-note-toolbar {
  position: absolute; bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 4px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 4px 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 100;
}
.fec-note-palette { display: flex; gap: 4px; }
.fec-note-color {
  width: 18px; height: 18px; border-radius: 50%; border: 1px solid rgba(0,0,0,0.1);
  cursor: pointer; padding: 0; transition: transform 0.1s;
}
.fec-note-color:hover { transform: scale(1.2); }
.fec-note-tsep { width: 1px; height: 16px; background: #e2e8f0; margin: 0 4px; }
.fec-note-tbtn {
  width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
  border: none; background: transparent; cursor: pointer; color: #64748b; border-radius: 4px;
}
.fec-note-tbtn:hover { background: #f1f5f9; color: #2563eb; }
.fec-note-tbtn--del:hover { background: #fee2e2; color: #dc2626; }
.fec-note-tsize { font-size: 11px; font-weight: 700; color: #475569; min-width: 16px; text-align: center; }

.fec-note-ta {
  width: 100%; height: 100%; min-height: 100px;
  border: none; background: transparent; resize: none;
  font-family: inherit; font-size: 13px; color: #713f12; outline: none;
}
.fec-note-content {
  flex: 1; font-size: 13px; color: #713f12; line-height: 1.5;
  overflow-y: auto; overflow-x: hidden;
}

/* Markdown Styling inside notes */
.fec-note-content :deep(h1) { font-size: 1.25rem; font-weight: 700; margin: 0 0 0.5rem; color: #422006; }
.fec-note-content :deep(h2) { font-size: 1.1rem; font-weight: 700; margin: 0.75rem 0 0.4rem; color: #422006; }
.fec-note-content :deep(p) { margin: 0 0 0.5rem; }
.fec-note-content :deep(ul), .fec-note-content :deep(ol) { margin: 0 0 0.5rem; padding-left: 1.25rem; }
.fec-note-content :deep(code) { background: rgba(0,0,0,0.05); padding: 0.1rem 0.2rem; border-radius: 3px; font-family: monospace; font-size: 0.9em; }
.fec-note-content :deep(pre) { background: rgba(0,0,0,0.05); padding: 0.5rem; border-radius: 5px; overflow-x: auto; margin: 0.5rem 0; }
.fec-note-content :deep(pre code) { background: transparent; padding: 0; }

.fec-note-resizer {
  position: absolute; bottom: 0; right: 0;
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  color: #94a3b8; cursor: nwse-resize; z-index: 10;
  transition: color 0.1s;
}
.fec-note-resizer:hover { color: #2563eb; }
.fec-note-resizer .msi { font-size: 16px; }

/* ── Dynamic Select Styles ───────────────────────────────────────── */
.fec-dynamic-sel-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.fec-sel-with-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fec-sel-with-refresh .fec-prop-sel {
  flex: 1;
}

.fec-refresh-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s;
}

.fec-refresh-btn:hover:not(:disabled) {
  background: #e2e8f0;
  color: #334155;
}

.fec-refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.fec-refresh-btn .msi {
  font-size: 16px;
}

/* Multi Select Styles */
.fec-multi-sel-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fec-checkbox-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px;
  background: #fff;
}

.fec-checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.1s;
}

.fec-checkbox-item:hover {
  background: #f1f5f9;
}

.fec-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #2563eb;
}

.fec-checkbox-label {
  flex: 1;
  font-size: 13px;
  color: #334155;
}

.fec-checkbox-meta {
  color: #94a3b8;
  font-size: 11px;
  margin-left: 4px;
}
</style>
