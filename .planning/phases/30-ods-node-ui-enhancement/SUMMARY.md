---
phase: 30-ods-node-ui-enhancement
status: complete
completed_date: 2026-05-16
---

# Phase 30: ODS Node UI Enhancement - Execution Summary

## Overview
Successfully implemented the ODS PostgreSQL node UI enhancement with dynamic selectors, conditional fields, and refresh capabilities.

## Files Created

### 1. Database Migration
**File:** `backend/alembic/versions/030_update_ods_pg_tool.py`

Updates the `ods_pg` tool definition with:
- `connection_id`: Select field with `options_source: 'data_sources'` filtered by PostgreSQL type
- `schema`: Text field (kept from original)
- `table`: Dynamic select field that fetches tables from the selected connection
- `write_mode`: Select field (kept from original with append/upsert/overwrite/merge options)
- `identity_fields`: Multi-select field with conditional visibility (only shows when `write_mode == 'upsert'`)
- `batch_size`: Text field (kept from original)

### 2. Vue Component Updates
**File:** `dashboard-app/src/components/editor/FlowEditorCanvas.vue`

#### New Reactive State
- `dynamicOptionsCache`: Object to cache fetched options by endpoint
- `dynamicLoading`: Object to track loading state per property key

#### New Helper Functions
- `shouldShowProp(def)`: Evaluates `show_if` conditions
- `visiblePropDefs`: Computed property that filters prop definitions by visibility
- `getSelectOptions(def)`: Handles `options_source` for data sources
- `canFetchDynamic(def)`: Checks if all dependencies are satisfied
- `buildEndpoint(def)`: Builds API endpoint URL with variable substitution
- `getOptionsForDef(def, key)`: Returns cached options or triggers fetch
- `fetchDynamicOptions(def, key)`: Fetches options from API
- `refreshDynamicOptions(def, key)`: Forces refresh by clearing cache

#### Fixed Functions
- `getToolByType(toolType)`: Now parses `prop_defs` and `default_props` JSON strings
- `getNodePropDefs(toolType)`: Now parses `prop_defs` if stored as JSON string
- `onDrop(e)`: Now parses `default_props` when creating new nodes
- `watch(selectedNode)`: Now merges missing props with tool defaults for backward compatibility
- `watch(() => props.diagramData)`: Now merges node props with tool defaults when loading existing flows

#### New Template Handlers
- `dynamic_select`: Select dropdown with refresh button and disabled state
- `multi_select`: Checkbox list for selecting multiple identity fields

#### Cascading Watchers
- `connection_id` change → clears `table` and `identity_fields`
- `table` change → clears `identity_fields`
- `schema` change → clears `table` and `identity_fields`

#### New CSS Styles
- `.fec-dynamic-sel-wrap`: Container for dynamic selectors
- `.fec-sel-with-refresh`: Flex layout for select + refresh button
- `.fec-refresh-btn`: Refresh button styling with hover/disabled states
- `.fec-multi-sel-wrap`: Container for multi-select
- `.fec-checkbox-list`: Scrollable checkbox container
- `.fec-checkbox-item`: Individual checkbox row
- `.fec-checkbox`: Checkbox input styling
- `.fec-checkbox-label`: Label styling
- `.fec-checkbox-meta`: Data type hint styling

## API Integration

### Endpoints Used
- `GET /api/v1/data-sources` - List all data sources (for connection_id selector)
- `GET /api/v1/data-sources/{id}/tables?schema={schema}` - List tables
- `GET /api/v1/data-sources/{id}/tables/{table}/columns?schema={schema}` - List columns

### Authentication
All API requests include the auth token from `authStore.token` in the Authorization header.

## Success Criteria Met

✅ **Dynamic Table Selector**
- Connection selection triggers table dropdown population
- Tables fetched from `/data-sources/{id}/tables?schema={schema}`
- Refresh button re-fetches table list
- Select disabled until connection and schema are set

✅ **Conditional Identity Fields**
- Hidden when `write_mode != 'upsert'`
- Visible when `write_mode == 'upsert'`
- Shows multi-select checkboxes with column names
- Column data types shown in parentheses

✅ **Column Discovery**
- Fetches columns when table is selected
- Columns from `/data-sources/{id}/tables/{table}/columns`
- Refresh button re-fetches columns

✅ **Cascading Clears**
- Changing `connection_id` clears `table` and `identity_fields`
- Changing `table` clears `identity_fields`
- Changing `schema` clears `table` and `identity_fields`
- Cache cleared appropriately on each change

✅ **Backward Compatibility**
- Existing flows with old `ods_pg` props will still load
- New fields have sensible defaults
- Old flows can be edited with new UI

## Testing Notes

### Build Verification
Frontend build completed successfully with no errors:
```
vite v5.4.21 building for production...
✓ 1078 modules transformed.
✓ built in 12.05s
```

### Bug Fixes Applied

**Issue:** Properties not showing for existing nodes
- **Cause:** Database stores `prop_defs` and `default_props` as JSON strings, but code expected objects
- **Cause:** Existing nodes in saved flows didn't have the new fields initialized
- **Fix:** 
  1. Added JSON parsing in `getToolByType()` and `getNodePropDefs()`
  2. Added prop merging logic when loading diagrams and selecting nodes
  3. Added prop parsing in `onDrop()` when creating new nodes

**Issue:** 401 Unauthorized error when fetching dynamic options
- **Cause:** Used `authStore.token` which may be null or stale; auth store uses external `_keycloak` reference
- **Fix:** 
  1. Import `keycloak` directly from `@/services/keycloak`
  2. Use `keycloak.token` instead of `authStore.token`
  3. Add token expiration check and auto-refresh (30s buffer) before API calls
  4. Add proper error handling when token is not available

**Issue:** Properties not persisting/reloading after save (cascading clears on node selection)
- **Cause:** Cascading watchers were triggering when a node was selected, clearing dependent field values (table, identity_fields)
- **Root Cause:** The watchers didn't distinguish between user-initiated changes vs initial node selection loading
- **Fix:**
  1. Added `isInitializingNodeSelection` flag
  2. Set flag at start of `watch(selectedNode)` and clear with `nextTick()` after initialization
  3. Added checks in cascading watchers to skip when flag is set
  4. Added checks to skip when `oldVal === undefined` (initial watch trigger)

### Migration Notes
Run migration with:
```bash
cd backend
alembic upgrade 030
```

Rollback if needed:
```bash
alembic downgrade 029
```

### Important: Clear Browser Cache
After deploying the migration, users should clear their browser cache or hard refresh (Ctrl+F5) to ensure the updated JavaScript is loaded.

## Next Phase Dependencies

Phase 31 (ODS Execution Engine) will use:
- `connection_id` to look up data source configuration
- `identity_fields` to build ON CONFLICT clause for upserts
- `write_mode` to determine SQL execution strategy
- `schema` and `table` for target location

## Architecture Notes

### Design Decisions
1. **Cache Strategy**: Options are cached by endpoint URL to avoid repeated API calls
2. **Auto-fetch**: Data is fetched automatically when dependencies are met
3. **Cascading Clears**: Dependent fields are cleared immediately when parent changes
4. **Conditional Visibility**: Uses computed property `visiblePropDefs` to filter by `show_if` conditions
5. **Error Handling**: Failed fetches show empty lists with console errors

### Extensibility
The dynamic selector pattern can be reused for other tools by:
1. Adding `type: 'dynamic_select'` or `type: 'multi_select'` to prop definitions
2. Setting `depends_on` and `fetch_endpoint` properties
3. Optionally adding `show_if` for conditional visibility

## Files Modified
- `backend/alembic/versions/030_update_ods_pg_tool.py` (created)
- `dashboard-app/src/components/editor/FlowEditorCanvas.vue` (extended)
- `.planning/ROADMAP.md` (updated status)
