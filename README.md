# Mini Issue Tracker

A small local web application for creating, viewing, updating, assigning, searching,
filtering and deleting software issues. Python/FastAPI serves a modular vanilla
JavaScript frontend and REST API. SQLite persists data across restarts.

## Setup and run (macOS)

Requires Python 3.12+ and a modern browser. No Node, database service, or API keys are needed to run the app.
Node 20+ is optional for the frontend controller tests.
From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Interactive API documentation is at
http://127.0.0.1:8000/docs. Stop with Control-C. SQLite tables and three demo users
are initialized automatically on startup. Issues start empty.

## Environment

`DATABASE_PATH` optionally specifies a writable SQLite file; default `issues.db`
relative to the working directory. Its parent directory must already exist.
No `.env` loader is used; export variables in the shell:

```sh
export DATABASE_PATH=/tmp/mini-issues.db
```

Run from the repository root. The database and virtual environment are ignored by
Git. Back up the database before deleting it; removing it resets stored issues.
Bind to localhost: there is no authentication and this is not a public deployment.

The lock file pins the complete tested dependency set; `requirements.txt` lists
direct dependencies. Commands also work on Linux.

## Tests

```sh
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Tests use temporary SQLite files, not your application database. They cover CRUD,
created/updated dates, invalid requests and assignees, missing issues, search plus
status filtering, pagination, restart persistence, frontend delivery and safe
storage/unexpected errors. Deliberate failure tests assert that internal details
are not returned to clients. They may produce expected server error logs.

Optional frontend regression checks (Node 20+, no npm install):

```sh
node --test tests/frontend.test.cjs
```

These use a small DOM stand-in to test pending saves, draft retention, focus, stale
errors and API error messages. They are not a browser automation suite.

Manual browser check: create an issue, open details, edit its status/assignee,
search its description, combine a status filter, reload, and delete a disposable
issue. Also check keyboard navigation and a narrow browser window.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/users` | Seeded assignee choices |
| GET | `/api/issues` | Newest first; `status`, `search`, `limit` (1–100), `offset` |
| GET | `/api/issues/{id}` | Single issue; 404 if absent |
| POST | `/api/issues` | All five editable fields required; 201 with Location |
| PATCH | `/api/issues/{id}` | One or more editable fields; 200 |
| DELETE | `/api/issues/{id}` | 204; 404 if absent |

Example create body:

```json
{"title":"Fix login","description":"Login fails on mobile","status":"Open","priority":"High","assignee_id":1}
```

Server-generated `id`, `created_at`, and `updated_at` cannot be supplied. Invalid
input returns 422; unavailable storage returns 503; unexpected errors return a
safe 500 response. Server logs retain diagnostic details.

## Assumptions and limitations

- Seeded users: Alzayed Alhassan, Alex Morgan, Sam Taylor. Every issue must have an
  existing assignee; no user administration or unassigned state.
- Statuses: Open, In Progress, Resolved, Closed. All transitions allowed.
- Priorities: Low, Medium, High, Critical.
- Title and description are required, whitespace-trimmed, capped at 200 and 10,000
  characters. NUL and invisible-only text, explicit nulls, and unknown fields are
  rejected. IDs/offsets fit SQLite signed 64-bit integers.
- Search is literal substring matching across title and description. SQLite lower()
  case folding primarily covers ASCII; full multilingual search is future work.
- Pydantic accepts numeric path forms such as `1.0` as ID 1; body assignee IDs
  require strict integers. An empty `status=` is invalid; omit it for all statuses.
- Dates are UTC ISO strings; the browser displays local time. Update changes
  updated_at, including a request that sets an existing value again.
- Lists use offset pagination, 20 rows per UI page. A full last page may expose an
  empty next page. Concurrent inserts can shift offset pages.
- No authentication, authorization, optimistic concurrency, audit history,
  migrations, deployment, or automated browser regression suite. Last write wins.
- SQLite is appropriate for this local exercise; concurrent writes serialize.
- A failed users load requires a page reload to retry initial setup.
- There is no Host allowlist or request-body byte cap; localhost binding is the
  intended use, not an internet-facing service. `/docs` loads Swagger UI from a CDN.

## AI assistance

AI assistance was used for implementation, tests, documentation, and five separate
Claude Fable 5.1 review chats. This is disclosed because the brief permits AI and
holds the candidate responsible for explaining all submitted code. See
[WALKTHROUGH.md](WALKTHROUGH.md) for the code paths and review exercises, and
[ENGINEERING.md](ENGINEERING.md) for design decisions and limitations.
