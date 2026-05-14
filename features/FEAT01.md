Para que **Gemini Code Assist** (o un agente de IA similar) pueda implementar este feature en tu repositorio dashboardstudio de manera precisa, el documento de requisitos (ReqSpec) debe ser técnico, modular y basado en el contexto de tu stack (**Vue 3, Pinia, FastAPI, JWT**).
Aquí tienes el **Requirement Specification (ReqSpec)** listo para ser copiado y pegado en tu prompt de Code Assist:
# ReqSpec: Secure Dashboard Embedding & Pop-out Sync
## 1. Objective
Enable a "Shared & Embedded" mode for dashboards and a "Pop-out" independent window feature, ensuring secure data isolation and real-time state synchronization between windows.
## 2. Technical Stack
 * **Frontend:** Vue 3 (Composition API), Pinia (State Management).
 * **Communication:** Broadcast Channel API.
 * **Backend:** FastAPI (Python), Jose (JWT).
 * **Security:** CSP (Content Security Policy) frame-ancestors, SameSite Cookies.
## 3. Functional Requirements
### FR1: Secure Embedding (Iframe)
 * **Token Generation:** Backend must provide an endpoint /dashboards/{id}/embed-token that returns a short-lived JWT.
 * **Validation:** The frontend, when in embed mode, must send this JWT in the Authorization header for all data requests.
 * **Layout Mode:** Implement a isEmbedded computed property in Vue to hide navigation bars and sidebars when the URL contains ?embed=true.
### FR2: Pop-out Window (Independent View)
 * **Detachment:** Create a function openDashboardPopout(id) using window.open targeting a specific route /render/:id.
 * **Window Management:** Ensure the child window is identifiable and can be focused if already open.
### FR3: Real-time State Sync (Pinia + BroadcastChannel)
 * **Sync Plugin:** Create a Pinia plugin that listens to a BroadcastChannel('dashboard_sync').
 * **Bidirectional Sync:** * Any change in dashboardStore.filters in the Main App must reflect in the Pop-out window.
   * (Optional) Actions in the Pop-out window should notify the Main App.
 * **Serialization:** Ensure state is sanitized (JSON stringify/parse) before transmission to avoid reference leaks.
## 4. Security & Constraints (Non-Functional)
### NF1: Clickjacking Protection
 * **CSP Header:** Implement a dynamic Content-Security-Policy: frame-ancestors to allow only authorized domains (Tenant Whitelist).
### NF2: Cross-Origin Isolation
 * **PostMessage Validation:** If using postMessage for external host communication, strictly validate event.origin.
### NF3: Performance
 * Sync latency between windows must be <100ms (Native BroadcastChannel).
## 5. Implementation Tasks (Steps for Gemini)
 1. **Backend:** Modify main.py or the security router to include the JWT-based Signed URL logic.
 2. **Store:** Enhance src/stores/dashboard.ts to include the sync logic using store.$subscribe.
 3. **Router:** Add the /render/:id route in src/router/index.ts with a layout-only component.
 4. **Component:** Create a PopoutButton.vue that triggers the independent window.