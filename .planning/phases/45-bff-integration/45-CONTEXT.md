# Phase 45: BFF Integration - Context

## Objective
Enable secure access to the AI Analyst service from the frontend via the BFF.

## Core Requirements
- SVC-04: Secure proxy for AI chat service with session validation.

## Success Criteria
1. `POST /bff/ai/chat` with valid session forwards to `ai-analyst`.
2. 401 Unauthorized for requests without valid session.
3. User identity (sub) injected as `X-User-ID` header.
4. Screen context passed through without modification.
5. Support for streaming (SSE) without buffering.

## Technical Details
- **BFF URL**: `http://localhost:8000` (external), proxies to internal services.
- **AI Service URL**: `http://ai-analyst:8001` (internal Docker network).
- **Auth**: Uses existing `requireAuth` and `tokenRefresh` middleware in BFF.
- **SSE**: Requires `proxyTimeout: 0` and `timeout: 0` in `http-proxy-middleware`.

## File Map
- `bff/src/proxy.js`: Define and export `aiProxy`.
- `bff/src/index.js`: Mount `/bff/ai` route.
- `bff/.env-bff.example` & `environment/bi-backend.env`: Add `BFF_AI_URL`.
- `ai-analyst/app/main.py`: (Reference) `/chat` endpoint.
