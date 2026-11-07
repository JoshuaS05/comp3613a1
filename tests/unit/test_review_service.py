
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
