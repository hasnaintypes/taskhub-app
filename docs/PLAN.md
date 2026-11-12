# TaskHub — Implementation Plan

Phased, milestone-based roadmap for an 8–12 hour build. See `docs/ARCHITECTURE.md` for design and `docs/REQUIREMENTS.md` for requirement IDs. Each milestone is independently runnable/testable — we verify before moving on.

**Rule for every milestone:** implement → run tests → check acceptance criteria → note any deviation → only then move to next milestone. No commits without explicit approval (see root `CLAUDE.md` once written).

---

## M0 — Scaffolding (~0.5h)
**Objective:** runnable skeleton, nothing functional yet.
- `backend/`: Django project (`config`), apps `accounts`, `tasks`, `dashboard`, `notifications`; `requirements.txt` (Django, DRF, psycopg2, django-redis, celery, django-cors-headers, pytest-django).
- `frontend/`: Angular standalone-component app (`ng new` equivalent), base routing shell.
- `docker-compose.yml`: postgres, redis, backend, celery worker, frontend (dev servers).
- `.env.example`, settings split (env-driven secret key, DB URL, Redis URL, CORS origin, Celery broker).
- **Acceptance:** `docker-compose up` brings up all 5 services; Django admin loads; Angular default page loads.

## M1 — Auth & sessions (~1.5h) [AUTH-01…13, SEC-01/02/03]
- Custom `User` model (`role` field) + migration; `accounts` app.
- Views: `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/me/`, `GET /api/auth/session/`.
- Settings: session cookie flags, CSRF settings, CORS allowed origin + credentials.
- **Tests:** valid/invalid login, anonymous access rejected, logout invalidates session, CSRF-missing request rejected.
- **Acceptance:** can log in via `curl`/Postman with cookie jar, CSRF round-trip works, protected endpoint returns 401 when logged out.

## M2 — RBAC & user management (~1h) [RBAC-01/02/08/09/11, SEC-05]
- Seed 3 roles via management command/fixture (one Admin, one Manager, two Employees for testing).
- `GET /api/users/` (Admin/Manager), `POST /api/users/` (Admin only).
- Permission classes: `IsAdmin`, `IsAdminOrManager`.
- **Tests:** Manager blocked from create-user (403), Employee blocked from user list (403), role immutability (user can't PATCH own role).
- **Acceptance:** permission matrix §1.2 verified for the user-management rows specifically.

## M3 — Task domain & object-level RBAC (~1.5h) [RBAC-03…07/10, QA-04]
- `Task` model + migration, serializers (restricted field set per role on write).
- `GET/POST /api/tasks/`, `GET/PATCH/DELETE /api/tasks/{id}/`.
- Object-level permission (`IsTaskVisible`, `CanEditTaskFields`, `CanDeleteTask`) + queryset filtering by role.
- **Tests:** Employee can't list others' tasks, Employee can't delete (403), Employee can only PATCH `status` on own task, IDOR attempt on another user's task ID rejected, Manager can edit/view all tasks but not delete.
- **Acceptance:** full CRUD matrix from §1.2 (minus assign/dashboard) enforced and tested.

## M4 — Assignment + Celery notifications (~1.5h) [CELERY-01…11]
- `TaskAssignmentEvent` model + migration.
- `POST /api/tasks/{id}/assign/` — creates event row inside the same transaction as the assignment, enqueues via `transaction.on_commit`.
- Celery app config (Redis broker), `notifications` app task `send_assignment_email(event_id)` with `select_for_update` idempotency guard, `autoretry_for`, logging.
- Console email backend.
- **Tests:** transaction-rollback never enqueues; duplicate task execution (same event_id) sends one email; reassignment creates new event and sends a new email; retry path triggers logging.
- **Acceptance:** assign call returns immediately (202-style payload), worker log shows one send per genuine event.

## M5 — Redis dashboard caching (~1.5h) [CACHE-01…07]
- `dashboard` app: `GET /api/dashboard/stats/`, scoped query per role (§1.3 table).
- Cache service: `dashboard:stats:v1:user:<id>` key, 300s TTL, explicit `cache.delete` calls wired into M3/M4 mutation paths (create/update/assign/delete).
- Redis-outage fallback (catch connection errors → direct DB query).
- **Tests:** second request within TTL hits cache (mock/spy or TTL-timing check), mutation invalidates the right keys, simulated Redis-down still returns correct scoped data, role change invalidates stale authorization (not just stale numbers).
- **Acceptance:** dashboard numbers match `REQUIREMENTS.md` CACHE-02 table for each seeded role; Redis-down test passes.

## M6 — Angular frontend (~3h) [FE-01…13]
- `core`: HTTP interceptor (credentials + CSRF header + 401→redirect), auth guard, typed API services, shared models.
- `auth`: login page/service, session bootstrap.
- `dashboard`: stat tiles, loading/empty/error states.
- `tasks`: list, details (role-restricted fields), creation form, assign action.
- `users`: list (Admin/Manager), create form (Admin only).
- **Verification:** manual walkthrough as each of the 3 seeded roles — every UI action that should be hidden is hidden, and the same action attempted directly against the API is still rejected.
- **Acceptance:** all 6 screens functional per `REQUIREMENTS.md` §1.5; no console errors; expired-session flow redirects with message.

## M7 — Hardening, docs, submission polish (~1h) [QA-01…10, SUB-01…07]
- Finish `README.md` (setup, run, test commands, architecture notes, assumptions/trade-offs — pointing at `docs/ARCHITECTURE.md` for depth).
- Finalize `docker-compose.yml` + `.env.example`.
- Run full test suite, fix any gaps flagged by `docs/testing-strategy.md` (write that doc here if not already present).
- Final security pass: no secrets committed, no wildcard CORS, confirm `.gitignore` still excludes confidential docs.
- **Acceptance:** clean checkout → `docker-compose up` → tests pass → README accurate end to end.

---

## Sequencing notes
- M1→M2→M3 are strictly sequential (each depends on the User/Task models before it).
- M4 depends on M3 (needs `Task`); M5 depends on M3+M4 (invalidation hooks reference both mutation paths).
- M6 can start on auth/core (interceptor, login) as soon as M1 is done, in parallel with M2–M5 backend work, then wire up each feature screen as its backend lands.
- M7 runs continuously in small slices (README notes, tests) rather than only at the end — but a final pass closes it out.

## Status tracking
Progress is tracked here as milestones complete — update the checkbox and one-line note after each.

- [x] M0 — Scaffolding — Django project + 4 apps via real `django-admin`/`manage.py` commands; Angular 19 standalone app via `ng new`; Angular Material added; Docker Compose (Postgres/Redis/backend/celery/frontend) up and verified.
- [x] M1 — Auth & sessions — login/logout/me/session live; CSRF cookie + header flow verified end-to-end via curl against the real stack; session cookie flags set (HttpOnly, SameSite=Lax, Secure in prod).
- [x] M2 — RBAC & user management — role field + IsAdmin/IsAdminOrManager; manager blocked from user creation verified by test.
- [x] M3 — Task domain & object-level RBAC — Task model, scoped queryset, IsTaskVisible/CanDeleteTask/CanCreateOrAssignTask; IDOR + status-only-edit verified by test and manual curl.
- [x] M4 — Assignment + Celery notifications — TaskAssignmentEvent idempotency table, `transaction.on_commit` enqueue, console email delivered and logged against the real Celery worker + Redis broker; retry-suppression and rollback-never-enqueues verified by test.
- [x] M5 — Redis dashboard caching — scoped stats, cache hit/invalidate verified by test, Redis-outage fallback verified live (stopped the Redis container, endpoint still returned correct scoped data).
- [x] M6 — Angular frontend — all 6 screens (login, dashboard, task list/detail/create, users) built as standalone components with Angular Material; HTTP interceptor + guards wired; verified end-to-end in a real browser against the live stack as both Admin and Employee (caught and fixed a status-update response bug and an auth-guard race condition on page reload along the way).
- [ ] M7 — Hardening, docs, submission polish

**Backend test suite:** 26/26 passing (`pytest`) against the real Dockerized Postgres + Redis, covering every row of the brief's minimum test table.
**Frontend:** `ng build` and `ng test` both clean; manual browser walkthrough covered login/logout, session-expiry redirect, dashboard scoping, task create/assign/status-update, and role-based nav/route visibility for Admin and Employee.
