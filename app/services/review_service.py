from datetime import datetime, timezone
from pathlib import Path

from app.models.review import Review
from app.models.submission import Submission
from app.repositories.review import ReviewRepository

REVIEW_DECISIONS = {"Revision Required", "Accepted", "Rejected"}


class ReviewService:
    def __init__(self, review_repository: ReviewRepository):
        self.review_repository = review_repository

    def save_review(
        self,
        *,
        submission_id: int,
        feedback: str,
        decision: str,
        reviewer_id: int,
    ) -> Review:
        if decision not in REVIEW_DECISIONS:
            raise ValueError("Invalid review decision")

        submission, review = self.get_submission_for_review(
            submission_id=submission_id,
            reviewer_id=reviewer_id,
        )
        if submission.status not in {"Submitted", "Under Review"}:
            raise ValueError("Review decisions can only be changed during review")
        if review is None:
            review = Review(
                submission_id=submission_id,
                reviewer_id=reviewer_id,
                feedback=feedback,
                decision=decision,
                reviewed_at=datetime.now(timezone.utc),
            )
        else:
            review.feedback = feedback
            review.decision = decision
            review.reviewed_at = datetime.now(timezone.utc)

        submission.status = decision
        return self.review_repository.save(review, submission)

    def list_review_queue(self, reviewer_id: int) -> list[Submission]:
        return self.review_repository.list_review_queue(reviewer_id)

    def get_submission_for_review(
        self,
        *,
        submission_id: int,
        reviewer_id: int,
    ) -> tuple[Submission, Review | None]:
        submission = self.review_repository.get_submission(submission_id)
        if submission is None:
            raise LookupError("Submission not found")

        review = self.review_repository.get_for_submission(submission_id)
        if review is not None:
            if review.reviewer_id != reviewer_id:
                raise PermissionError("This submission belongs to another reviewer")
            if submission.status not in {"Under Review", "Accepted", "Scheduled"}:
                raise LookupError("Submission is not available for this reviewer")
        elif submission.status not in {"Submitted", "Under Review"}:
            raise LookupError("Submission is not awaiting review")

        return submission, review

    def get_research_file_path(
        self,
        *,
        submission_id: int,
        reviewer_id: int,
    ) -> Path:
        submission, _ = self.get_submission_for_review(
            submission_id=submission_id,
            reviewer_id=reviewer_id,
        )
        upload_root = Path("uploads").resolve()
        file_path = Path(submission.file_path).resolve()
        if upload_root not in file_path.parents or not file_path.is_file():
            raise LookupError("Research file not found")
        return file_path