
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SubmissionResponse(BaseModel):
    id: int
    title: str
    abstract: str
    submission_type: str
    status: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
