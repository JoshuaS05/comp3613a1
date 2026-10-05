from fastapi import File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.submission import SubmissionRepository
from app.services.submission_service import SubmissionService
from app.repositories.review import ReviewRepository
from app.repositories.presentation import PresentationRepository
from app.services.tracking_service import TrackingService
from app.utilities.flash import flash
from . import router, templates


@router.get("/research/submissions/{submission_id}", name="track_submission_view")
async def track_submission_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    submission_id: int,
):
    service = TrackingService(
        SubmissionRepository(db),
        ReviewRepository(db),
        PresentationRepository(db),
    )
    try:
        submission, review, presentation, status_timeline = service.get_submission_details(
            submission_id=submission_id,
            researcher_id=user.id,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return templates.TemplateResponse(
        request=request,
        name="submission-status.html",
        context={
            "user": user,
            "submission": submission,
            "review": review,
            "presentation": presentation,
            "status_timeline": status_timeline,
        },
    )


@router.get("/research/submit", name="submit_research_form")
async def submit_research_form(request: Request, user: AuthDep):
    return templates.TemplateResponse(
        request=request,
        name="submit-research.html",
        context={"user": user},
    )


@router.get(
    "/research/submissions/{submission_id}/edit",
    name="edit_submission_view",
)
async def edit_submission_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    submission_id: int,
):
    service = SubmissionService(SubmissionRepository(db))

    try:
        submission = service.get_editable_submission(
            submission_id=submission_id,
            researcher_id=user.id,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return templates.TemplateResponse(
        request=request,
        name="edit-resubmit.html",
        context={
            "user": user,
            "submission": submission,
        },
    )


@router.post(
    "/research/submissions/{submission_id}/resubmit",
    name="resubmit_research",
)
async def resubmit_research(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    submission_id: int,
    title: str = Form(),
    abstract: str = Form(),
    submission_type: str = Form(),
    updated_file: UploadFile | None = File(default=None),
):
    repository = SubmissionRepository(db)
    service = SubmissionService(repository)

    try:
        service.resubmit_research(
            submission_id=submission_id,
            title=title,
            abstract=abstract,
            submission_type=submission_type,
            updated_file=updated_file,
            researcher_id=user.id,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    flash(request, "Research resubmitted successfully.")

    return RedirectResponse(
        url=request.url_for(
            "track_submission_view",
            submission_id=submission_id,
        ),
        status_code=303,
    )


@router.post("/research/submit", name="submit_research")
async def submit_research(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    title: str = Form(),
    abstract: str = Form(),
    submission_type: str = Form(),
    research_file: UploadFile = File(),
):
    repository = SubmissionRepository(db)
    service = SubmissionService(repository)

    service.submit_research(
        title=title,
        abstract=abstract,
        submission_type=submission_type,
        research_file=research_file,
        researcher_id=user.id,
    )

    flash(request, "Research submitted successfully.")

    return RedirectResponse(
        url=request.url_for("user_home_view"),
        status_code=303,
    )