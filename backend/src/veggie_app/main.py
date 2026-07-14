"""FastAPI entrypoint."""

from fastapi import FastAPI

from veggie_app.api.routes import suggestions

app = FastAPI(title="Veggie App API")
app.include_router(suggestions.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
