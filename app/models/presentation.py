from datetime import date, time
from typing import Optional

from sqlmodel import Field, SQLModel


class Presentation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    date: date
    time: time
    location: str

    submission_id: int = Field(
        foreign_key="submission.id",
        unique=True,
    )