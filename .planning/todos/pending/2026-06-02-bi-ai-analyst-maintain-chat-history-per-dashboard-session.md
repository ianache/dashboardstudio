---
created: 2026-06-02T04:11:54.582Z
title: BI AI Analyst maintain chat history per dashboard session
area: ui
files:
  - dashboard-app/src/stores/aiAnalyst.js
  - dashboard-app/src/components/dashboard/AiAnalystPanel.vue
  - ai-analyst/app/main.py
---

## Problem

The AI Analyst chat currently creates a new session per request and holds no conversation history across messages within the same user session. Each message is treated as an isolated query, so the user cannot ask follow-up questions that build on prior context (e.g., "why?" after the first answer, or "now break that down by region").

Additionally, if the user switches between dashboards, they should get separate chat histories — the conversation for "Sales Dashboard" is irrelevant when they're on "Operations Dashboard".

## Solution

Implement per-dashboard chat session isolation with in-session memory:

1. **Frontend (`aiAnalyst.js`):** Use a `Map<dashboardId, Message[]>` structure instead of a single flat `messages` array. When `AiAnalystPanel` mounts, load the history for the current `dashboardId`. Clear/switch context when the dashboard changes.

2. **Frontend → Backend:** Pass a stable `session_id` (keyed by `dashboardId + userId`) in the POST `/chat` body so the backend ai-analyst service can accumulate conversation history within the same session.

3. **Backend (`ai-analyst/app/main.py`):** Instead of creating a new session per request (`uuid4()`), look up or create a session by the provided `session_id`. The `InMemorySessionService` already supports named sessions — just skip the `create_session` call if the session already exists and reuse it.

Note: Sessions are in-memory only; they reset on service restart. Persistence across page reloads or service restarts is out of scope for this todo.
