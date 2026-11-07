
from datetime import date, datetime, time, timezone

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.user import User
from app.models.submission import Submission
from app.models.review import Review
from app.models.presentation import Presentation

from app.repositories.review import ReviewRepository
from app.repositories.presentation import PresentationRepository
from app.services.presentation_service import PresentationService


def test_schedule_presentation_updates_submission():
    # Create an isolated test database
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

        reviewer_id = reviewer.id

        # Create an accepted research submission
        submission = Submission(
            title="AI in Education",
            abstract="Research on AI in learning",
            submission_type="Presentation",
            file_path="test_research.pdf",
            status="Accepted",
            submitted_at=datetime.now(timezone.utc),
            researcher_id=researcher.id,
        )

        session.add(submission)
        session.commit()
        session.refresh(submission)

        assert submission.id is not None
        submission_id = submission.id

        # Create an existing accepted review
        review = Review(
            feedback="Excellent research",
            decision="Accepted",
            reviewed_at=datetime.now(timezone.utc),
            submission_id=submission_id,
            reviewer_id=reviewer_id,
        )

        session.add(review)
        session.commit()

        # Use real repositories and service
        presentation_repository = PresentationRepository(session)
        review_repository = ReviewRepository(session)

        service = PresentationService(
            presentation_repository=presentation_repository,
            review_repository=review_repository,
        )

        # Schedule the presentation
        presentation = service.schedule_presentation(
            submission_id=submission_id,
            presentation_date=date(2026, 12, 10),
            presentation_time=time(10, 30),
            location="Lecture Hall A",
            reviewer_id=reviewer_id,
        )

        assert presentation.id is not None
        assert presentation.location == "Lecture Hall A"

    # Verify the saved records in a new session
    with Session(engine) as session:
        presentation_repository = PresentationRepository(session)

        saved_presentation = (
            presentation_repository.get_for_submission(
                submission_id
            )
        )

        saved_submission = session.get(
            Submission,
            submission_id,
        )

        assert saved_presentation is not None
        assert saved_submission is not None

        # Check presentation details
        assert saved_presentation.date == date(2026, 12, 10)
        assert saved_presentation.time == time(10, 30)
        assert saved_presentation.location == "Lecture Hall A"
        assert saved_presentation.submission_id == submission_id

        # Check that submission status was updated
        assert saved_submission.status == "Scheduled"

    engine.dispose()
