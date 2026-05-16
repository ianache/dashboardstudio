# Phase 30: Task Checklist

## Overview
Quick reference checklist for Phase 30 implementation. For full details, see PLAN.md.

## Tasks

### ☐ Task 1: Database Migration
**File:** `backend/alembic/versions/030_update_ods_pg_tool.py`

**Changes:**
- [ ] Create migration file with revision `030`
- [ ] Update `prop_defs` with new field definitions
  - [ ] `connection_id` - select from data sources
  - [ ] `table` - dynamic_select with refresh
  - [ ] `identity_fields` - multi_select with show_if condition
- [ ] Update `default_props` with new defaults
- [ ] Test migration: `alembic upgrade 030`
- [ ] Test downgrade: `alembic downgrade 029`

### ☐ Task 2: Extend Property Renderer
**File:** `dashboard-app/src/components/editor/FlowEditorCanvas.vue`

**Template Section (around line 540):**
- [ ] Add `visiblePropDefs` computed property with `show_if` filtering
- [ ] Add `dynamic_select` type handler with select + refresh button
- [ ] Add `multi_select` type handler with checkbox list

**Script Section:**
- [ ] Add `dynamicOptionsCache` reactive object
- [ ] Add `dynamicLoading` reactive object
- [ ] Implement `shouldShowProp(def)` function
- [ ] Implement `fetchDynamicOptions(def, key)` function
- [ ] Implement `getSelectOptions(def)` function
- [ ] Implement `canFetchDynamic(def)` function
- [ ] Implement `getDynamicOptions(def, key)` function
- [ ] Implement `refreshDynamicOptions(def, key)` function
- [ ] Add watchers for cascading clears (connection_id → table → identity_fields)

### ☐ Task 3: Add Styles
**File:** `dashboard-app/src/components/editor/FlowEditorCanvas.vue`

**CSS to add:**
- [ ] `.fec-dynamic-sel-wrap` - Container for dynamic selectors
- [ ] `.fec-sel-with-refresh` - Flex layout for select + button
- [ ] `.fec-refresh-btn` - Refresh button styling
- [ ] `.fec-multi-sel-wrap` - Container for multi-select
- [ ] `.fec-checkbox-list` - Scrollable checkbox container
- [ ] `.fec-checkbox-item` - Individual checkbox row
- [ ] `.fec-checkbox` - Checkbox input styling
- [ ] `.fec-checkbox-label` - Label styling
- [ ] `.fec-checkbox-meta` - Data type hint styling

### ☐ Task 4: Testing
**Test Cases:**

**Basic Flow:**
- [ ] Create flow with ODS node
- [ ] Select connection_id → table dropdown populates
- [ ] Select table → identity_fields fetches columns
- [ ] Refresh buttons work

**Conditional Visibility:**
- [ ] identity_fields hidden when write_mode != 'upsert'
- [ ] identity_fields visible when write_mode == 'upsert'

**Cascading Clears:**
- [ ] Change connection_id → table and identity_fields cleared
- [ ] Change table → identity_fields cleared

**Backward Compatibility:**
- [ ] Open existing flow from before Phase 30
- [ ] Verify no errors
- [ ] Can edit and save

## Dependencies

### Required Before Starting
- Phase 29 completed (metadata API endpoints available)
- Backend running with Phase 29 migrations applied

### APIs Used
- `GET /api/v1/data-sources` - List data sources
- `GET /api/v1/data-sources/{id}/tables?schema={schema}` - List tables
- `GET /api/v1/data-sources/{id}/tables/{table}/columns?schema={schema}` - List columns

## Success Criteria

1. User can select a connection from dropdown
2. User can see and select tables from the connected database
3. User can refresh table list
4. Identity fields only appear when write_mode is 'upsert'
5. User can select multiple identity columns with checkboxes
6. Changing connection clears table and identity selections
7. Changing table clears identity selections
8. Existing flows continue to work

## Estimated Effort
- Migration: 30 min
- Vue template changes: 2 hours
- Vue script changes: 3 hours
- Styling: 1 hour
- Testing: 1 hour
- **Total: ~7.5 hours**

## Notes

- The dynamic selector pattern established here can be reused for other tools
- Consider extracting DynamicSelector and MultiSelect to separate components in future
- Column data types shown in parentheses help users identify PK columns
