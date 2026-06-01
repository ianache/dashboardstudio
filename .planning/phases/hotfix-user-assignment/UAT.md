# UAT: Dashboard User Assignment Fix

**Objective:** Verify that user assignments to dashboards persist after closing and re-opening the "Asignar Usuarios" modal, and that search results from Keycloak are correctly mapped and synchronized.

## Requirements Coverage
| ID | Requirement | Status |
|----|-------------|--------|
| ASSIGN-01 | Assigned users must persist when re-opening the modal. | 🟢 |
| ASSIGN-02 | Dashboard cards must show the correct assigned user count on load. | 🟢 |
| ASSIGN-03 | Keycloak search results must display correct names and avatars. | 🟢 |
| ASSIGN-04 | Selecting/Deselecting users must sync correctly without losing search state. | 🟢 |

## Test Cases

### 1. Persistence Verification
- **Step 1:** In the Designer view, click "Asignar Usuarios" on a dashboard card.
- **Step 2:** Search for and assign 2 users.
- **Step 3:** Click "Guardar asignación".
- **Step 4:** Close the modal (if not closed) and then click "Asignar Usuarios" again on the same card.
- **Expected:** The 2 previously assigned users are still visible in the "USUARIOS ASIGNADOS" section with their full names and avatars.
- **Actual:** [TBD]
- **Status:** ⚪ PENDING

### 2. Dashboard Card Count
- **Step 1:** Refresh the Designer page.
- **Step 2:** Locate the dashboard card from the previous test.
- **Expected:** The "assigned-users-count" displayed on the card matches the number of assigned users (e.g., "2").
- **Actual:** [TBD]
- **Status:** ⚪ PENDING

### 3. Keycloak Mapping & Sync
- **Step 1:** Open the assignment modal.
- **Step 2:** Search for a user (e.g., "demo").
- **Step 3:** Verify results show Name, Email/Username, and an Avatar.
- **Step 4:** Select a user from the results.
- **Step 5:** Verify the user moves to the "Asignados" list and the search results remain populated with other matches.
- **Expected:** Mapping is correct and UI sync is seamless.
- **Actual:** [TBD]
- **Status:** ⚪ PENDING

## Issues Found
| ID | Title | Description | Severity | Status |
|----|-------|-------------|----------|--------|
| - | - | - | - | - |

## Summary
- **Total Tests:** 3
- **Passed:** 0
- **Failed:** 0
- **Pending:** 3
