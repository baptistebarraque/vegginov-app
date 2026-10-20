"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from veggie_app.api.routes import (
    admin_recipes,
    admin_users,
    auth,
    likes,
    preferences,
    suggestions,
    watchlist,
)
from veggie_app.config import settings

# StaticFiles requires the directory to exist at mount time.
settings.upload_dir.mkdir(parents=True, exist_ok=True)


def api_docs_urls() -> dict[str, str | None]:
    """Swagger/ReDoc/OpenAPI in development only: in production they would
    hand anyone a map of every endpoint, admin ones included."""
    if settings.app_env == "production":
        return {"docs_url": None, "redoc_url": None, "openapi_url": None}
    return {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}


app = FastAPI(title="Veggie App API", **api_docs_urls())
app.add_middleware(
    CORSMiddleware,
    # CORS_ALLOWED_ORIGINS (config.py): the Vite dev server by default, the
    # public frontend URL in production. Cookies are involved, so this must
    # stay an explicit list, never "*".
    allow_origins=settings.cors_allowed_origins,
    # Required so the browser sends/receives the admin session cookie.
    # Safe with an explicit origin list above (browsers reject this combined
    # with allow_origins=["*"]).
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(suggestions.router)
app.include_router(auth.router)
app.include_router(admin_recipes.router)
app.include_router(admin_users.router)
app.include_router(preferences.router)
app.include_router(watchlist.router)
app.include_router(likes.router)
app.mount("/media", StaticFiles(directory=settings.upload_dir), name="media")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
