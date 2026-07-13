"""FastAPI entrypoint."""

from fastapi import FastAPI

app = FastAPI(title="Veggie App API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}