from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    title: str
    abstract: str
    submission_type: str
    file_path: str
    status: str
    submitted_at: datetime

    researcher_id: int = Field(foreign_key="user.id")