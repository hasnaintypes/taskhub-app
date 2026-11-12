# TaskHub — Testing Strategy

Maps the assessment's minimum test expectations (and this project's own `REQUIREMENTS.md`
IDs) to the actual automated tests. All backend tests run against the real Dockerized
Postgres and Redis — nothing here is mocked at the infrastructure level; mocks are used
only to isolate a single unit's behavior (e.g. spying on `_compute_stats` to prove a cache
hit skipped recomputation).

## Coverage map

| Assessment test | Requirement ID(s) | Test |
|---|---|---|
| Valid / invalid login | AUTH-01 | `accounts/tests.py::TestAuthentication::test_valid_login_establishes_session`, `test_invalid_login_is_rejected` |
| Anonymous or expired session | AUTH-05, AUTH-13 | `test_anonymous_access_to_private_api_is_rejected` |
| Logout | AUTH-02 | `test_logout_invalidates_session` |
| CSRF validation | AUTH-09, SEC-02 | `test_state_changing_request_without_csrf_token_is_rejected` |
| Role permissions (user mgmt) | RBAC-02 | `TestUserManagementRBAC::*` (3 tests) |
| Role permissions (tasks) | RBAC-01...09 | `tasks/tests.py::TestTaskRBAC::*` (8 tests) |
| Employee deletes a task | RBAC-07 | `test_employee_deleting_a_task_is_rejected` |
| Employee reads another user's task | RBAC-10, SEC-04 | `test_employee_reading_another_users_task_is_rejected` |
| Role/permission change | CACHE-06, SEC-06 | `dashboard/tests.py::test_role_change_does_not_serve_stale_authorization` |
| Repeated dashboard request | CACHE-03 | `test_repeated_request_is_served_from_cache` |
| Task modification/assignment invalidates cache | CACHE-04 | `test_task_mutation_invalidates_cache`, `tasks/tests.py::test_admin_general_edit_invalidates_dashboard_cache` |
| Redis unavailable | CACHE-07 | `test_redis_outage_falls_back_to_db_without_exposing_unauthorized_data` |
| Task assignment queued only after commit | CELERY-03/04 | `tasks/tests.py::TestAssignmentAndNotifications::test_assign_persists_before_enqueue_and_only_after_commit`, `test_rolled_back_assignment_never_enqueues` |
| Repeated task execution doesn't duplicate-notify | CELERY-08 | `test_repeated_delivery_of_same_event_does_not_duplicate_notify` |
| Reassignment is a new, notifiable event | CELERY-09 | `test_reassignment_creates_a_new_event_eligible_to_notify` |

Two tests go beyond the brief's minimum list, added after bugs they would have caught:

- `test_admin_cannot_reassign_via_generic_patch` — guards against `assigned_to` being
  writable on the general `PATCH` endpoint, which would let a reassignment silently skip
  the notification pipeline.
- `test_admin_general_edit_invalidates_dashboard_cache` — guards against an Admin/Manager
  field edit bypassing cache invalidation (the Employee status-update path and the
  create/assign/delete paths were covered from the start; this one wasn't until review).

## Why `django_capture_on_commit_callbacks`

`pytest-django`'s `django_db` fixture wraps each test in a transaction that is always
rolled back, never committed — so `transaction.on_commit` callbacks registered during a
test never fire by default, which would make it impossible to actually test CELERY-03/04
("enqueue only after commit"). Tests that need to observe `on_commit` behavior use
pytest-django's `django_capture_on_commit_callbacks(execute=True)` fixture, which captures
and manually executes those callbacks without requiring a real commit.

## Why an autouse cache-clearing fixture

Redis is real external state, not rolled back with the test database between tests or
between separate `pytest` invocations. Because fixture-created user IDs are deterministic
per run (Django recreates the test database, resetting sequences, at the start of each
`pytest` session), a dashboard-cache entry left over from a previous run can produce a
false cache hit in the next run for a user that happens to get the same ID. `conftest.py`'s
autouse `clear_cache` fixture flushes Redis before and after every test to keep the suite
deterministic — this was caught by the suite actually failing intermittently, not by
inspection.

## Frontend tests

`ng test` covers `AppComponent`'s core routing-shell behavior (nav bar hidden while
unauthenticated). Given the assessment's point allocation (Angular frontend is evaluated on
working flows and correct API integration, not component-test coverage), the primary
frontend verification was a full manual walkthrough in a real browser against the live
backend/Postgres/Redis/Celery stack, covering: login/logout, session-expiry redirect on a
401, role-scoped dashboard numbers, task creation with an initial assignee (verified the
email landed in the Celery worker's console log), status-only editing as an Employee,
role-based nav/route visibility, and direct-URL IDOR/role-guard checks. That walkthrough
caught two real bugs (documented in `docs/PLAN.md`'s M6 entry) that no unit test would have
caught, since both were about the live interaction between routing, async session restore,
and a partial API response shape.

## What is intentionally not tested

- Celery retry/backoff *itself* (i.e. that a transient broker failure is retried N times
  with backoff) is configured (`autoretry_for`, `retry_backoff=True`) but not exercised by
  a test, since reliably simulating broker flakiness in a unit test adds more complexity
  than it proves — the idempotency guard that actually matters for correctness (no
  duplicate email on a real retry) is tested directly.
- Angular component-level unit tests beyond the app shell — the manual browser walkthrough
  was judged higher-value for the time available, per the assessment's own evaluation
  principle favoring "a secure and well-tested implementation" over coverage percentage.
