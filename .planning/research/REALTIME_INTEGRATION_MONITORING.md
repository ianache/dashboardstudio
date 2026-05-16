# Research: Real-time Integration Progress Monitoring

**Date:** 2026-05-15
**Goal:** Implement real-time monitoring of integration progress and display scheduled run times in the `IntegrationsView`.

## Executive Summary
To track integration progress in real-time, the current pull-based polling architecture needs enhancement. The backend currently uses `deno_service` and `scheduler`, likely executed via Celery or similar async tasks. To meet requirements, we need:
1.  **State Tracking:** A reliable way to store `total_nodes` and `executed_nodes` for active integrations.
2.  **Efficient Transport:** WebSockets or SSE (Server-Sent Events) for real-time updates.
3.  **UI Integration:** Updates to `IntegrationsView` to handle streaming progress data.

## Architectural Implications
- **Backend:** Current FastAPI setup likely handles logic in `scheduler.py` or `deno_service.py`. We need to introduce an event emitter or progress broadcast mechanism.
- **Frontend:** `IntegrationsView` uses Pinia. We should extend `integrations.js` to handle a socket connection or periodic background polling for status updates if WebSockets are too heavy for current infrastructure.

## Recommended Approach
1.  **Status Table:** Use a dedicated table in Postgres to track `integration_run_status` (run_id, total_nodes, completed_nodes, status).
2.  **Broadcast Mechanism:** Use FastAPI's `WebSockets` or simple periodic polling from the frontend to `GET /api/v1/integrations/status` if latency requirements allow. Given "refrescar automáticamente", polling every 2-5 seconds is a simpler, reliable, and less intrusive start than full WebSocket integration.
3.  **Frontend Implementation:**
    - Update `integrations.js` store to track per-flow progress.
    - Add a `useProgressMonitoring` composable that starts polling on mount.
    - Update the `IntegrationsView` table component to include a Progress column with a `progress-bar` widget.

## Feasibility
- **HIGH:** Technical foundation is present.
- **Risk:** Database load if too many integrations poll simultaneously.
- **Mitigation:** Use a smart polling strategy (only poll active flows).

## Roadmap Implications
- **Phase 1:** Backend API endpoints for current execution status.
- **Phase 2:** Frontend integration for real-time state consumption.
- **Phase 3:** UI column rendering and progress bar implementation.
