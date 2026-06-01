# Phase 46: Chat UI - Context

## Objective
Implement an interactive AI Analyst chat panel embedded in the Dashboard Designer to provide data insights and operational skills.

## Core Requirements
- CHAT-01: Collapsible AI Analyst panel in the designer.
- CHAT-02: Captures dashboard "screen context" (widget metadata/data) automatically.
- CHAT-03: Real-time response streaming (SSE).
- CHAT-04: Display usage metrics (tokens, cost) and thinking process.
- CHAT-05: Skill Call-to-Action (CTA) buttons in chat bubbles.

## Technical Details
- **Frontend Framework**: Vue 3 (Composition API).
- **State Management**: Pinia (new `aiAnalyst` store).
- **Styling**: Vanilla CSS, matching the existing "Stitch" design system (Material Symbols, flex layouts).
- **API**: Proxied via BFF at `/bff/ai/chat` (Phase 45).
- **SSE Handling**: Use `fetch` with `ReadableStream` for POST-based streaming.
- **Markdown**: Use `marked` + `dompurify` for safe rendering.

## File Map
- `dashboard-app/src/components/dashboard/AiAnalystPanel.vue`: Main UI component.
- `dashboard-app/src/stores/aiAnalyst.js`: Chat history, streaming logic, and context capture.
- `dashboard-app/src/views/DashboardDesignerView.vue`: Integration point for the panel and toggle button.
- `dashboard-app/src/components/dashboard/AiAnalystMessage.vue`: Sub-component for individual message bubbles with Thought/Action/Result sections.
