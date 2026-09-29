from fastapi import (
    APIRouter,
    Form,
    Request,
    status
)

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.auth_service import authenticate_user


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/",
    response_class=HTMLResponse
)
async def login_page(request: Request):

    if request.session.get("user"):
        return RedirectResponse(
            "/dashboard",
            status_code=status.HTTP_302_FOUND
        )

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request
        }
    )


@router.post(
    "/login",
    response_class=HTMLResponse
)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):

    email = email.strip().lower()

    user = authenticate_user(
        email,
        password
    )

    if not user:

        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "error": "Invalid email or password.",
                "email": email
            },
            status_code=401
        )

    request.session.clear()

    request.session["user"] = {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name") or user["email"].split("@")[0].title()
    }

    return RedirectResponse(
        "/dashboard",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get(
    "/forgot-password",
    response_class=HTMLResponse
)
async def forgot_password(request: Request):

    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {
            "request": request
        }
    )


@router.post("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        "/",
        status_code=status.HTTP_303_SEE_OTHER
    )