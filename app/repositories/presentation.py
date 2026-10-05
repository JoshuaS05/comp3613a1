from sqlmodel import Session, select

from app.models.presentation import Presentation
from app.models.submission import Submission


class PresentationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_submission(
        self,
        submission_id: int,
    ) -> Presentation | None:
        statement = select(Presentation).where(
            Presentation.submission_id == submission_id
        )
        return self.db.exec(statement).one_or_none()

    def save(
        self,
        presentation: Presentation,
        submission: Submission,
    ) -> Presentation:
        try:
            self.db.add(presentation)
            self.db.add(submission)
            self.db.commit()
            self.db.refresh(presentation)
            return presentation
        except Exception:
            self.db.rollback()
            raise