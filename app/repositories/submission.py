from sqlmodel import Session, select

from app.models.submission import Submission


class SubmissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, submission: Submission) -> Submission:
        try:
            self.db.add(submission)
            self.db.commit()
            self.db.refresh(submission)
            return submission
        except Exception:
            self.db.rollback()
            raise

    def list_for_researcher(self, researcher_id: int) -> list[Submission]:
        statement = (
            select(Submission)
            .where(Submission.researcher_id == researcher_id)
            .order_by(Submission.submitted_at.desc())
        )
        return list(self.db.exec(statement).all())

    def get_for_researcher(
        self,
        submission_id: int,
        researcher_id: int,
    ) -> Submission | None:
        statement = select(Submission).where(
            Submission.id == submission_id,
            Submission.researcher_id == researcher_id,
        )
        return self.db.exec(statement).one_or_none()

    def update(self, submission: Submission) -> Submission:
        try:
            self.db.add(submission)
            self.db.commit()
            self.db.refresh(submission)
            return submission
        except Exception:
            self.db.rollback()
            raise