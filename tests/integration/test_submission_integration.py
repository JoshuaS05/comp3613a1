
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.user import User
from app.models.submission import Submission
from app.repositories.submission import SubmissionRepository
from app.services.submission_service import SubmissionService


def test_create_and_retrieve_submission(tmp_path):
    # Create an isolated test database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    # Create a test researcher
    with Session(engine) as session:
        researcher = User(
            username="testresearcher",
            email="researcher@example.com",
            password="testpassword",
            role="researcher",
        )

        session.add(researcher)
        session.commit()
        session.refresh(researcher)

        researcher_id = researcher.id
        assert researcher_id is not None

        # Create the service with a real repository
        repository = SubmissionRepository(session)

        service = SubmissionService(
            submission_repository=repository,
            uploads_directory=tmp_path / "uploads",
        )

        research_file = UploadFile(
            filename="research.pdf",
            file=BytesIO(b"Integration test research content"),
        )

        # Submit research
        submission = service.submit_research(
            title="Integration Test Research",
            abstract="Testing database integration",
            submission_type="Poster",
            research_file=research_file,
            researcher_id=researcher_id,
        )

        submission_id = submission.id
        assert submission_id is not None

    # Retrieve the submission using a new database session
    with Session(engine) as session:
        repository = SubmissionRepository(session)

        retrieved = repository.get_for_researcher(
            submission_id,
            researcher_id,
        )

        # Verify the saved data
        assert retrieved is not None
        assert retrieved.title == "Integration Test Research"
        assert retrieved.abstract == "Testing database integration"
        assert retrieved.submission_type == "Poster"
        assert retrieved.status == "Submitted"
        assert retrieved.researcher_id == researcher_id

        # Verify the research document was saved
        assert Path(retrieved.file_path).read_bytes() == (
            b"Integration test research content"
        )

        # Verify another researcher cannot retrieve it
        assert repository.get_for_researcher(
            submission_id,
            researcher_id + 999,
        ) is None

    engine.dispose()
