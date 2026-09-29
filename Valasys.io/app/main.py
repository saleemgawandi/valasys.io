import os

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.routes import auth
from app.routes import dashboard
from app.routes import data
from app.routes import settings


load_dotenv()

SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-secret-key")
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "86400"))


app = FastAPI(
    title="Valasys.io"
)


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=SESSION_MAX_AGE,
    same_site="lax",
    https_only=False
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


app.include_router(auth.router)

app.include_router(dashboard.router)

app.include_router(data.router)

app.include_router(settings.router)

@app.get("/health")
async def health_check():

    return {
        "status": "ok",
        "application": "Valasys.io"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )