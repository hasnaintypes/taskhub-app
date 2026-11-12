# TaskHub

A multi-user task management system demonstrating secure session-based authentication,
backend-enforced role-based access control, Redis-backed dashboard caching, and
asynchronous email notifications via Celery.

**Stack:** Django 5 + Django REST Framework · Angular 19 (standalone components, Angular
Material) · PostgreSQL 16 · Redis 7 · Celery 5 · Docker Compose.

See `docs/ARCHITECTURE.md` for the system design (diagrams, data model, auth/CSRF flow,
caching and notification flows) and `docs/PLAN.md` for the milestone-by-milestone build log.

## Prerequisites

- Docker and Docker Compose (v2).
- Nothing else — Python, Node, Postgres and Redis all run inside containers.

## Setup

```bash
cp .env.example .env
docker compose up --build
```

This starts five services: `db` (Postgres), `redis`, `backend` (Django, runs migrations
automatically on start), `celery_worker`, and `frontend` (Angular dev server).

- Backend API: http://localhost:8000/api/
- Django admin: http://localhost:8000/admin/
- Frontend: http://localhost:4200/

Seed three demo accounts (Admin, Manager, two Employees) once the backend is up:

```bash
docker compose exec backend python manage.py seed_demo_users
```

All seeded accounts use the password `DemoPass123!` — usernames are `admin`, `manager`,
`employee1`, `employee2`.

## Running tests

Backend (26 tests — covers every row of the assessment's minimum test table: auth,
CSRF, RBAC, IDOR, cache hit/invalidation/outage-fallback, and Celery idempotency):

```bash
docker compose exec backend pytest -v
```

Frontend (standalone-component unit tests) — run on the host, not inside the `frontend`
container: it's a slim `node:22-alpine` image with no Chrome installed, so Karma/Chrome
Headless can't launch there.

```bash
cd frontend
npm install
npm test -- --watch=false --browsers=ChromeHeadless
```

Both suites were also run locally against the real Dockerized Postgres/Redis during
development — see `docs/PLAN.md` for the verification log per milestone.

## Architecture notes

- **Auth**: Django session authentication. Angular reads the (non-HttpOnly) `csrftoken`
  cookie and submits it via the `X-CSRFToken` header on every state-changing request
  (`core/interceptors/api.interceptor.ts`). See `docs/ARCHITECTURE.md` §4 for the full
  sequence diagram.
- **RBAC**: a `role` field on the custom `User` model (Admin/Manager/Employee) rather than
  Django Groups — documented deviation, see `docs/ARCHITECTURE.md` §2. Every permission is
  enforced in DRF permission classes on the backend; Angular route guards are a UX
  convenience only and are never the security boundary.
- **Caching**: `GET /api/dashboard/stats/` is cached per-user-id in Redis with a 300s TTL.
  A Redis outage falls back straight to a scoped DB query rather than failing the request.
  See `docs/ARCHITECTURE.md` §6.
- **Notifications**: assigning a task creates a `TaskAssignmentEvent` row in the same
  transaction as the assignment, and the Celery job is enqueued only via
  `transaction.on_commit` — so a rolled-back assignment never sends a notification. A
  retried delivery of the same event is suppressed by a `notified` flag checked under
  `select_for_update`; a genuinely new assignment (including a later reassignment) is a new
  event and is always eligible to send. See `docs/ARCHITECTURE.md` §5.
- **Email**: Django's console backend is used, per the assessment's own guidance — assigned
  task emails are printed to the `celery_worker` container's logs
  (`docker compose logs -f celery_worker`).

## Assumptions and trade-offs

Documented in full, with requirement-ID traceability, in `docs/REQUIREMENTS.md` (an
internal planning document, not tracked in Git — ask for the current copy if reviewing
outside this repository). The load-bearing ones:

- An assignee may update only a task's `status` field; Admin/Manager may edit any field.
  Reassignment only happens through `POST /api/tasks/{id}/assign/`, never through the
  general `PATCH` endpoint — this is what guarantees every reassignment creates a
  notification event (see `docs/ARCHITECTURE.md`'s decisions table).
- Task status is a three-value enum (`pending` / `in_progress` / `completed`); the brief
  only names `completed_tasks` and `pending_tasks` in the dashboard response.
- A Manager has the same task create/assign/view-all scope as Admin, differing only in
  delete rights and user administration — the brief's permission matrix shows no narrower
  scope for Manager on those rows.
- DRF's `SessionAuthentication` returns 403 for both "not logged in" and "logged in but
  forbidden" by default; this backend restores 401 specifically for "not logged in" so the
  frontend can reliably distinguish "redirect to login" from "show a permission error."

## Known limitations / not implemented

- No password reset, email verification, or rate limiting on login — not required by the
  assessment brief; noted as optional hardening.
- No task due dates, priority, filtering/search UI, or pagination UI beyond the API's
  default page size (25) — out of scope per the brief's explicit priority on
  correctness/security over feature breadth.
- The Angular UI is functional but not visually polished, consistent with the brief's
  explicit statement that "production-level visual polish is not required."
