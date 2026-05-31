---
phase: 35
plan: 02
subsystem: bff, backend
tags: ["bff", "cors", "fastapi", "cleanup"]
dependency_graph:
  requires: ["35-01"]
  provides: ["CORS-01"]
  affects: ["bff", "backend"]
tech_stack:
  added: ["cors"]
  patterns: ["BFF-owned CORS", "Single CORS Owner"]
key_files:
  created: []
  modified: ["bff/package.json", "bff/src/index.js", "backend/app/main.py"]
  deleted: []
decisions:
  - "BFF is the sole owner of CORS — backend is CORS-agnostic. Prevents duplicate/conflicting headers."
  - "onProxyRes strips any residual CORS headers from upstream responses as a safety net."
metrics:
  duration: "verified post-hoc"
  completed_date: "2026-05-30"
---

# Phase 35 Plan 02: CORS Consolidation Summary

Made the BFF the sole owner of CORS headers and removed all CORS handling from the FastAPI backend.

## Key Changes

### 1. `bff/package.json`
- Added `cors@^2.8.6` dependency.

### 2. `bff/src/index.js`
- Configured `cors` middleware with `config.spaOrigins` (allows multiple SPA origins), `credentials: true`, and explicit `methods` and `allowedHeaders`.
- Applied before all routes so every response carries the correct CORS headers.

### 3. `backend/app/main.py`
- Removed `CORSMiddleware` import and `app.add_middleware(CORSMiddleware, ...)`.
- Removed any manual CORS header injection from `global_exception_handler`.
- FastAPI now returns responses without CORS headers — the BFF proxy strips any accidental residual headers via `onProxyRes`.

## Deviations from Plan

None — all changes implemented exactly as specified.

## Verification Results

- `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` are set exclusively by the BFF.
- No duplicate CORS headers on proxied responses (stripped in `proxy.js` `proxyRes` handler).
- FastAPI backend responds correctly without CORS configuration.

## Self-Check: PASSED
- [x] cors package added to bff/package.json
- [x] cors middleware configured in index.js with spaOrigins and credentials: true
- [x] CORSMiddleware removed from backend/app/main.py
- [x] No manual CORS headers in global_exception_handler
- [x] proxy.js strips residual CORS headers from upstream responses
