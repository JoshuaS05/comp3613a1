from app.models.presentation import Presentation
from app.models.review import Review
from app.models.submission import Submission
from app.repositories.presentation import PresentationRepository
from app.repositories.review import ReviewRepository
from app.repositories.submission import SubmissionRepository

STATUS_PATHS = {
    "Submitted": ["Submitted"],
    "Under Review": ["Submitted", "Under Review"],
    "Revision Required": ["Submitted", "Under Review", "Revision Required"],
    "Accepted": ["Submitted", "Under Review", "Accepted"],
    "Rejected": ["Submitted", "Under Review", "Rejected"],
    "Scheduled": ["Submitted", "Under Review", "Accepted", "Scheduled"],
}


class TrackingService:
    def __init__(
        self,
        submission_repository: SubmissionRepository,
        review_repository: ReviewRepository,
        presentation_repository: PresentationRepository,
    ):
        self.submission_repository = submission_repository
        self.review_repository = review_repository
        self.presentation_repository = presentation_repository

    def get_submission_details(
        self,
        *,
        submission_id: int,
        researcher_id: int,
    ) -> tuple[Submission, Review | None, Presentation | None, list[dict[str, str]]]:
        submission = self.submission_repository.get_for_researcher(
            submission_id,
            researcher_id,
        )
        if submission is None:
            raise LookupError("Submission not found")

        status_path = STATUS_PATHS.get(submission.status, [submission.status])
        timeline = [
            {
                "label": label,
                "state": "current" if index == len(status_path) - 1 else "complete",
            }
            for index, label in enumerate(status_path)
        ]
        return (
            submission,
            self.review_repository.get_for_submission(submission_id),
            self.presentation_repository.get_for_submission(submission_id),
            timeline,
        )