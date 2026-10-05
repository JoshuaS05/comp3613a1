from app.models.presentation import Presentation
from app.repositories.presentation import PresentationRepository
from app.repositories.review import ReviewRepository


class PresentationService:
    def __init__(
        self,
        presentation_repository: PresentationRepository,
        review_repository: ReviewRepository,
    ):
        self.presentation_repository = presentation_repository
        self.review_repository = review_repository

    def get_presentation(self, submission_id: int):
        return self.presentation_repository.get_for_submission(submission_id)

    def schedule_presentation(
        self,
        *,
        submission_id: int,
        presentation_date,
        presentation_time,
        location: str,
        reviewer_id: int,
    ) -> Presentation:
        submission = self.review_repository.get_submission(submission_id)

        if submission is None:
            raise LookupError("Submission not found.")

        review = self.review_repository.get_for_submission(submission_id)

        if review is None:
            raise ValueError(
                "The submission must be reviewed before it can be scheduled."
            )

        if review.reviewer_id != reviewer_id:
            raise PermissionError(
                "Only the reviewer of record can schedule this presentation."
            )

        if submission.status not in {"Accepted", "Scheduled"}:
            raise ValueError(
                "Only accepted submissions can be scheduled."
            )

        if not location.strip():
            raise ValueError("Presentation location is required.")

        presentation = self.presentation_repository.get_for_submission(
            submission_id
        )

        if presentation is None:
            presentation = Presentation(
                date=presentation_date,
                time=presentation_time,
                location=location.strip(),
                submission_id=submission_id,
            )
        else:
            presentation.date = presentation_date
            presentation.time = presentation_time
            presentation.location = location.strip()

        submission.status = "Scheduled"

        return self.presentation_repository.save(
            presentation,
            submission,
        )