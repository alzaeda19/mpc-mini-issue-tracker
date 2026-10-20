"""Shared request validation and API response shapes."""
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator


# SQLite INTEGER values are signed 64-bit numbers. Validate before binding SQL.
SQLITE_INT_MAX = 2**63 - 1


class Status(StrEnum):
    OPEN = 'Open'
    IN_PROGRESS = 'In Progress'
    RESOLVED = 'Resolved'
    CLOSED = 'Closed'


class Priority(StrEnum):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'


class IssueFields(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    status: Status
    priority: Priority
    assignee_id: int = Field(gt=0, le=SQLITE_INT_MAX, strict=True)


class IssueCreate(IssueFields):
    pass


class IssuePatch(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    status: Status | None = None
    priority: Priority | None = None
    assignee_id: int | None = Field(default=None, gt=0, le=SQLITE_INT_MAX, strict=True)

    @field_validator('*', mode='before')
    @classmethod
    def reject_explicit_null(cls, value):
        # Omitted fields retain their old value; explicit null is not a valid value.
        if value is None:
            raise ValueError('Fields cannot be null')
        return value


class Issue(IssueFields):
    id: int
    created_at: str
    updated_at: str


class User(BaseModel):
    id: int
    name: str
