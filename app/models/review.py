from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    feedback: str
    decision: str
    reviewed_at: datetime

    submission_id: int = Field(
        foreign_key="submission.id",
        unique=True,
    )

    reviewer_id: int = Field(
        foreign_key="user.id"
    )