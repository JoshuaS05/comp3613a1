
from unittest.mock import Mock

import pytest

from app.services.review_service import ReviewService


def test_invalid_review_decision():
    repository = Mock()

    service = ReviewService(
        review_repository=repository
    )

    with pytest.raises(
        ValueError,
        match="Invalid review decision"
    ):
        service.save_review(
            submission_id=1,
            feedback="Test feedback",
            decision="Pending",
            reviewer_id=2
        )

    repository.save.assert_not_called()


def test_valid_review_decision():
    repository = Mock()

    submission = Mock()
    submission.id = 1
    submission.status = "Submitted"

    repository.get_submission.return_value = submission
    repository.get_for_submission.return_value = None

    service = ReviewService(
        review_repository=repository
    )

    service.save_review(
        submission_id=1,
        feedback="Research approved",
        decision="Accepted",
        reviewer_id=2
    )

    repository.save.assert_called_once()

    saved_review, updated_submission = repository.save.call_args.args

    assert saved_review.decision == "Accepted"
    assert saved_review.feedback == "Research approved"
    assert saved_review.reviewer_id == 2
    assert updated_submission.status == "Accepted"
