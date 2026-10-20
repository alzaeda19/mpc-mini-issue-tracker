"""HTTP boundary: validation, response codes, safe errors, and static frontend."""
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, HTTPException, Path as ApiPath, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from .database import initialize
from .models import Issue, IssueCreate, IssuePatch, Status, User
from .repository import InvalidAssignee, NotFound, Repository

logger = logging.getLogger(__name__)
IssueId = Annotated[int, ApiPath(gt=0)]
STATIC = Path(__file__).parent / 'static'


def create_app(database_path=None):
    path = database_path or os.environ.get('DATABASE_PATH', 'issues.db')
    repository = Repository(path)

    @asynccontextmanager
    async def lifespan(app):
        initialize(path)
        yield

    app = FastAPI(title='Mini Issue Tracker', lifespan=lifespan)

    @app.exception_handler(NotFound)
    async def not_found(request, exc):
        return JSONResponse(status_code=404, content={'detail': 'Issue not found'})

    @app.exception_handler(InvalidAssignee)
    async def invalid_assignee(request, exc):
        return JSONResponse(status_code=422, content={'detail': 'Choose an existing assignee'})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error('Request failed: %s %s', request.method, request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content={'detail': 'Something went wrong. Please try again.'})

    @app.exception_handler(sqlite3.Error)
    async def database_error(request, exc):
        logger.error('Database operation failed', exc_info=exc)
        return JSONResponse(status_code=503, content={'detail': 'Storage is temporarily unavailable. Please try again.'})

    @app.get('/api/users', response_model=list[User])
    def users():
        return repository.users()

    @app.get('/api/issues', response_model=list[Issue])
    def list_issues(status: Status | None = None,
                    search: Annotated[str, Query(max_length=200)] = '',
                    limit: Annotated[int, Query(ge=1, le=100)] = 20,
                    offset: Annotated[int, Query(ge=0)] = 0):
        return repository.list(status, search.strip(), limit, offset)

    @app.get('/api/issues/{issue_id}', response_model=Issue)
    def get_issue(issue_id: IssueId):
        return repository.get(issue_id)

    @app.post('/api/issues', response_model=Issue, status_code=201)
    def create_issue(payload: IssueCreate, response: Response):
        issue = repository.create(payload.model_dump())
        response.headers['Location'] = f'/api/issues/{issue["id"]}'
        return issue

    @app.patch('/api/issues/{issue_id}', response_model=Issue)
    def update_issue(issue_id: IssueId, payload: IssuePatch):
        values = payload.model_dump(exclude_unset=True)
        if not values:
            raise HTTPException(status_code=422, detail='Provide at least one field to update')
        return repository.update(issue_id, values)

    @app.delete('/api/issues/{issue_id}', status_code=204)
    def delete_issue(issue_id: IssueId):
        repository.delete(issue_id)
        return Response(status_code=204)

    @app.get('/', include_in_schema=False)
    def index():
        return FileResponse(STATIC / 'index.html')

    app.mount('/static', StaticFiles(directory=STATIC), name='static')
    return app


app = create_app()
