
from datetime import date, datetime, time, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.user import User
from app.models.submission import Submission
from app.models.review import Review
from app.models.presentation import Presentation

from app.repositories.submission import SubmissionRepository
from app.repositories.review import ReviewRepository
from app.repositories.presentation import PresentationRepository

from app.services.tracking_service import TrackingService


def test_tracking_returns_review_and_presentation():
    # Create a separate test database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create researcher and reviewer
        researcher = User(
            username="researcher",
            email="researcher@example.com",
            password="testpassword",
            role="researcher",
        )

        reviewer = User(
            username="reviewer",
            email="reviewer@example.com",
            password="testpassword",
            role="reviewer",
        )

        session.add_all([researcher, reviewer])
        session.commit()
        session.refresh(researcher)
        session.refresh(reviewer)

        assert researcher.id is not None
        assert reviewer.id is not None

        researcher_id = researcher.id
        reviewer_id = reviewer.id

        # Create a scheduled submission
        submission = Submission(
            title="AI in Education",
            abstract="Research on AI in learning",
            submission_type="Presentation",
            file_path="test_research.pdf",
            status="Scheduled",
            submitted_at=datetime.now(timezone.utc),
            researcher_id=researcher_id,
        )

        session.add(submission)
        session.commit()
        session.refresh(submission)

        assert submission.id is not None
        submission_id = submission.id

        # Create an accepted review
        review = Review(
            feedback="Excellent research",
            decision="Accepted",
            reviewed_at=datetime.now(timezone.utc),
            submission_id=submission_id,
            reviewer_id=reviewer_id,
        )

        # Create presentation information
        presentation = Presentation(
            date=date(2026, 12, 10),
            time=time(10, 30),
            location="Lecture Hall A",
            submission_id=submission_id,
        )

        session.add_all([review, presentation])
        session.commit()

    # Retrieve records using real repositories
    # and a new database session
    with Session(engine) as session:
        service = TrackingService(
            submission_repository=SubmissionRepository(session),
            review_repository=ReviewRepository(session),
            presentation_repository=PresentationRepository(session),
        )

        result_submission, result_review, result_presentation, timeline = (
            service.get_submission_details(
                submission_id=submission_id,
                researcher_id=researcher_id,
            )
        )

        # Check submission information
        assert result_submission.title == "AI in Education"
        assert result_submission.status == "Scheduled"
        assert result_submission.researcher_id == researcher_id

        # Check review information
        assert result_review is not None
        assert result_review.decision == "Accepted"
        assert result_review.feedback == "Excellent research"

        # Check presentation information
        assert result_presentation is not None
        assert result_presentation.date == date(2026, 12, 10)
        assert result_presentation.time == time(10, 30)
        assert result_presentation.location == "Lecture Hall A"

        # Check the complete timeline
        assert [step["label"] for step in timeline] == [
            "Submitted",
            "Under Review",
            "Accepted",
            "Scheduled",
        ]

        assert [step["state"] for step in timeline] == [
            "complete",
            "complete",
            "complete",
            "current",
        ]

        # Check that another researcher cannot access it
        with pytest.raises(LookupError):
            service.get_submission_details(
                submission_id=submission_id,
                researcher_id=researcher_id + 999,
            )

    engine.dispose()
