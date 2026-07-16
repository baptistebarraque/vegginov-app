"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from veggie_app.api.routes import admin_recipes, auth, suggestions

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
