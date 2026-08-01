from veggie_app.matching.embeddings import EMBEDDING_DIM, embed_text


def test_embed_text_has_expected_dimension() -> None:
    assert len(embed_text("curry de lentilles")) == EMBEDDING_DIM


def test_embed_text_is_deterministic() -> None:
    assert embed_text("curry de lentilles") == embed_text("curry de lentilles")


def test_embed_text_differs_for_different_text() -> None:
    assert embed_text("curry de lentilles") != embed_text("gratin de courgettes")
