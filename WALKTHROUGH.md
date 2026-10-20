# Candidate review walkthrough

This is AI-assisted code. Read each file and run the application before submitting.
The following explains the path through the code; it does not establish that you
already understand or personally authored it.

1. Start at `app/main.py`. `create_app` accepts a database path so tests can create
   isolated applications. Lifespan initializes schema before requests. Route
   functions use synchronous def because sqlite3 blocks; FastAPI runs them in a
   worker thread. There are no async database calls to await.
2. Read `models.py`. Enums restrict status and priority. Field constraints reject
   blank/oversized strings and invalid IDs. Extra fields are forbidden so a client
   cannot set server-owned dates. Explain omitted versus explicit null in PATCH:
   the validator rejects provided nulls; exclude_unset omits absent keys.
3. Read `database.py`. The context manager always closes connections. `with
   connection` commits success or rolls back exceptions. Foreign keys must be
   enabled per connection. Initialization uses IF NOT EXISTS and INSERT OR IGNORE
   so restarts preserve existing data.
4. Read `repository.py`. Values use placeholders, preventing SQL injection. Update
   column names come only from validated model fields. Assignee IDs reference a
   users table. Create assigns both dates; update changes only updated_at. Domain
   exceptions are translated at the HTTP layer. Search uses instr for literal
   substring matching; a percent sign does not mean a wildcard.
5. Follow New issue in `static/app.js`: open/reset the form, collect its fields,
   convert the select's string user ID to a number, call request, reload list and
   fetch details. `api.js` converts HTTP failures to readable errors; network
   failures are caught by callers. `views.js` assigns user strings with textContent
   to avoid executing injected HTML. No framework silently manages state.
6. Explain request counters: older responses must not replace newer search/detail
   selections. A database transaction does not solve browser response ordering.
7. Read each test, especially why failed patches leave the original record intact
   and why persistence is tested with a fresh app on the same SQLite file.

Review exercises:

- Use /docs to create a record with an invalid assignee, then explain the 422.
- PATCH only priority and show that title and created_at stay unchanged.
- Stop and restart the server and find your issue again.
- Explain why SQLite is fine locally but write concurrency matters at scale.
- Explain the limitations of last-write-wins, offset pagination and ASCII search.
- Choose one small change yourself, predict the affected files, implement it, and
  add a meaningful test. Keep its commit separate from the AI-generated baseline.

Before submission, make sure you can explain every function and dependency, revise
ENGINEERING.md into your own accurate account, and confirm current submission
instructions. Creating/pushing a GitHub repository and submitting require separate
authorization and have not been performed.
