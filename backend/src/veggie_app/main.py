"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from veggie_app.api.routes import admin_recipes, auth, preferences, suggestions, watchlist
from veggie_app.config import settings

# StaticFiles requires the directory to exist at mount time.
settings.upload_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Veggie App API")
app.add_middleware(
    CORSMiddleware,
    # Vite dev server origin. Both host forms are listed since browsers treat
    # localhost and 127.0.0.1 as different origins for CORS purposes, and
    # cookies are involved here (unlike the origin-less /suggestions calls).
    # Revisit once the frontend has a deployed URL.
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
app.include_router(preferences.router)
app.include_router(watchlist.router)
app.mount("/media", StaticFiles(directory=settings.upload_dir), name="media")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
