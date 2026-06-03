---
created: 2026-06-02T04:11:54.582Z
title: BI AI Analyst use dashboard filters for context-aware data analysis
area: ui
files:
  - dashboard-app/src/stores/aiAnalyst.js
  - dashboard-app/src/components/dashboard/AiAnalystPanel.vue
  - dashboard-app/src/components/dashboard/DashboardFilterBar.vue
---

## Problem

When a user asks the BI AI Analyst a question, the agent runs CubeJS queries without the active dashboard filters applied (date range, dimension slices, etc.). This means the agent's analysis may reflect different data than what the user is currently seeing in the dashboard charts — breaking the expectation that the AI is talking about the same data visible on screen.

For example: if the user has filtered to "Region: Lima, Month: April 2026", a question like "what drove the drop in sales?" should analyze April 2026 Lima data, not the full dataset.

## Solution

Pass the active dashboard filter state (from `DashboardFilterBar` / the dashboard store) as part of the context payload sent to the ai-analyst service on every `/chat` request.

The `screen_context` / `context` field already exists in `ChatRequest` — the fix is to populate it with the active filter values from the Pinia dashboard store before calling `sendMessage()` in `AiAnalystPanel.vue`.

On the backend, the agent instruction or the `query_data` tool should receive and apply these filters when building CubeJS queries.

Steps:
1. In `AiAnalystPanel.vue`, read active filters from the dashboard store when calling `sendMessage()` and include them in the context object.
2. Update `sendMessage()` in `aiAnalyst.js` to accept and forward the filter context to the POST body.
3. In `ai-analyst/app/tools/cube.py`, incorporate the forwarded filters into CubeJS query construction (or pass them to the agent instruction as a formatted string).
