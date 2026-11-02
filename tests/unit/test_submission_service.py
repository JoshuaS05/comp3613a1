from io import BytesIO
from unittest.mock import Mock

from fastapi import UploadFile

from app.services.submission_service import SubmissionService


def test_submit_research(tmp_path):
    repository = Mock()

    def return_submission(submission):
        return submission

    repository.create.side_effect = return_submission

    service = SubmissionService(
        submission_repository=repository,
        uploads_directory=tmp_path,
    )

    research_file = UploadFile(
        filename="research.pdf",
        file=BytesIO(b"test research content"),
    )

    submission = service.submit_research(
        title="Test Research",
        abstract="Test abstract",
        submission_type="Poster",
        research_file=research_file,
        researcher_id=1,
    )

    assert submission.title == "Test Research"
    assert submission.abstract == "Test abstract"
    assert submission.submission_type == "Poster"
    assert submission.status == "Submitted"
    assert submission.researcher_id == 1

    repository.create.assert_called_once()