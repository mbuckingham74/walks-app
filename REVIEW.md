# Walks Tracker — Code Review Recommendations

Reviewed: 2026-07-06

Check off items as they are completed. Each item is self-contained enough to be addressed in a separate context window.

---

## CRITICAL — Security (Do First)

- [x] **1. Redact plaintext credentials in `.walks_project_plan.md`**
  - File: `.walks_project_plan.md` (lines 222–233, 316–317)
  - Contains plaintext Garmin password, MySQL passwords, and NPM credentials
  - Action: Delete the credentials or redact them with placeholders. Consider whether this file should exist at all.

- [x] **2. Add authentication to `POST /api/steps`**
  - File: `walks-app/backend/app/main.py:475`
  - Currently anyone on the internet can inject fake step data for any date within a 730-day window
  - Action: Require a shared secret (e.g., check for a header like `X-Shortcut-Secret` matching an env var). The iOS Shortcut can include this header.

- [x] **3. Set a real `API_KEY` in production `.env`**
  - File: `walks-app/.env`
  - Currently set to `your_secure_api_key_here` — the `/api/activities` endpoint is effectively unprotected
  - Action: Generate a strong random key (e.g., `openssl rand -hex 32`) and set it in the production `.env`

- [x] **4. Separate MySQL root and app passwords; stop leaking root password to API container**
  - File: `walks-app/.env`, `walks-app/docker/docker-compose.yml`
  - `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` are identical. The API container receives `MYSQL_ROOT_PASSWORD` via `env_file` even though it never needs it.
  - Action: Generate a separate root password. Create a dedicated `env_file` for the MySQL container that includes root credentials, and a separate one (or filtered env) for the API container that only includes app credentials.

---

## HIGH — Security & Bugs

- [x] **5. Add rate limiting to GET API endpoints**
  - File: `walks-app/frontend/nginx.conf:36-46`
  - `/api/stats`, `/api/steps`, `/api/route`, `/api/config` have no rate limiting
  - Action: Add a `limit_req_zone` for read endpoints (e.g., `rate=30r/s`) and apply it to the `/api` location block

- [x] **6. Increase `stats_json` column from `VARCHAR(4000)` to `TEXT`**
  - Files: `walks-app/backend/schema.sql`, `walks-app/backend/app/models.py:57`
  - If the stats response grows, JSON gets silently truncated mid-string and `json.loads()` throws a 500
  - Action: Change column type to `TEXT` in both schema.sql and the ORM model. Run `ALTER TABLE stats_cache MODIFY stats_json TEXT NOT NULL` on production.

- [x] **7. Add a React error boundary**
  - File: `walks-app/frontend/src/App.jsx`
  - Any render crash produces a white screen with no recovery
  - Action: Create an `ErrorBoundary` component and wrap the `<Routes>` block. Show a user-friendly error message with a reload button.

- [x] **8. Limit initial step data fetch range on Dashboard**
  - File: `walks-app/frontend/src/components/Dashboard.jsx:21`
  - `useSteps('2000-01-01', ...)` fetches the entire history on every page load
  - Action: Fetch only the current year's data by default. Load historical data on demand (e.g., when "All" range is selected in the chart).

- [x] **9. Display API error states on Dashboard**
  - File: `walks-app/frontend/src/components/Dashboard.jsx:26`
  - All hook error states are silently ignored — if the API is down, user sees an empty dashboard
  - Action: Destructure `error` from each hook and display a banner or toast when any fetch fails.

- [x] **10. Add HSTS header at TLS termination point**
  - File: `walks-app/docker/nginx.conf`
  - No `Strict-Transport-Security` header on the HTTPS server block
  - Action: Add `add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;` to the `listen 443` server block

- [x] **11. Add `.dockerignore` for frontend**
  - File: `walks-app/frontend/` (missing)
  - Without it, `node_modules`, `.git`, `.env`, IDE files may be copied into Docker image layers
  - Action: Create `frontend/.dockerignore` excluding `node_modules`, `.git`, `.env*`, `dist`, `*.md`, IDE files

- [x] **12. Strengthen SSL cipher suite**
  - File: `walks-app/docker/nginx.conf:18`
  - Only two 128-bit ciphers are configured
  - Action: Use Mozilla's "Intermediate" profile cipher string, including 256-bit ciphers (AES256-GCM-SHA384, CHACHA20-POLY1305)

---

## MEDIUM — Code Quality & Architecture

- [x] **13. Align step goal to a single value across DB, config, and docs**
  - Files: `walks-app/backend/schema.sql` (default 10000), `walks-app/backend/app/models.py:35` (default 10000), `walks-app/backend/app/config.py` (15000), `walks-app/DASHBOARD.md` (says 10000), `walks-app/CLAUDE.md` (says 15000)
  - Action: Pick one value. Update the DB default, model default, config default, and all documentation to match.

- [x] **14. Delete dead code**
  - Files to delete:
    - `walks-app/frontend/src/components/StepsDetail2025.jsx` — superseded by `StepsDetail.jsx`
    - `walks-app/frontend/src/components/StepsDetail2026.jsx` — superseded by `StepsDetail.jsx`
  - Code to remove:
    - `walks-app/backend/app/main.py` — `_get_all_time_steps()` function (never called)
    - `walks-app/backend/app/schemas.py` — `StatsSchema`, `PositionSchema` classes (never used as response models, and out of sync with actual response shape)
    - `walks-app/backend/app/models.py` — `RouteProgress` model (table exists but is never read/written)
    - `walks-app/backend/app/main.py:20` — `RouteProgress` import

- [x] **15. Consolidate duplicate aggregate queries in stats computation**
  - File: `walks-app/backend/app/main.py`
  - `_compute_data_hash()` and `_compute_stats()` run nearly identical DB queries (8+ redundant round-trips on cache miss)
  - Action: Extract shared query logic into a single function that returns all aggregates, then use results for both hash computation and stats response.

- [x] **16. Defer engine creation to FastAPI lifespan**
  - File: `walks-app/backend/app/database.py:12-14`
  - `get_settings()` and `create_async_engine()` run at import time, before the lifespan handler
  - Action: Move engine creation into an `init_engine()` function called from the lifespan. This makes testing easier and errors occur during controlled startup.

- [x] **17. Add basic test suite**
  - No tests exist for backend or frontend
  - Action: Add pytest tests for at minimum: route calculation (`route.py`), stats computation, schema validation, and API endpoint smoke tests. Add a `tests/` directory and a CI config.

- [ ] **18. Enable `pool_pre_ping` or add connection retry logic**
  - File: `walks-app/backend/app/database.py:24`
  - `pool_pre_ping=False` means stale MySQL connections cause 500 errors instead of being recycled
  - Action: Investigate aiomysql compatibility with pre_ping. If truly incompatible, add a retry decorator on DB operations that catches `OperationalError` and retries once.

- [x] **19. Remove duplicate and redundant indexes from schema**
  - File: `walks-app/backend/schema.sql`
  - `idx_activity_date` and `idx_activity_year` both index `activity_date` (line 23-24)
  - `stats_cache`, `route_progress`, and `daily_steps` have explicit indexes on columns that already have UNIQUE constraints (which create implicit indexes)
  - Action: Remove `idx_activity_year`, `idx_stats_year`, `idx_progress_year`, and `idx_step_date`

- [x] **20. Add engine disposal on shutdown**
  - Files: `walks-app/backend/app/main.py`, `walks-app/backend/app/database.py`
  - The lifespan handler initializes the DB but never calls `engine.dispose()` on shutdown, leaving dangling connections
  - Action: Add `await engine.dispose()` in the shutdown portion of the lifespan context manager

- [x] **21. Fix `datetime.utcnow()` deprecation**
  - File: `walks-app/backend/app/main.py:555`
  - Health check uses deprecated `datetime.utcnow()` while rest of codebase uses timezone-aware datetimes
  - Action: Replace with `datetime.now(APP_TIMEZONE)` or `datetime.now(timezone.utc)`

- [x] **22. Add downsampling to StepsChart "All" range**
  - File: `walks-app/frontend/src/components/StepsChart.jsx:80-94`
  - "All" range renders a data point for every single day from earliest record to today — thousands of SVG points
  - Action: When range is "All" and data exceeds ~365 points, aggregate to weekly or monthly averages

- [x] **23. Extract shared `useFetch` hook**
  - Files: `walks-app/frontend/src/hooks/useConfig.js`, `useStats.js`, `useRoute.js`, `useSteps.js`
  - All four hooks contain nearly identical fetch-with-AbortController boilerplate
  - Action: Create a generic `useFetch(url, options)` hook and refactor the four hooks to use it

- [x] **24. Add `dist/` to frontend `.gitignore`**
  - File: `walks-app/frontend/` (build artifacts committed to submodule)
  - Action: Add `dist/` to `.gitignore` and remove from git tracking with `git rm -r --cached dist/`

---

## LOW — Minor Issues

- [ ] **25. Remove unused imports in `main.py`**
  - File: `walks-app/backend/app/main.py`
  - `Decimal` (line 7), `text` (line 14 — if f-string pattern is removed), `RouteProgress` (line 20) are unused

- [ ] **26. Remove unnecessary TypeScript devDependencies**
  - File: `walks-app/frontend/package.json`
  - `@types/react` and `@types/react-dom` are listed but the project uses plain `.jsx`/`.js`

- [ ] **27. Add ESLint and Prettier configuration**
  - File: `walks-app/frontend/` (missing)
  - No linter or formatter config exists. Code style consistency relies on developer discipline.
  - Action: Add `.eslintrc.cjs` and `.prettierrc` with sensible defaults for React + JSX

- [ ] **28. Add `jsconfig.json` for IDE support**
  - File: `walks-app/frontend/` (missing)
  - Without it, IDE features like "Go to Definition" and import auto-complete may not work
  - Action: Add `jsconfig.json` with `"baseUrl": "./src"` and path aliases

- [ ] **29. Pin `lucide-react` and `react-router-dom` to stable versions**
  - File: `walks-app/frontend/package.json`
  - `lucide-react@^0.330.0` is pre-1.0 (breaking changes in minor bumps)
  - `react-router-dom@^7.10.1` caret range could pull in breaking changes
  - Action: Pin to exact versions or use `~` instead of `^`

- [ ] **30. Use Tailwind theme colors in chart instead of hardcoded hex**
  - File: `walks-app/frontend/src/components/StepsChart.jsx:169-170, 198-202`
  - Chart stroke/gradient colors hardcoded to `#16a34a`
  - Action: Read colors from CSS custom properties or Tailwind config

- [ ] **31. Extract duplicated utility functions**
  - `parseLocalDate` is defined independently in `StatsCards.jsx:4` and `StepsDetail.jsx:8`
  - `formatDate` is defined in `StepsDetail.jsx:13` and duplicated in dead code files
  - Action: Create `src/lib/dates.js` and import from a single source

- [ ] **32. Fix `deploy.sh` SSH host key verification**
  - File: `walks-app/deploy.sh`
  - Uses `StrictHostKeyChecking=accept-new` which auto-accepts first host key (MITM risk)
  - Action: Pin the host key fingerprint in `known_hosts` and set `StrictHostKeyChecking=yes`

- [ ] **33. Add Docker container hardening**
  - File: `walks-app/docker/docker-compose.yml`
  - No `read_only`, `mem_limit`, `security_opt`, or `cap_drop` on any service
  - Action: Add `read_only: true` with tmpfs mounts, `security_opt: ["no-new-privileges:true"]`, `cap_drop: ["ALL"]`, and resource limits

- [ ] **34. Run frontend nginx as non-root**
  - File: `walks-app/frontend/Dockerfile`
  - Backend correctly uses non-root user; frontend nginx runs as root
  - Action: Configure nginx to run on a high port with non-root user (requires custom nginx config)

- [ ] **35. Add CSP header to static asset nginx location block**
  - File: `walks-app/frontend/nginx.conf:54-62`
  - Static asset block re-adds most security headers but omits `Content-Security-Policy`
  - Action: Add `add_header Content-Security-Policy "..." always;` to the static asset block

- [ ] **36. Externalize Matomo analytics site ID**
  - File: `walks-app/frontend/index.html:20`
  - Site ID `12` and tracker URL hardcoded
  - Action: Inject via environment variable or nginx `sub_filter` at deploy time

- [ ] **37. Fix `.env` comment about `API_KEY` usage**
  - File: `walks-app/.env`
  - Comment says "required for POST /api/steps and /api/sync* endpoints" but `POST /api/steps` is currently public
  - Action: Update comment to accurately reflect which endpoints use the key

- [ ] **38. Add `STEPS_PER_MILE` to production `.env`**
  - File: `walks-app/.env`
  - Present in `.env.example` but missing from `.env`. App falls back to default, but should be explicit.

- [ ] **39. Add `client_max_body_size` to nginx configs**
  - Files: `walks-app/frontend/nginx.conf`, `walks-app/docker/nginx.conf`
  - No explicit body size limit. Nginx default is 1MB, but should be explicitly set for the public write endpoint.
  - Action: Add `client_max_body_size 1m;` to the server block

- [ ] **40. Decouple frontend healthcheck from backend**
  - File: `walks-app/docker/docker-compose.yml`
  - Frontend healthcheck probes `/api/health` which depends on backend being up
  - Action: Change to probe `/` (static content) so frontend health is independent of backend
