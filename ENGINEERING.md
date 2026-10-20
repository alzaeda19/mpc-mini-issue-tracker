# Engineering decisions

## Why this stack?

FastAPI provides request validation, response schemas, HTTP routing and generated
API documentation with little framework code. Python's sqlite3 provides durable,
transactional relational storage without another service. A same-origin HTML/CSS/
JavaScript frontend avoids CORS, a Node toolchain and an extra server. React and
TypeScript would help a larger interface but add setup and abstractions to this
small exercise. The tradeoff is manually managed UI state and fewer static checks.

## Structure

`models.py` defines accepted input and output. `database.py` owns connections,
schema and seeded users. `repository.py` owns parameterized SQL and domain errors.
`main.py` translates HTTP into repository operations and safe responses. Frontend
`api.js` handles HTTP/errors, `views.js` builds safe DOM nodes, and `app.js` manages
interaction state. Separating these responsibilities keeps SQL out of routes and
rendering out of data access without adding a redundant service layer.

Each database operation uses a short-lived connection. Writes commit on success
and roll back on failure; foreign keys are enabled on every connection. Database
constraints reinforce API validation. The status/id index supports filtered lists.
Tests use the actual API and temporary SQLite files, so they check wiring and
persistence rather than just mocking repository return values.

## Most difficult part

The main design challenge in this implementation was partial updates: omitted
fields must retain their values, explicit nulls must be rejected, assignees must
exist, and invalid changes must leave the stored issue untouched. A dedicated
patch model and exclude_unset distinguish omitted fields from explicit nulls.
Pydantic rejects malformed input before SQL; the assignee lookup rejects missing
users before the write. SQLite constraints and rollback protect the write itself.
The preliminary reads occur before SQLite implicitly starts its write transaction,
so they are not isolated from other writers. Users are immutable through this API;
last-write-wins for issue edits is an explicit limitation. On the frontend, request
version counters discard stale list and detail results arriving out of order.

## Another two days

Add automated browser tests for create/edit/filter/delete and failure recovery
(the current Node tests use a DOM stand-in);
review accessibility and responsive layouts; add optimistic concurrency with a
version field and 409 conflicts; introduce schema migrations and dependency update
automation; improve retry/loading states and pagination totals.
Discuss authentication, authorization and team/user administration requirements
before implementing them. Add structured logs and operational health checks.

## At 100,000 users

User count alone does not determine load: measure active users, issue volume,
request rate, write contention and latency first. For a shared multi-user service,
introduce authentication, project-scoped authorization, rate limits, backups and
restore drills. Move SQLite to PostgreSQL for concurrent writes and shared storage
across app instances. Use migrations, a connection pool, indexed project/status
queries and cursor pagination. Replace substring scans with indexed full-text
search when profiling warrants it. Keep API instances stateless behind a load
balancer; monitor errors, latency and saturation. Add audit history and concurrency
control to avoid silently overwriting collaborators. Do not add caches or queues
until a measured workload requires them.
