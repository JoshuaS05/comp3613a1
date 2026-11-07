
from unittest.mock import Mock

from app.services.tracking_service import TrackingService

import pytest

def test_tracking_scheduled_submission():
    submission_repository = Mock()
    review_repository = Mock()
    presentation_repository = Mock()

    submission = Mock()
    submission.id = 1
    submission.status = "Scheduled"
    submission.researcher_id = 1

    submission_repository.get_for_researcher.return_value = submission

    review = Mock()
    presentation = Mock()

    review_repository.get_for_submission.return_value = review
    presentation_repository.get_for_submission.return_value = presentation

    service = TrackingService(
        submission_repository=submission_repository,
        review_repository=review_repository,
        presentation_repository=presentation_repository,
    )

    result_submission, result_review, result_presentation, timeline = (
        service.get_submission_details(
            submission_id=1,
            researcher_id=1,
        )
    )

    assert result_submission == submission
    assert result_review == review
    assert result_presentation == presentation

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

    submission_repository.get_for_researcher.assert_called_once_with(1, 1)


def test_cannot_track_another_researchers_submission():
    submission_repository = Mock()
    review_repository = Mock()
    presentation_repository = Mock()

    # Ownership-filtered lookup returns no submission.
    submission_repository.get_for_researcher.return_value = None

    service = TrackingService(
        submission_repository=submission_repository,
        review_repository=review_repository,
        presentation_repository=presentation_repository,
    )

    with pytest.raises(
        LookupError,
        match="Submission not found"
    ):
        service.get_submission_details(
            submission_id=1,
            researcher_id=2,
        )

    submission_repository.get_for_researcher.assert_called_once_with(1, 2)
    review_repository.get_for_submission.assert_not_called()
    presentation_repository.get_for_submission.assert_not_called()
