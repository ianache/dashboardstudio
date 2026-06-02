---
created: 2026-06-02T04:11:54.582Z
title: BI AI Analyst summarize chat history when context exceeds 200kb
area: ui
files:
  - ai-analyst/app/main.py
  - ai-analyst/app/agent.py
  - dashboard-app/src/stores/aiAnalyst.js
---

## Problem

As a chat session grows (many back-and-forth exchanges, large CubeJS data payloads in context), the accumulated conversation history fed to the LLM can exceed the model's practical context window, leading to degraded responses, higher latency, and increased token costs. At ~200 KB of accumulated session content the risk of context overflow becomes significant.

## Solution

Implement automatic context summarization when the session payload exceeds 200 KB:

1. **Backend (`ai-analyst/app/main.py` or a new `session_manager.py`):** Before calling `active_runner.run_async()`, estimate the serialized size of the session history. If it exceeds 200 KB, trigger a summarization pass:
   - Call the LLM with the current history and a system prompt like: *"Summarize the conversation so far, preserving key findings, data points discussed, and open questions."*
   - Replace the session history with a single synthetic "assistant" message containing the summary.
   - Continue the original user request with the condensed history.

2. **Threshold:** 200 KB of raw session JSON. This is an approximation — actual token count depends on the model, but byte size is cheap to compute without a tokenizer.

3. **Frontend (`aiAnalyst.js`):** Optionally, when the backend emits a special SSE event (e.g., `{"type": "context_summarized"}`) the frontend can insert a visual divider in the chat: *"— Context summarized to keep responses sharp —"*

Note: This is related to the chat-history-per-dashboard-session todo — implement that first, as this builds on having a stable session.
