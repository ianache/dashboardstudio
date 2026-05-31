# Project Retrospective: Dashboard Studio

---

## Milestone: v1.8 — BFF Service Architecture

**Shipped:** 2026-05-31
**Phases:** 5 (33-37) | **Plans:** 21 | **Commits:** ~42

### What Was Built

- Express 5 BFF containerized in `bff/` with Redis session store and HttpOnly cookie auth
- Full OIDC Authorization Code + PKCE flow via `openid-client` v6 — server-side, browser never sees tokens
- `tokenRefresh` middleware with concurrent refresh coordination (race-condition safe)
- FastAPI proxy at `/bff/api/*` with automatic Bearer injection from session
- CubeJS proxy at `/bff/cubejs/*` with HS256 JWT signing per-request server-side
- Backend and CubeJS removed from public Docker network (internal-only)
- Vue 3 SPA migrated: `keycloak-js` deleted, all traffic routed through BFF cookie session

### What Worked

- **Build order constraint respected:** Foundation → Auth → FastAPI proxy → CubeJS proxy → Frontend. Each phase was a clean dependency step, no backtracking.
- **Post-hoc summary verification:** Two phases (34, 35) had complete implementations but missing SUMMARY.md files. Quick code-vs-plan verification before closing avoided executing already-done work.
- **Redis over PostgreSQL for sessions:** The switch from `connect-pg-simple` to `connect-redis` (from the original plan) was the right call — TTL management and latency are both better.

### What Was Inefficient

- **Summary drift:** Several plans were implemented but their SUMMARY.md files were never created, causing GSD to report phases as incomplete. Should write summaries immediately after each plan execution.
- **REQUIREMENTS.md checkbox updates:** All 18 requirements were implemented but only 5 were checked off during execution. Requires a cleanup pass at milestone close.
- **No milestone audit:** Skipped `/gsd:audit-milestone` — acceptable for a well-tracked milestone but worth running next time to catch integration gaps early.

### Patterns Established

- **BFF-as-CORS-owner:** Stripping upstream CORS headers in `onProxyRes` as a safety net alongside BFF-owned CORS middleware is the correct pattern for all future proxy setups.
- **`activeRefreshes` Map for concurrent token refresh:** Pattern to prevent duplicate IdP calls when multiple requests arrive simultaneously for an expiring session.
- **`req.session.save()` before redirects:** Explicit session save before any redirect in OIDC flows — prevents race condition where Keycloak returns before Redis write completes.
- **Plain-serializable session tokens:** Store only primitive fields in session (not openid-client class instances) to ensure Redis serialization compatibility.

### Key Lessons

1. Verify implementation against plans before executing — avoids re-doing already-shipped work.
2. Write SUMMARY.md immediately after each plan — not at the end of the phase.
3. `openid-client` v6 is ESM-only — plan the ESM migration as a prerequisite phase, not a surprise.
4. Network isolation (removing public ports) is a separate phase from the proxy itself — the dependency order matters for testability.

### Cost Observations

- Model: sonnet (quality profile)
- Sessions: ~4 sessions across the milestone
- Notable: Post-hoc verification of already-implemented plans saved at least 2 full execution sessions

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Timeline | Notable |
|-----------|--------|-------|----------|---------|
| v1.6 | 3 | 6 | 1 day | ODSExecutor + 55 tests |
| v1.7 | 1 | 3 | 1 day | Email + Jinja2 + 44 tests |
| v1.8 | 5 | 21 | 3 days | Full BFF architecture |

**Trend:** Milestone scope is growing (6 → 21 plans). Phase granularity is working well — each phase is independently deployable and testable.
