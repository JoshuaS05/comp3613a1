
from datetime import datetime, timezone

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.user import User
from app.models.submission import Submission
from app.models.review import Review
from app.repositories.review import ReviewRepository
from app.services.review_service import ReviewService


def test_review_updates_submission_status():
    # Create an isolated test database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create a researcher and reviewer
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

        # Create a submitted research item
        submission = Submission(
            title="AI in Education",
            abstract="Research on AI in learning",
            submission_type="Poster",
            file_path="test_research.pdf",
            status="Submitted",
            submitted_at=datetime.now(timezone.utc),
            researcher_id=researcher.id,
        )

        session.add(submission)
        session.commit()
        session.refresh(submission)

        submission_id = submission.id
        reviewer_id = reviewer.id

        # Create the real repository and service
        repository = ReviewRepository(session)
        service = ReviewService(repository)

        # Reviewer accepts the submission
        review = service.save_review(
            submission_id=submission_id,
            feedback="Excellent research",
            decision="Accepted",
            reviewer_id=reviewer_id,
        )

        assert review.decision == "Accepted"
        assert review.feedback == "Excellent research"

    # Open a new session to verify database changes
    with Session(engine) as session:
        repository = ReviewRepository(session)

        saved_submission = repository.get_submission(
            submission_id
        )

        saved_review = repository.get_for_submission(
            submission_id
        )

        assert saved_submission is not None
        assert saved_review is not None

        # Check that the review was saved
        assert saved_review.decision == "Accepted"
        assert saved_review.feedback == "Excellent research"
        assert saved_review.reviewer_id == reviewer_id

        # Check that submission status was updated
        assert saved_submission.status == "Accepted"

    engine.dispose()
