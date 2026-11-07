
from fastapi import HTTPException, status
from pydantic import BaseModel
from datetime import date, time

from app.repositories.presentation import PresentationRepository
from app.services.presentation_service import PresentationService
from app.dependencies.auth import ReviewerAdminDep
from app.dependencies.session import SessionDep
from app.repositories.review import ReviewRepository
from app.services.review_service import ReviewService
from app.schemas.submission import SubmissionResponse

from . import api_router


class ReviewDecisionRequest(BaseModel):
    feedback: str
    decision: str


@api_router.get(
    "/reviews/queue",
    response_model=list[SubmissionResponse],
)
async def get_review_queue(
    user: ReviewerAdminDep,
    db: SessionDep,
):
    repository = ReviewRepository(db)
    service = ReviewService(repository)

    return service.list_review_queue(user.id)


@api_router.post("/reviews/{submission_id}/decision")
async def submit_review_decision(
    submission_id: int,
    review_data: ReviewDecisionRequest,
    user: ReviewerAdminDep,
    db: SessionDep,
):
    repository = ReviewRepository(db)
    service = ReviewService(repository)

    try:
        review = service.save_review(
            submission_id=submission_id,
            feedback=review_data.feedback,
            decision=review_data.decision,
            reviewer_id=user.id,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return {
        "id": review.id,
        "submission_id": review.submission_id,
        "decision": review.decision,
        "feedback": review.feedback,
    }


class PresentationScheduleRequest(BaseModel):
    presentation_date: date
    presentation_time: time
    location: str


@api_router.post("/reviews/{submission_id}/schedule")
async def schedule_submission_presentation(
    submission_id: int,
    schedule_data: PresentationScheduleRequest,
    user: ReviewerAdminDep,
    db: SessionDep,
):
    review_repository = ReviewRepository(db)
    presentation_repository = PresentationRepository(db)

    service = PresentationService(
        presentation_repository,
        review_repository,
    )

    try:
        presentation = service.schedule_presentation(
            submission_id=submission_id,
            presentation_date=schedule_data.presentation_date,
            presentation_time=schedule_data.presentation_time,
            location=schedule_data.location,
            reviewer_id=user.id,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return {
        "id": presentation.id,
        "submission_id": presentation.submission_id,
        "date": presentation.date,
        "time": presentation.time,
        "location": presentation.location,
    }
