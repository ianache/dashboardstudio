# Phase 30: ODS Node UI Enhancement

## Overview
Update the ODS PostgreSQL node properties panel with dynamic selectors for tables and columns, conditional visibility for identity fields, and refresh capability. This phase builds directly on Phase 29's Metadata Inspection API.

## Requirements Mapping

| Requirement | Description | Implementation Target |
|-------------|-------------|----------------------|
| FR-01 | Table discovery dropdown | Dynamic selector for `table` field fetching from `/data-sources/{id}/tables` |
| FR-02 | Refresh button | Add refresh icon button next to dynamic selectors |
| FR-03 | Identity field selection | Multi-select for columns when `write_mode == 'upsert'` |
| FR-04 | Column discovery | Fetch columns from `/data-sources/{id}/tables/{table}/columns` |
| TR-02 | DynamicSelect component | Extend property renderer to support `type: 'dynamic_select'` |
| TR-03 | Conditional visibility | Implement `show_if` logic in property definitions |

## Current State Analysis

### ODS Tool Definition (Current)
```python
{
  'schema':     {'label':'Schema destino',  'type':'text',   'placeholder':'ods'},
  'table':      {'label':'Tabla destino',   'type':'text',   'placeholder':'fact_ventas'},
  'write_mode': {'label':'Modo escritura',  'type':'select', 'options':[...]},
  'batch_size': {'label':'Tamaño de batch', 'type':'text',   'placeholder':'1000'}
}
```

### Phase 29 API (Available)
- `GET /data-sources/{id}/tables?schema={schema}` - Returns list of table names
- `GET /data-sources/{id}/tables/{table_name}/columns?schema={schema}` - Returns column objects with `name` and `type`

### Property Renderer (Current)
Located in `FlowEditorCanvas.vue` lines 540-566, supports:
- `code` → CodeEditor component
- `textarea` → textarea element
- `select` → select element with options
- default → input element

## Target State

### Updated ODS Tool Definition
```python
{
  'connection_id': {
    'label': 'Conexión de Datos',
    'type': 'select',
    'options_source': 'data_sources',
    'filter_by_type': 'postgresql'
  },
  'schema': {
    'label': 'Schema destino',
    'type': 'text',
    'placeholder': 'ods',
    'default': 'ods'
  },
  'table': {
    'label': 'Tabla destino',
    'type': 'dynamic_select',
    'depends_on': 'connection_id',
    'refreshable': True,
    'placeholder': 'Seleccione una tabla...',
    'fetch_endpoint': '/data-sources/{connection_id}/tables?schema={schema}'
  },
  'write_mode': {
    'label': 'Modo escritura',
    'type': 'select',
    'options': [
      {'value': 'append', 'label': 'Append'},
      {'value': 'upsert', 'label': 'Upsert'},
      {'value': 'overwrite', 'label': 'Overwrite'},
      {'value': 'merge', 'label': 'Merge (SCD2)'}
    ]
  },
  'identity_fields': {
    'label': 'Campos de Identidad (PK)',
    'type': 'multi_select',
    'show_if': {'field': 'write_mode', 'equals': 'upsert'},
    'depends_on': ['connection_id', 'table', 'schema'],
    'refreshable': True,
    'placeholder': 'Seleccione columnas...',
    'fetch_endpoint': '/data-sources/{connection_id}/tables/{table}/columns?schema={schema}'
  },
  'batch_size': {
    'label': 'Tamaño de batch',
    'type': 'text',
    'placeholder': '1000',
    'default': '1000'
  }
}
```

## Task Breakdown

### Task 1: Extend Property Type System
**File:** `dashboard-app/src/components/editor/FlowEditorCanvas.vue`

**Work:**
1. Add `dynamic_select` type handler in the properties template section
2. Add `multi_select` type handler with checkbox/chip UI
3. Create computed property `visiblePropDefs` that filters based on `show_if` conditions
4. Add state management for dynamic selector cache (avoid refetching)

**Code Changes:**
- Lines 540-566: Extend the `v-for` template to handle new types
- Add `DynamicSelector` component inline or as separate component
- Add `MultiSelect` component for identity fields
- Add `shouldShowProp(propDef)` helper function

**New Data:**
```javascript
// Add to script setup
const dynamicOptionsCache = ref({}) // key: endpoint, value: options[]
const dynamicLoading = ref({})      // key: propKey, value: boolean

// Helper to evaluate show_if conditions
function shouldShowProp(def) {
  if (!def.show_if) return true
  const { field, equals } = def.show_if
  return selectedNode.value?.props?.[field] === equals
}

// Helper to fetch dynamic options
async function fetchDynamicOptions(propDef, key) {
  if (!propDef.fetch_endpoint || !selectedNode.value) return
  
  // Build endpoint with variable substitution
  let endpoint = propDef.fetch_endpoint
  const deps = Array.isArray(propDef.depends_on) 
    ? propDef.depends_on 
    : [propDef.depends_on]
  
  for (const dep of deps) {
    const value = selectedNode.value.props?.[dep]
    if (!value) return // Don't fetch if dependencies not set
    endpoint = endpoint.replace(`{${dep}}`, encodeURIComponent(value))
  }
  
  const cacheKey = endpoint
  if (dynamicOptionsCache.value[cacheKey]) {
    return dynamicOptionsCache.value[cacheKey]
  }
  
  dynamicLoading.value[key] = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}${endpoint}`, {
      headers: { 'Authorization': `Bearer ${window.keycloak?.token}` }
    })
    const data = await response.json()
    dynamicOptionsCache.value[cacheKey] = data
    return data
  } catch (e) {
    console.error(`Failed to fetch options for ${key}:`, e)
    return []
  } finally {
    dynamicLoading.value[key] = false
  }
}
```

### Task 2: Create Database Migration for Tool Definition
**File:** `backend/alembic/versions/030_update_ods_pg_tool.py`

**Work:**
1. Create migration to update `prop_defs` for `ods_pg` tool
2. Update `default_props` with new fields

**Migration:**
```python
"""update ods_pg tool for dynamic selectors

Revision ID: 030
Revises: 029 (metadata API migration)
Create Date: 2026-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '030'
down_revision: Union[str, None] = '029'  # Phase 29 migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        column('prop_defs', sa.JSON),
        column('default_props', sa.JSON),
        schema='biportal'
    )
    
    new_prop_defs = {
        'connection_id': {
            'label': 'Conexión de Datos',
            'type': 'select',
            'options_source': 'data_sources',
            'filter_by_type': 'postgresql'
        },
        'schema': {
            'label': 'Schema destino',
            'type': 'text',
            'placeholder': 'ods',
            'default': 'ods'
        },
        'table': {
            'label': 'Tabla destino',
            'type': 'dynamic_select',
            'depends_on': 'connection_id',
            'refreshable': True,
            'placeholder': 'Seleccione una tabla...',
            'fetch_endpoint': '/data-sources/{connection_id}/tables?schema={schema}'
        },
        'write_mode': {
            'label': 'Modo escritura',
            'type': 'select',
            'options': [
                {'value': 'append', 'label': 'Append'},
                {'value': 'upsert', 'label': 'Upsert'},
                {'value': 'overwrite', 'label': 'Overwrite'},
                {'value': 'merge', 'label': 'Merge (SCD2)'}
            ]
        },
        'identity_fields': {
            'label': 'Campos de Identidad (PK)',
            'type': 'multi_select',
            'show_if': {'field': 'write_mode', 'equals': 'upsert'},
            'depends_on': ['connection_id', 'table', 'schema'],
            'refreshable': True,
            'placeholder': 'Seleccione columnas...',
            'fetch_endpoint': '/data-sources/{connection_id}/tables/{table}/columns?schema={schema}'
        },
        'batch_size': {
            'label': 'Tamaño de batch',
            'type': 'text',
            'placeholder': '1000',
            'default': '1000'
        }
    }
    
    new_default_props = {
        'connection_id': '',
        'schema': 'ods',
        'table': '',
        'write_mode': 'upsert',
        'identity_fields': [],
        'batch_size': '1000'
    }
    
    op.execute(
        tools_table.update()
        .where(tools_table.c.type == 'ods_pg')
        .values(
            prop_defs=json.dumps(new_prop_defs),
            default_props=json.dumps(new_default_props)
        )
    )

def downgrade() -> None:
    # Restore original prop_defs
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        column('prop_defs', sa.JSON),
        column('default_props', sa.JSON),
        schema='biportal'
    )
    
    old_prop_defs = {
        'schema': {'label': 'Schema destino', 'type': 'text', 'placeholder': 'ods'},
        'table': {'label': 'Tabla destino', 'type': 'text', 'placeholder': 'fact_ventas'},
        'write_mode': {
            'label': 'Modo escritura',
            'type': 'select',
            'options': [
                {'value': 'append', 'label': 'Append'},
                {'value': 'upsert', 'label': 'Upsert'},
                {'value': 'overwrite', 'label': 'Overwrite'},
                {'value': 'merge', 'label': 'Merge (SCD2)'}
            ]
        },
        'batch_size': {'label': 'Tamaño de batch', 'type': 'text', 'placeholder': '1000'}
    }
    
    old_default_props = {
        'schema': 'ods',
        'table': '',
        'write_mode': 'upsert',
        'batch_size': '1000'
    }
    
    op.execute(
        tools_table.update()
        .where(tools_table.c.type == 'ods_pg')
        .values(
            prop_defs=json.dumps(old_prop_defs),
            default_props=json.dumps(old_default_props)
        )
    )
```

### Task 3: Implement Dynamic Selector UI
**File:** `dashboard-app/src/components/editor/FlowEditorCanvas.vue`

**Template Changes (around line 540):**
```vue
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
    <textarea 
      v-else-if="def.type === 'textarea'" 
      v-model="selectedNode.props[key]" 
      class="fec-prop-ta" 
      :rows="def.rows || 3" 
      :placeholder="def.placeholder || ''"
    />
    
    <!-- Static Select -->
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
          <option v-for="opt in getDynamicOptions(def, key)" :key="opt" :value="opt">{{ opt }}</option>
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
      <div class="fec-sel-with-refresh">
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
      <div v-else-if="getDynamicOptions(def, key).length === 0 && !dynamicLoading[key]" class="fec-conn-hint">
        No hay columnas disponibles. Haga clic en refresh.
      </div>
      <div v-else class="fec-checkbox-list">
        <label 
          v-for="opt in getDynamicOptions(def, key)" 
          :key="opt.name || opt"
          class="fec-checkbox-item"
        >
          <input 
            type="checkbox" 
            :value="opt.name || opt"
            v-model="selectedNode.props[key]"
            class="fec-checkbox"
          />
          <span class="fec-checkbox-label">
            {{ opt.name || opt }}
            <span v-if="opt.type" class="fec-checkbox-meta">({{ opt.type }})</span>
          </span>
        </label>
      </div>
    </div>
    
    <!-- Default input -->
    <input 
      v-else 
      v-model="selectedNode.props[key]" 
      class="fec-prop-i" 
      :placeholder="def.placeholder || ''" 
    />
  </div>
</template>
```

**Script Changes:**
```javascript
// Computed property for visible props (respects show_if)
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

// Helper to get static select options
function getSelectOptions(def) {
  if (def.options_source === 'data_sources') {
    return dataSources.value
      .filter(ds => !def.filter_by_type || ds.type === def.filter_by_type)
      .map(ds => ({ value: ds.id, label: ds.name }))
  }
  return def.options || []
}

// Helper to check if dynamic fetch is possible
function canFetchDynamic(def) {
  if (!selectedNode.value) return false
  const deps = Array.isArray(def.depends_on) ? def.depends_on : [def.depends_on]
  return deps.every(dep => selectedNode.value.props?.[dep])
}

// Helper to get dynamic options
function getDynamicOptions(def, key) {
  if (!canFetchDynamic(def)) return []
  
  let endpoint = def.fetch_endpoint
  const deps = Array.isArray(def.depends_on) ? def.depends_on : [def.depends_on]
  for (const dep of deps) {
    const value = selectedNode.value.props?.[dep]
    if (!value) return []
    endpoint = endpoint.replace(`{${dep}}`, encodeURIComponent(value))
  }
  
  // Auto-fetch on first view
  if (!dynamicOptionsCache.value[endpoint] && !dynamicLoading.value[key]) {
    fetchDynamicOptions(def, key)
  }
  
  const cached = dynamicOptionsCache.value[endpoint]
  if (!cached) return []
  
  // Handle both string arrays (table names) and object arrays (columns)
  return cached
}

// Refresh handler
async function refreshDynamicOptions(def, key) {
  if (!canFetchDynamic(def)) return
  
  let endpoint = def.fetch_endpoint
  const deps = Array.isArray(def.depends_on) ? def.depends_on : [def.depends_on]
  for (const dep of deps) {
    const value = selectedNode.value.props?.[dep]
    endpoint = endpoint.replace(`{${dep}}`, encodeURIComponent(value))
  }
  
  // Clear cache to force refetch
  delete dynamicOptionsCache.value[endpoint]
  await fetchDynamicOptions(def, key)
}

// Watch for changes in dependencies to clear dependent values
watch(() => selectedNode.value?.props?.connection_id, (newVal, oldVal) => {
  if (newVal !== oldVal && selectedNode.value) {
    selectedNode.value.props.table = ''
    selectedNode.value.props.identity_fields = []
  }
})

watch(() => selectedNode.value?.props?.table, (newVal, oldVal) => {
  if (newVal !== oldVal && selectedNode.value) {
    selectedNode.value.props.identity_fields = []
  }
})
```

### Task 4: Add CSS Styles
**File:** `dashboard-app/src/components/editor/FlowEditorCanvas.vue` (style section)

**Add to `<style scoped>`:**
```css
/* Dynamic Select Styles */
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
```

## Dependencies

### Phase 29 (Completed)
- ✅ `GET /data-sources/{id}/tables` endpoint
- ✅ `GET /data-sources/{id}/tables/{table_name}/columns` endpoint
- ✅ `metadata_service.py` with PostgreSQL support

### Data Sources API
- `dataSourcesApi.getAll()` - Already used in FlowEditorCanvas for connection binding

## Integration Points

### Connection Selector Integration
The `connection_id` field uses `options_source: 'data_sources'` which will:
1. Fetch data sources via existing `loadDataSources()` function
2. Filter by `filter_by_type: 'postgresql'` 
3. Display name/label mapping

This is similar to the existing connection binding UI (lines 488-536) but integrated into the property renderer.

### Metadata API Integration
The `dynamic_select` and `multi_select` types will:
1. Build endpoint URLs with variable substitution from dependent fields
2. Fetch via authenticated requests using existing auth pattern
3. Cache results to avoid repeated requests
4. Support manual refresh via refresh button

## Success Criteria

1. **Dynamic Table Selector**
   - [ ] When `connection_id` is selected, the `table` field shows a dropdown
   - [ ] Tables are fetched from `/data-sources/{id}/tables?schema={schema}`
   - [ ] A refresh button appears next to the table selector
   - [ ] Clicking refresh re-fetches the table list

2. **Conditional Identity Fields**
   - [ ] `identity_fields` is hidden when `write_mode != 'upsert'`
   - [ ] `identity_fields` appears when `write_mode == 'upsert'`
   - [ ] Shows multi-select checkboxes with column names
   - [ ] Column data types shown in parentheses

3. **Column Discovery**
   - [ ] When table is selected, identity_fields fetches columns
   - [ ] Columns come from `/data-sources/{id}/tables/{table}/columns`
   - [ ] Refresh button re-fetches columns

4. **Cascading Clears**
   - [ ] Changing `connection_id` clears `table` and `identity_fields`
   - [ ] Changing `table` clears `identity_fields`

5. **Backward Compatibility**
   - [ ] Existing flows with old `ods_pg` props still load
   - [ ] New fields have sensible defaults
   - [ ] Old flows can be edited with new UI

## Testing Plan

### Manual Test Cases

**Test 1: Basic Dynamic Selector Flow**
1. Create new flow
2. Add ODS PostgreSQL node
3. Verify `connection_id` shows data sources
4. Select a PostgreSQL connection
5. Verify table dropdown populates
6. Select a table
7. Verify identity_fields fetches columns

**Test 2: Conditional Visibility**
1. Set `write_mode` to 'append'
2. Verify `identity_fields` is hidden
3. Set `write_mode` to 'upsert'
4. Verify `identity_fields` appears
5. Set `write_mode` back to 'append'
6. Verify `identity_fields` is hidden

**Test 3: Refresh Functionality**
1. Select connection and table
2. Click refresh on table selector
3. Verify loading spinner appears
4. Verify list refreshes
5. Select columns in identity_fields
6. Click refresh on identity_fields
7. Verify columns refresh (selection cleared)

**Test 4: Cascading Clears**
1. Select connection, table, and identity columns
2. Change connection
3. Verify table and identity_fields are cleared
4. Select table and identity columns again
5. Change table
6. Verify identity_fields is cleared

**Test 5: Backward Compatibility**
1. Open existing flow from Phase 28
2. Verify ODS node loads without errors
3. Edit ODS node properties
4. Save and reload

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Migration fails if tool not found | High | Use `where` clause, don't fail if no rows affected |
| Dynamic fetch fails (network) | Medium | Show error message, allow retry |
| Large table/column lists | Low | Virtual scroll or search filter (future) |
| Cache grows unbounded | Low | Clear cache on component unmount |
| Backward compatibility breaks | High | Test with old flow data before commit |

## Files Modified

1. `dashboard-app/src/components/editor/FlowEditorCanvas.vue` - Property renderer updates
2. `backend/alembic/versions/030_update_ods_pg_tool.py` - Tool definition migration (NEW)

## Files Created

1. `.planning/phases/30-ods-node-ui-enhancement/PLAN.md` - This file

## Next Phase Dependencies

Phase 31 (ODS Execution Engine) will use:
- `connection_id` to look up data source config
- `identity_fields` to build ON CONFLICT clause
- `write_mode` to determine SQL strategy

## Execution Order

1. **Task 2 first** (Database migration) - Must update tool definition before UI can use it
2. **Task 1 & 3** (Vue component changes) - Can be developed in parallel with migration
3. **Task 4** (CSS) - Polish at the end
4. **Testing** - After all tasks complete

## Goal-Backward Verification

**Goal:** Users can configure ODS PostgreSQL nodes with dynamic table/column discovery

**Verification:**
- Can select connection from dropdown? ✅ Task 2 (connection_id field)
- Can see and select tables from database? ✅ Task 3 (dynamic_select)
- Can refresh table list? ✅ Task 3 (refresh button)
- Identity fields only show for upsert? ✅ Task 1 (show_if logic)
- Can select multiple identity columns? ✅ Task 3 (multi_select)
- Values cleared when dependencies change? ✅ Task 3 (watchers)
