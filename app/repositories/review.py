from sqlalchemy import and_, or_
from sqlmodel import Session, select

from app.models.review import Review
from app.models.submission import Submission


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_submission(self, submission_id: int) -> Submission | None:
        return self.db.get(Submission, submission_id)

    def get_for_submission(self, submission_id: int) -> Review | None:
        statement = select(Review).where(Review.submission_id == submission_id)
        return self.db.exec(statement).one_or_none()

    def list_review_queue(self, reviewer_id: int) -> list[Submission]:
        unreviewed = and_(
            Review.id.is_(None),
            Submission.status.in_(["Submitted", "Under Review"]),
        )
        returned_to_reviewer = and_(
            Review.id.is_not(None),
            Review.reviewer_id == reviewer_id,
            Submission.status.in_(
                ["Under Review", "Accepted", "Scheduled"]
            ),
        )
        statement = (
            select(Submission)
            .outerjoin(Review, Review.submission_id == Submission.id)
            .where(or_(unreviewed, returned_to_reviewer))
            .order_by(Submission.submitted_at.asc())
        )
        return list(self.db.exec(statement).all())

    def save(self, review: Review, submission: Submission) -> Review:
        try:
            self.db.add(review)
            self.db.add(submission)
            self.db.commit()
            self.db.refresh(review)
            return review
        except Exception:
            self.db.rollback()
            raise