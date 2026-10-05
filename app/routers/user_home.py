from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.repositories.submission import SubmissionRepository
from app.services.submission_service import SubmissionService


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    repository = SubmissionRepository(db)
    service = SubmissionService(repository)
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "submissions": service.list_researcher_submissions(user.id),
        }
    )