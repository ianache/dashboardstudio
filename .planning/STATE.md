---
gsd_state_version: 1.0
milestone: v1.8
milestone_name: BFF Service Architecture
current_phase: 33
current_plan: Not started
status: defining_requirements
last_updated: "2026-05-28T00:00:00.000Z"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State: BFF Service Architecture

- **Status:** Defining requirements
- **Current Phase:** Not started
- **Last Action:** Milestone v1.8 started — BFF Service Architecture

## Workflow Status
- [x] Config defined
- [x] Context created
- [ ] Research completed
- [ ] Requirements finalized
- [ ] Roadmap structured
- [ ] Execution complete

## Milestone: v1.8 BFF Service Architecture
- [ ] Phase 33+: TBD after roadmap

## Accumulated Context

### Milestone Goals
- Crear servicio BFF en Node.js + Express en `bff/`
- BFF maneja autenticación Keycloak (login, logout, callback OIDC, refresh)
- Sesiones server-side con express-session y cookie segura
- BFF proxea todas las rutas del backend FastAPI
- BFF proxea CubeJS (token gestionado server-side)
- Backend cleanup: eliminar lógica de auth, solo lógica de negocio pura
- Frontend actualizado para llamar al BFF en lugar de backend/Keycloak directamente

### Technical Context
- **Milestone anterior completado:** Email Node with Dynamic Templates (Phase 32)
- **Arquitectura actual:** dashboard-app → backend (FastAPI) directamente; Keycloak SDK en frontend
- **Nueva arquitectura objetivo:** dashboard-app → BFF (Express) → backend (FastAPI) + CubeJS
- **BFF stack:** Node.js + Express, keycloak-connect, express-session
- **Session strategy:** Server-side sessions, secure cookie al browser
- **Frontend:** Vue 3, actualmente usa Keycloak JS adapter directamente

### Project Reference

See: .planning/PROJECT.md (updated 2026-05-28)

**Core value:** BFF concentra auth y session management, expone API unificada al frontend
**Current focus:** Defining requirements for v1.8 BFF Service Architecture
