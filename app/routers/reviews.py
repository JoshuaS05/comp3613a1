from datetime import date, time

from fastapi import Form, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse

from app.dependencies.auth import ReviewerAdminDep
from app.dependencies.session import SessionDep
from app.repositories.review import ReviewRepository
from app.repositories.presentation import PresentationRepository
from app.services.review_service import ReviewService
from app.services.presentation_service import PresentationService
from app.utilities.flash import flash
from . import router, templates


@router.get("/review/submissions", name="review_queue_view")
async def review_queue_view(
    request: Request,
    user: ReviewerAdminDep,
    db: SessionDep,
):
    service = ReviewService(ReviewRepository(db))

    return templates.TemplateResponse(
        request=request,
        name="review-queue.html",
        context={
            "user": user,
            "submissions": service.list_review_queue(user.id),
        },
    )


@router.get(
    "/review/submissions/{submission_id}",
    name="review_submission_view",
)
async def review_submission_view(
    request: Request,
    user: ReviewerAdminDep,
    db: SessionDep,
    submission_id: int,
):
    review_repository = ReviewRepository(db)
    presentation_repository = PresentationRepository(db)
    service = ReviewService(review_repository)
    presentation_service = PresentationService(
        presentation_repository,
        review_repository,
    )

    try:
        submission, review = service.get_submission_for_review(
            submission_id=submission_id,
            reviewer_id=user.id,
        )
        presentation = presentation_service.get_presentation(submission_id)
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

    return templates.TemplateResponse(
        request=request,
        name="review-submission.html",
        context={
            "user": user,
            "submission": submission,
            "review": review,
            "presentation": presentation,
        },
    )


@router.get(
    "/review/submissions/{submission_id}/file",
    name="review_submission_file",
)
async def review_submission_file(
    user: ReviewerAdminDep,
    db: SessionDep,
    submission_id: int,
):
    service = ReviewService(ReviewRepository(db))
    try:
        file_path = service.get_research_file_path(
            submission_id=submission_id,
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

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        content_disposition_type="inline",
    )


@router.post(
    "/review/submissions/{submission_id}/decision",
    name="save_review",
)
async def save_review(
    request: Request,
    user: ReviewerAdminDep,
    db: SessionDep,
    submission_id: int,
    feedback: str = Form(),
    decision: str = Form(),
):
    repository = ReviewRepository(db)
    service = ReviewService(repository)

    try:
        service.save_review(
            submission_id=submission_id,
            feedback=feedback,
            decision=decision,
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

    flash(request, "Review saved.")

    return RedirectResponse(
        url=request.url_for("review_queue_view"),
        status_code=303,
    )


@router.post(
    "/review/submissions/{submission_id}/schedule",
    name="schedule_presentation",
)
async def schedule_presentation(
    request: Request,
    user: ReviewerAdminDep,
    db: SessionDep,
    submission_id: int,
    presentation_date: date = Form(),
    presentation_time: time = Form(),
    location: str = Form(),
):
    review_repository = ReviewRepository(db)
    presentation_repository = PresentationRepository(db)

    service = PresentationService(
        presentation_repository,
        review_repository,
    )

    try:
        service.schedule_presentation(
            submission_id=submission_id,
            presentation_date=presentation_date,
            presentation_time=presentation_time,
            location=location,
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

    flash(request, "Presentation schedule saved.")

    return RedirectResponse(
        url=request.url_for(
            "review_submission_view",
            submission_id=submission_id,
        ),
        status_code=303,
    )