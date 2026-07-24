from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe


def test_post_suggestions_returns_matching_recipes(client: TestClient, db_session: Session) -> None:
    db_session.add(
        Recipe(
            title="Curry de lentilles",
            ingredients=[
                {"name": "lentilles", "quantity": None},
                {"name": "curry", "quantity": None},
            ],
            allergens=[],
            embedding=[0.1] * EMBEDDING_DIM,
        )
    )
    db_session.flush()

    response = client.post(
        "/suggestions", json={"title": "Curry de poulet", "ingredients": ["poulet"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["suggestions"]) == 1
    assert body["suggestions"][0]["title"] == "Curry de lentilles"
    assert body["suggestions"][0]["ingredients"] == ["lentilles", "curry"]


def test_post_suggestions_empty_db_returns_empty_list(client: TestClient) -> None:
    response = client.post("/suggestions", json={"title": "Curry de poulet", "ingredients": []})

    assert response.status_code == 200
    assert response.json() == {"suggestions": []}


def test_post_suggestions_requires_title(client: TestClient) -> None:
    response = client.post("/suggestions", json={"ingredients": ["poulet"]})

    assert response.status_code == 422
