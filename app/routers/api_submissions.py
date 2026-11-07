
from fastapi import File, Form, UploadFile, status
from fastapi import HTTPException

from app.repositories.review import ReviewRepository
from app.repositories.presentation import PresentationRepository
from app.services.tracking_service import TrackingService
from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.submission import SubmissionRepository
from app.services.submission_service import SubmissionService
from app.schemas.submission import SubmissionResponse

from . import api_router


@api_router.get(
    "/submissions",
    response_model=list[SubmissionResponse],
)
async def list_my_submissions(
    user: AuthDep,
    db: SessionDep,
):
    repository = SubmissionRepository(db)
    service = SubmissionService(repository)

    return service.list_researcher_submissions(user.id)


@api_router.post(
    "/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_submission(
    user: AuthDep,
    db: SessionDep,
    title: str = Form(),
    abstract: str = Form(),
    submission_type: str = Form(),
    research_file: UploadFile = File(),
):
    repository = SubmissionRepository(db)
    service = SubmissionService(repository)

    return service.submit_research(
        title=title,
        abstract=abstract,
        submission_type=submission_type,
        research_file=research_file,
        researcher_id=user.id,
    )


@api_router.get("/submissions/{submission_id}/tracking")
async def track_submission(
    submission_id: int,
    user: AuthDep,
    db: SessionDep,
):
    service = TrackingService(
        submission_repository=SubmissionRepository(db),
        review_repository=ReviewRepository(db),
        presentation_repository=PresentationRepository(db),
    )

    try:
        submission, review, presentation, timeline = (
            service.get_submission_details(
                submission_id=submission_id,
                researcher_id=user.id,
            )
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except PermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        ) from error

    return {
        "submission": {
            "id": submission.id,
            "title": submission.title,
            "status": submission.status,
        },
        "review": None if review is None else {
            "decision": review.decision,
            "feedback": review.feedback,
        },
        "presentation": None if presentation is None else {
            "date": presentation.date,
            "time": presentation.time,
            "location": presentation.location,
        },
        "timeline": timeline,
    }
