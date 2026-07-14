"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from veggie_app.api.routes import suggestions

app = FastAPI(title="Veggie App API")
app.add_middleware(
    CORSMiddleware,
    # Vite dev server origin. Revisit once the frontend has a deployed URL.
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(suggestions.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
