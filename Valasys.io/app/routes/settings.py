from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.mongodb import get_credentials_collection
from app.utils.security import (
    verify_password,
    hash_password
)


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/settings",
    response_class=HTMLResponse
)
async def settings_page(request: Request):

    user = request.session.get("user")

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "user": user
        }
    )


@router.post(
    "/settings/change-password",
    response_class=HTMLResponse
)
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):

    user = request.session.get("user")

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )


    # Check new password length

    if len(new_password) < 8:

        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "user": user,
                "error":
                    "New password must contain at least 8 characters."
            },
            status_code=400
        )


    # Check password confirmation

    if new_password != confirm_password:

        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "user": user,
                "error":
                    "New password and confirmation password do not match."
            },
            status_code=400
        )


    # Get MongoDB collection

    collection = get_credentials_collection()


    # Find logged-in user

    database_user = collection.find_one(
        {
            "email": user["email"]
        }
    )


    if not database_user:

        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "user": user,
                "error":
                    "User account could not be found."
            },
            status_code=404
        )


    # Verify old password

    stored_password = database_user.get("password")


    if not stored_password or not verify_password(
        old_password,
        stored_password
    ):

        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "user": user,
                "error":
                    "Your current password is incorrect."
            },
            status_code=400
        )


    # Don't allow same password

    if verify_password(
        new_password,
        stored_password
    ):

        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "user": user,
                "error":
                    "New password must be different from your old password."
            },
            status_code=400
        )


    # Hash new password

    new_hashed_password = hash_password(
        new_password
    )


    # Update MongoDB

    collection.update_one(
        {
            "_id": database_user["_id"]
        },
        {
            "$set": {
                "password": new_hashed_password
            }
        }
    )


    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "user": user,
            "success":
                "Password updated successfully."
        }
    )