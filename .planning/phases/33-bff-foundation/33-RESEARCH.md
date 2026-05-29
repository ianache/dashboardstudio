# Phase 33: BFF Foundation - Research

**Researched:** 2026-05-28
**Domain:** Node.js Express 5 BFF service — Docker Compose scaffold, PostgreSQL-backed sessions, environment-variable configuration
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- BFF gets a public Traefik label and hostname in Phase 33: `dashboard-bff.pm.comsatel.com.pe`
- Entrypoint: `web-secure` with TLS (same as backend)
- Internal port: `3001`
- BFF joins both `frontends` and `backends` Docker networks (same pattern as the `backend` service)
- `frontend-app` service gets `depends_on: bff` added in Phase 33 (establishing the future dependency early)
- `SameSite=Lax` — BFF and frontend share the `.pm.comsatel.com.pe` parent domain
- Cookie name: `bff.sid`
- Cookie domain: `.pm.comsatel.com.pe` (shared across all `*.pm.comsatel.com.pe` subdomains so Phase 34 auth callbacks work seamlessly)
- Session TTL: 8 hours (maxAge = 28800000 ms)
- HttpOnly: true, Secure: true
- BFF gets its own `.env-bff` file (follows existing `.env-backend` pattern)
- `.env-bff` is gitignored; `.env-bff.example` with placeholder values is committed
- All BFF vars use `BFF_` prefix (e.g., `BFF_SESSION_SECRET`, `BFF_KEYCLOAK_URL`)
- BFF uses its own `BFF_POSTGRES_*` vars for the session store DB connection (same instance as backend, but independently declared)
- All BFF routes namespaced under `/bff/` prefix (e.g., `/bff/health`, future `/bff/auth/*`, `/bff/api/*`)
- Health check: `GET /bff/health` → `{ "status": "ok" }` JSON, 200
- Express server listens on port `3001` inside Docker

### Claude's Discretion
- Node.js image version (node:20-alpine, consistent with frontend build stage)
- npm as package manager (consistent with existing)
- Express app internal directory structure (`src/`, `src/routes/`, `src/middleware/`)
- Dockerfile multi-stage vs single-stage (single-stage is fine for a server)
- connect-pg-simple session table name (default `session` in the `biportal` schema is fine)
- Exact `BFF_POSTGRES_*` var names beyond the agreed prefix

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BFF-01 | User can access the dashboard app through a BFF service deployed as an Express 5 Node.js server | Express 5.2.1 setup patterns, single-stage node:20-alpine Dockerfile, port 3001 |
| BFF-02 | BFF service is containerized and included in docker-compose alongside backend, frontend, and CubeJS | Docker Compose service definition, Traefik labels pattern (reuses backend pattern), dual-network attachment |
| BFF-03 | Server-side sessions are persisted in PostgreSQL via `connect-pg-simple` with HttpOnly secure cookie delivered to browser | connect-pg-simple 10.0.0 + express-session 1.19.0 + pg 8.x; schemaName option for `biportal`; createTableIfMissing strategy |
| BFF-04 | BFF configuration is fully externalized via environment variables (Keycloak URLs, client credentials, session secret, CubeJS secret) | .env-bff pattern; BFF_ prefix; .env-bff.example committed; .env-bff gitignored |
</phase_requirements>

---

## Summary

Phase 33 scaffolds the BFF as a pure Node.js Express 5 server — no auth flows, no proxying, no frontend migration. The deliverables are: a working `bff/` directory with `package.json`, `Dockerfile`, and `src/`; an entry in `docker-compose.yaml`; a `.env-bff.example`; and a health endpoint at `GET /bff/health`. The BFF must prove it can start, serve a request, and write a session row to PostgreSQL before Phase 34 can build on it.

Express 5.2.1 is now the npm `latest` tag (since early 2025). The critical change from Express 4 is that rejected promises from async route handlers are automatically forwarded to error middleware — no manual `.catch(next)` needed. All new code should be written for Express 5 from the start since this is a greenfield service.

Session management uses the `express-session` 1.19.0 + `connect-pg-simple` 10.0.0 combination, which is the standard PostgreSQL-backed session store for Express. The `schemaName` option in connect-pg-simple places the `session` table inside the `biportal` schema alongside the backend tables. `createTableIfMissing: true` is acceptable for Phase 33 (avoids a separate migration step); Alembic is not used by Node.js services. Behind Traefik (TLS termination), Express must be told `app.set('trust proxy', 1)` so that `req.secure === true` and the `secure: true` cookie is actually sent to the browser.

**Primary recommendation:** Use `node:20-alpine`, single-stage Dockerfile, `express@5`, `express-session`, `connect-pg-simple`, and `pg`. Set `app.set('trust proxy', 1)` before the session middleware. Use `schemaName: 'biportal'` and `createTableIfMissing: true` in the session store config.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| express | 5.2.1 | HTTP server, routing | Now npm `latest`; async error handling built-in; greenfield = no migration cost |
| express-session | 1.19.0 | Session middleware, cookie issuance | Standard session layer for Express; pairs directly with pg store |
| connect-pg-simple | 10.0.0 | PostgreSQL session store | Minimal, well-maintained; supports schemaName for biportal; most-used pg store |
| pg | 8.21.0 | PostgreSQL client (Pool) | Required peer dep for connect-pg-simple; same driver used conceptually by backend |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dotenv | 16.x | Load .env-bff into process.env | Dev only — Docker Compose passes env vars directly in production via `env_file:` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| express-session + connect-pg-simple | better-sqlite3 session store | SQLite is not acceptable — existing DB is PostgreSQL; consistency required |
| pg Pool directly | DATABASE_URL conString | Pool preferred; conString also works but requires building URL from BFF_POSTGRES_* vars |
| node:20-alpine | node:22-alpine | CONTEXT.md specifies 20 (consistent with frontend build stage) |

**Installation:**
```bash
npm install express express-session connect-pg-simple pg
npm install --save-dev dotenv
```

---

## Architecture Patterns

### Recommended Project Structure
```
bff/
├── Dockerfile              # Single-stage node:20-alpine
├── package.json            # name: "dashboard-bff", main: "src/index.js"
├── .dockerignore           # node_modules, .env-bff
└── src/
    ├── index.js            # Entry point: create app, attach middleware, start server
    ├── config.js           # Read all BFF_* env vars, validate required, export frozen config object
    ├── session.js          # Build pg Pool + session store + express-session middleware
    └── routes/
        └── health.js       # GET /bff/health → { status: "ok" }
```

### Pattern 1: Config Module (Fail-Fast on Missing Env Vars)

**What:** All environment variables are read and validated in one place at startup. Missing required vars throw immediately rather than failing mysteriously later.
**When to use:** Any env-driven service. Critical here because BFF-04 requires no hardcoded values.

```javascript
// src/config.js
// Source: standard Node.js pattern
const required = (key) => {
  const val = process.env[key];
  if (!val) throw new Error(`Missing required env var: ${key}`);
  return val;
};

module.exports = Object.freeze({
  port: parseInt(process.env.BFF_PORT || '3001', 10),
  sessionSecret: required('BFF_SESSION_SECRET'),
  keycloakUrl: required('BFF_KEYCLOAK_URL'),
  keycloakRealm: required('BFF_KEYCLOAK_REALM'),
  keycloakClientId: required('BFF_KEYCLOAK_CLIENT_ID'),
  keycloakClientSecret: required('BFF_KEYCLOAK_CLIENT_SECRET'),
  cubejsSecret: required('BFF_CUBEJS_SECRET'),
  db: {
    host: required('BFF_POSTGRES_HOST'),
    port: parseInt(process.env.BFF_POSTGRES_PORT || '5432', 10),
    database: required('BFF_POSTGRES_DB'),
    user: required('BFF_POSTGRES_USER'),
    password: required('BFF_POSTGRES_PASSWORD'),
    schema: process.env.BFF_POSTGRES_SCHEMA || 'biportal',
  },
});
```

### Pattern 2: Session Middleware (connect-pg-simple + express-session)

**What:** Build a `pg.Pool`, pass it to `connect-pg-simple`, wrap in `express-session`. The pool is reused — do not create one Pool per request.
**When to use:** All routes need session state. Middleware is applied once in `index.js`.

```javascript
// src/session.js
// Source: connect-pg-simple README + express-session docs
const session = require('express-session');
const pgSession = require('connect-pg-simple')(session);
const { Pool } = require('pg');
const config = require('./config');

const pool = new Pool({
  host: config.db.host,
  port: config.db.port,
  database: config.db.database,
  user: config.db.user,
  password: config.db.password,
});

const sessionMiddleware = session({
  store: new pgSession({
    pool,
    tableName: 'session',
    schemaName: config.db.schema,   // 'biportal'
    createTableIfMissing: true,
    pruneSessionInterval: 900,      // prune expired rows every 15 min
  }),
  name: 'bff.sid',
  secret: config.sessionSecret,
  resave: false,
  saveUninitialized: false,
  proxy: true,
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    domain: '.pm.comsatel.com.pe',
    maxAge: 28800000,               // 8 hours in ms
  },
});

module.exports = { pool, sessionMiddleware };
```

### Pattern 3: Express App Bootstrap

**What:** Trust proxy must come BEFORE session middleware. Router mounts use the `/bff` prefix once.
**When to use:** Every Express app behind Traefik (TLS termination).

```javascript
// src/index.js
// Source: Express 5 docs + express-session trust proxy guidance
const express = require('express');
const { sessionMiddleware } = require('./session');
const healthRouter = require('./routes/health');

const app = express();
app.set('trust proxy', 1);   // MUST be before session middleware — Traefik terminates TLS

app.use(express.json());
app.use(sessionMiddleware);

app.use('/bff', healthRouter);

app.listen(3001, () => {
  console.log('BFF listening on :3001');
});
```

### Pattern 4: Dockerfile (single-stage, node:20-alpine)

**What:** Server app — no build step needed. Single stage keeps image small.
**When to use:** Node.js Express servers (no frontend bundling required).

```dockerfile
# bff/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY src/ ./src/

ENV NODE_ENV=production

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD wget -qO- http://localhost:3001/bff/health || exit 1

CMD ["node", "src/index.js"]
```

Note: `wget` is available in alpine; `curl` is not installed by default. Use `wget -qO-` for the health check command.

### Pattern 5: Docker Compose Service Definition

**What:** Mirrors the existing `backend` service pattern — same networks, same Traefik label structure, `env_file` pointing to `.env-bff`.
**When to use:** This exact pattern is locked by CONTEXT.md.

```yaml
# Addition to docker-compose.yaml
  bff:
    build:
      context: ./bff
      dockerfile: Dockerfile
    env_file:
      - ./.env-bff
    restart: unless-stopped
    labels:
      traefik.enable: true
      traefik.http.routers.bff.rule: Host(`dashboard-bff.pm.comsatel.com.pe`)
      traefik.http.routers.bff.entrypoints: web-secure
      traefik.http.routers.bff.tls: true
      traefik.http.services.bff.loadbalancer.server.port: 3001
    networks:
      - frontends
      - backends
```

And update `frontend-app` to add:
```yaml
    depends_on:
      - backend
      - bff
```

### Pattern 6: .env-bff.example

**What:** Committed example file. All keys documented. BFF_ prefix throughout.

```dotenv
# BFF Service Configuration
# Copy to .env-bff and fill in values — never commit .env-bff

# Server
BFF_PORT=3001

# Session
BFF_SESSION_SECRET=change-me-to-a-random-32-char-minimum-string

# Keycloak (used in Phase 34+)
BFF_KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe
BFF_KEYCLOAK_REALM=Apps
BFF_KEYCLOAK_CLIENT_ID=dashboard-bff
BFF_KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret

# CubeJS (used in Phase 36+)
BFF_CUBEJS_SECRET=your-cubejs-jwt-secret

# PostgreSQL (session store — same instance as backend, independent connection)
BFF_POSTGRES_HOST=<db-host>
BFF_POSTGRES_PORT=5432
BFF_POSTGRES_DB=biportal
BFF_POSTGRES_USER=biportal
BFF_POSTGRES_PASSWORD=your-db-password
BFF_POSTGRES_SCHEMA=biportal
```

### Anti-Patterns to Avoid

- **No `trust proxy` before session**: Behind Traefik, `req.secure` is `false` without it. The `secure: true` cookie is never sent to the browser. Silent failure — session appears to work in dev but breaks in production.
- **Creating pg.Pool inside the session store config but also outside**: One Pool for the entire app lifetime; connect-pg-simple accepts and reuses the `pool` option.
- **Using `saveUninitialized: true`**: Creates a session row (and sets a cookie) before any login. Wastes DB rows, sends a cookie to unauthenticated requests. Use `false`.
- **Using `resave: true`**: Deprecated default. Forces writes even when session unchanged. Use `false` — connect-pg-simple implements `touch()`.
- **Wildcard `*` in Express 5 routes**: Express 5 requires named wildcards (`*splat`). Using bare `*` causes a startup error. Not relevant for Phase 33 (only `/bff/health`) but must be known for Phase 34+.
- **Hardcoding `domain` cookie in development**: The `domain: '.pm.comsatel.com.pe'` cookie will not work on `localhost`. This is intentional — Phase 33 is production-targeted. Local dev uses `docker-compose up` with the full domain stack or no domain attribute.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PostgreSQL session store | Custom pg INSERT/SELECT/DELETE for sessions | connect-pg-simple | Handles session expiry, TTL pruning, race conditions, schema creation |
| Session cookie signing | Manual HMAC on cookie value | express-session `secret` option | Handles key rotation, cookie parsing, session ID generation |
| DB connection pooling | Single pg.Client reused | pg.Pool | Pool handles reconnects, connection limits, idle timeouts |
| Health check command in alpine | Install curl | Use `wget -qO-` (built into alpine) | `curl` not in alpine by default; `wget` is |

**Key insight:** The entire session lifecycle (creation, signing, storage, expiry, pruning) is handled by express-session + connect-pg-simple. Phase 33 has zero custom session code beyond wiring the middleware.

---

## Common Pitfalls

### Pitfall 1: Secure Cookie Not Sent Behind Traefik
**What goes wrong:** Browser never receives `bff.sid` cookie. Session is created on every request (no session persistence).
**Why it happens:** Express receives HTTP from Traefik (TLS terminated at Traefik). `req.secure === false`. express-session refuses to set `secure: true` cookie over HTTP.
**How to avoid:** Always set `app.set('trust proxy', 1)` before `app.use(sessionMiddleware)`. This makes Express read `X-Forwarded-Proto` from Traefik and set `req.secure = true`.
**Warning signs:** Every request creates a new session row in the DB. `Set-Cookie` header missing in browser dev tools.

### Pitfall 2: Session Table Schema Mismatch
**What goes wrong:** `connect-pg-simple` fails with "relation session does not exist" or creates the table in the `public` schema instead of `biportal`.
**Why it happens:** Default `schemaName` is `public` if not specified.
**How to avoid:** Always pass `schemaName: 'biportal'` (or `config.db.schema`). With `createTableIfMissing: true`, the store creates `biportal.session` on startup.
**Warning signs:** BFF starts but throws SQL errors on first session write; `\dt biportal.*` in psql doesn't show `session`.

### Pitfall 3: Package.json / node_modules Not Excluded From Docker Build Context
**What goes wrong:** Slow builds; local `node_modules` overwrite the container's installed modules.
**Why it happens:** No `.dockerignore`.
**How to avoid:** Create `bff/.dockerignore` with `node_modules`, `.env-bff`, `npm-debug.log`.
**Warning signs:** Build takes 30+ seconds even on cache rebuild; npm install errors about conflicting platform binaries.

### Pitfall 4: .env-bff Accidentally Committed
**What goes wrong:** DB password and session secret in git history.
**Why it happens:** The root `.gitignore` has `.env.*` but `.env-bff` may not match without the dot prefix. The existing pattern is `.env-backend` (no dot between name and env), which is NOT matched by `.env.*`.
**How to avoid:** Explicitly add `.env-bff` to `.gitignore` (the root `.gitignore` currently uses `.env.*` which catches `.env.something` but NOT `.env-bff`). Verify with `git status` after creating the file.
**Warning signs:** `git status` shows `.env-bff` as untracked instead of ignored.

### Pitfall 5: Cookie `domain` Breaks Local Dev
**What goes wrong:** In local `docker-compose` without the full `.pm.comsatel.com.pe` domain, the browser rejects the cookie (domain mismatch). Session appears broken.
**Why it happens:** `domain: '.pm.comsatel.com.pe'` in cookie config is a production setting.
**How to avoid:** This is expected and acceptable for Phase 33 — the BFF is production-targeted. Document in `README` or `.env-bff.example` that `BFF_COOKIE_DOMAIN` may need adjustment for local dev. Alternatively, make domain configurable via env var.
**Warning signs:** Works in production, fails completely locally.

### Pitfall 6: Express 5 Wildcard Syntax (Future Phases)
**What goes wrong:** Route `app.get('/*', ...)` throws a syntax error at startup in Express 5.
**Why it happens:** Express 5 requires named wildcards: `app.get('/*splat', ...)`.
**How to avoid:** Phase 33 only has `/bff/health` — no wildcards needed. But Phase 35 (proxy routes) will need this. Document now.
**Warning signs:** App crashes at startup with path pattern error.

---

## Code Examples

### Health Route
```javascript
// bff/src/routes/health.js
// Source: standard Express 5 pattern
const { Router } = require('express');
const router = Router();

router.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

module.exports = router;
```

### Session Write Verification (smoke test pattern)
```javascript
// Useful for manual verification that BFF-03 is working
// curl http://localhost:3001/bff/health → { status: 'ok' }
// Then check: SELECT * FROM biportal.session;
// Should show 0 rows (saveUninitialized: false — no session written without modification)
```

### .gitignore Addition
```gitignore
# BFF env
.env-bff
```

Note: The root `.gitignore` uses `.env.*` which matches `.env.example` but NOT `.env-bff`. Explicit entry is required.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `npm install express@4` (default) | `npm install express` installs 5.x (now `latest`) | Early 2025 | New services should use Express 5 directly |
| Manual `.catch(next)` in async routes | Express 5 auto-forwards rejected promises | Express 5.0 (Oct 2024) | Cleaner async/await without boilerplate |
| `express@5` tag on npm | `express` (no tag) | 2025 | No `@5` needed — `npm install express` gives 5.x |

**Deprecated/outdated:**
- `app.del()`: Removed in Express 5 — use `app.delete()`
- `res.json(obj, status)`: Removed — use `res.status(status).json(obj)`
- Bare `*` wildcard in routes: Removed — use `/*splat`
- `express-session` with `resave: true` default: Deprecated — always set `resave: false`

---

## Open Questions

1. **Does the PostgreSQL instance accept connections from the `bff` container on the `backends` network?**
   - What we know: Backend connects to PostgreSQL from the `backends` network. BFF will join the same network.
   - What's unclear: Whether PostgreSQL is itself on the `backends` external network or whether the backend uses host networking / a separate internal network.
   - Recommendation: Verify with `docker network inspect backends` before implementing. If PostgreSQL is reachable from `backends`, use `BFF_POSTGRES_HOST=<same host as POSTGRES_HOST in backend>`.

2. **Alpine `wget` vs `curl` for Dockerfile HEALTHCHECK**
   - What we know: `curl` is not installed in `node:20-alpine` by default. `wget` is available.
   - What's unclear: Whether the project's alpine variant (could be slim) has wget.
   - Recommendation: Use `wget -qO- http://localhost:3001/bff/health || exit 1`. If uncertain, add `RUN apk add --no-cache curl` and use curl. Both are valid.

3. **`createTableIfMissing: true` vs explicit SQL migration**
   - What we know: CONTEXT.md notes "default session in biportal schema is fine." Backend uses Alembic but BFF is a separate Node.js service.
   - What's unclear: Whether the team wants all DDL changes tracked in Alembic for the session table.
   - Recommendation: Use `createTableIfMissing: true` for Phase 33 (avoids adding a Node-owned SQL file to an Alembic workflow). If the team wants Alembic ownership, add the DDL from `node_modules/connect-pg-simple/table.sql` as an Alembic migration and set `createTableIfMissing: false`.

---

## Sources

### Primary (HIGH confidence)
- https://expressjs.com/en/guide/migrating-5.html — Express 5 breaking changes: async error handling, wildcard syntax, removed methods (fetched directly)
- https://github.com/voxpelli/node-connect-pg-simple/blob/main/README.md — connect-pg-simple options: pool, schemaName, tableName, createTableIfMissing, ttl (fetched directly)
- https://github.com/voxpelli/node-connect-pg-simple/blob/main/table.sql — Session table DDL (fetched directly)
- https://expressjs.com/en/resources/middleware/session/ — express-session options: secret, resave, saveUninitialized, cookie, proxy, name (fetched directly)

### Secondary (MEDIUM confidence)
- https://expressjs.com/2024/10/15/v5-release.html — Express 5.0 release announcement (Oct 2024); verified by npm version search showing 5.2.1 as latest
- WebSearch result: express-session 1.19.0 confirmed as latest (published ~4 months ago as of May 2026)
- WebSearch result: connect-pg-simple 10.0.0 confirmed as latest (published ~2 years ago — stable)
- WebSearch result: pg 8.21.0 confirmed as latest
- WebSearch result: `app.set('trust proxy', 1)` required behind Traefik for `req.secure` — verified by multiple sources including Express official docs

### Tertiary (LOW confidence)
- https://markaicode.com/nodejs-docker-optimization-2025/ — Node.js Docker best practices 2025 (single source, general guidance)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified from npm search results cross-referenced with official release announcements
- Architecture patterns: HIGH — drawn from official Express 5 docs, connect-pg-simple README, and direct project code inspection
- Pitfalls: HIGH — trust proxy pitfall verified by official Express docs + community; gitignore pitfall verified by direct inspection of project's .gitignore file
- Docker/Traefik patterns: HIGH — drawn from direct inspection of existing `docker-compose.yaml` and `backend/Dockerfile`

**Research date:** 2026-05-28
**Valid until:** 2026-06-28 (stable libraries; Express 5 ecosystem is maturing but API is stable)
