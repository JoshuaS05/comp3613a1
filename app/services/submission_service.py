from datetime import datetime, timezone
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import UploadFile

from app.models.submission import Submission
from app.repositories.submission import SubmissionRepository


class SubmissionService:
    def __init__(
        self,
        submission_repository: SubmissionRepository,
        uploads_directory: Path = Path("uploads"),
    ):
        self.submission_repository = submission_repository
        self.uploads_directory = uploads_directory

    def list_researcher_submissions(self, researcher_id: int) -> list[Submission]:
        return self.submission_repository.list_for_researcher(researcher_id)

    def get_editable_submission(
        self,
        *,
        submission_id: int,
        researcher_id: int,
    ) -> Submission:
        submission = self.submission_repository.get_for_researcher(
            submission_id,
            researcher_id,
        )
        if submission is None or submission.status != "Revision Required":
            raise LookupError("Editable submission not found")
        return submission

    def resubmit_research(
        self,
        *,
        submission_id: int,
        title: str,
        abstract: str,
        submission_type: str,
        updated_file: UploadFile | None,
        researcher_id: int,
    ) -> Submission:
        submission = self.get_editable_submission(
            submission_id=submission_id,
            researcher_id=researcher_id,
        )
        replacement_path = None
        previous_path = Path(submission.file_path)

        if updated_file is not None and updated_file.filename:
            self.uploads_directory.mkdir(parents=True, exist_ok=True)
            extension = Path(updated_file.filename).suffix.lower()
            replacement_path = self.uploads_directory / f"{uuid4().hex}{extension}"
            try:
                with replacement_path.open("wb") as destination:
                    shutil.copyfileobj(updated_file.file, destination)
            except Exception:
                replacement_path.unlink(missing_ok=True)
                raise
            submission.file_path = str(replacement_path)

        submission.title = title
        submission.abstract = abstract
        submission.submission_type = submission_type
        submission.status = "Under Review"

        try:
            updated_submission = self.submission_repository.update(submission)
        except Exception:
            if replacement_path is not None:
                replacement_path.unlink(missing_ok=True)
            raise

        if replacement_path is not None:
            upload_root = self.uploads_directory.resolve()
            previous_file = previous_path.resolve()
            if upload_root in previous_file.parents and previous_file.is_file():
                previous_file.unlink(missing_ok=True)

        return updated_submission

    def submit_research(
        self,
        *,
        title: str,
        abstract: str,
        submission_type: str,
        research_file: UploadFile,
        researcher_id: int,
    ) -> Submission:
        self.uploads_directory.mkdir(parents=True, exist_ok=True)
        extension = Path(research_file.filename or "").suffix.lower()
        stored_path = self.uploads_directory / f"{uuid4().hex}{extension}"

        try:
            with stored_path.open("wb") as destination:
                shutil.copyfileobj(research_file.file, destination)

            submission = Submission(
                title=title,
                abstract=abstract,
                submission_type=submission_type,
                file_path=str(stored_path),
                status="Submitted",
                submitted_at=datetime.now(timezone.utc),
                researcher_id=researcher_id,
            )
            return self.submission_repository.create(submission)
        except Exception:
            stored_path.unlink(missing_ok=True)
            raise