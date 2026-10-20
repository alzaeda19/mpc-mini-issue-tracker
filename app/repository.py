"""Parameterized SQL and issue operations, independent of HTTP."""
from datetime import datetime, timezone
from .database import connect


class NotFound(Exception):
    pass


class InvalidAssignee(Exception):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def get_issue(db, issue_id):
    row = db.execute('SELECT * FROM issues WHERE id = ?', (issue_id,)).fetchone()
    if row is None:
        raise NotFound()
    return dict(row)


def check_assignee(db, values):
    if 'assignee_id' in values:
        if db.execute('SELECT id FROM users WHERE id = ?', (values['assignee_id'],)).fetchone() is None:
            raise InvalidAssignee()


class Repository:
    def __init__(self, path):
        self.path = path

    def users(self):
        with connect(self.path) as db:
            return [dict(row) for row in db.execute('SELECT * FROM users ORDER BY id')]

    def list(self, status, search, limit, offset):
        clauses, parameters = [], []
        if status:
            clauses.append('status = ?')
            parameters.append(status)
        if search:
            # instr treats %, _ and quotes literally instead of as SQL wildcards.
            clauses.append('(instr(lower(title), lower(?)) > 0 OR instr(lower(description), lower(?)) > 0)')
            parameters.extend([search, search])
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        with connect(self.path) as db:
            rows = db.execute('SELECT * FROM issues' + where + ' ORDER BY id DESC LIMIT ? OFFSET ?',
                              [*parameters, limit, offset])
            return [dict(row) for row in rows]

    def get(self, issue_id):
        with connect(self.path) as db:
            return get_issue(db, issue_id)

    def create(self, values):
        with connect(self.path) as db:
            check_assignee(db, values)
            now = timestamp()
            cursor = db.execute('''INSERT INTO issues
                (title, description, status, priority, assignee_id, created_at, updated_at)
                VALUES (:title, :description, :status, :priority, :assignee_id, :created_at, :updated_at)''',
                {**values, 'created_at': now, 'updated_at': now})
            return get_issue(db, cursor.lastrowid)

    def update(self, issue_id, values):
        with connect(self.path) as db:
            get_issue(db, issue_id)
            check_assignee(db, values)
            # Keys come only from validated model fields, never raw request keys.
            values = {**values, 'updated_at': timestamp()}
            assignments = ', '.join(f'{key} = ?' for key in values)
            db.execute(f'UPDATE issues SET {assignments} WHERE id = ?', [*values.values(), issue_id])
            return get_issue(db, issue_id)

    def delete(self, issue_id):
        with connect(self.path) as db:
            cursor = db.execute('DELETE FROM issues WHERE id = ?', (issue_id,))
            if cursor.rowcount == 0:
                raise NotFound()
