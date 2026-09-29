from bson import ObjectId
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.mongodb import get_credentials_collection


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/dashboard",
    response_class=HTMLResponse
)
async def dashboard(request: Request):

    session_user = request.session.get("user")

    if not session_user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    try:
        user_id = ObjectId(session_user.get("id", ""))
    except (TypeError, ValueError):
        request.session.clear()
        return RedirectResponse("/", status_code=303)

    database_user = get_credentials_collection().find_one(
        {"_id": user_id},
        {"email": 1, "name": 1}
    )

    if not database_user:
        request.session.clear()
        return RedirectResponse("/", status_code=303)

    email = database_user.get("email", "")
    user = {
        "id": str(database_user["_id"]),
        "email": email,
        "name": database_user.get("name") or email.split("@", 1)[0].title()
    }
    request.session["user"] = user

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "user": user
        }
    )