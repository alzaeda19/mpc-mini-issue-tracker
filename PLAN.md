# Implementation plan

Brief read in full on October 20, 2026:
[private exercise brief]

1. Persistent SQLite schema; validated issue models; REST CRUD and search/status filters.
2. Same-origin simple frontend: list, detail, create, edit, assign, change status, delete.
3. Integration tests: CRUD, invalid input, combined filters, persistence, safe failures.
4. README setup/environment/assumptions/limitations and ENGINEERING.md decisions.
5. Local verification and explanation walkthrough; candidate review before any submission.

Scope: FastAPI + Python standard-library SQLite + HTML/CSS/JavaScript. No separate frontend build. Three seeded demo users; no authentication or user administration. Search title/description case-insensitively. Dates are UTC. All status transitions allowed. Git commits stay local until expressly authorized otherwise.

AI assistance is allowed by the brief. This implementation is AI-assisted and requires Alzayed's review and understanding before submission.
