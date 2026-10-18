import pytest
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import recipe_service
from veggie_app.services.recipe_service import (
    IngredientQuantityError,
    PriceTierError,
    ProteinSourceError,
)


def _unit_vector(index: int) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    vector[index] = 1.0
    return vector


@pytest.fixture(autouse=True)
def _stub_query_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the stubbed-but-still-pseudo-random embed_text with a fixed
    vector, so tests can assert exact ranking order instead of relying on
    whatever a hash-derived vector happens to produce."""
    monkeypatch.setattr(recipe_service, "embed_text", lambda text: _unit_vector(0))


def test_get_suggestions_ranks_closest_first(db_session: Session) -> None:
    close = Recipe(title="Proche", ingredients=[], allergens=[], embedding=_unit_vector(0))
    far = Recipe(title="Loin", ingredients=[], allergens=[], embedding=_unit_vector(1))
    db_session.add_all([far, close])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert [s.title for s in suggestions] == ["Proche", "Loin"]
    assert suggestions[0].score > suggestions[1].score


def test_get_suggestions_caps_at_suggestion_count(db_session: Session) -> None:
    for i in range(recipe_service.SUGGESTION_COUNT + 2):
        db_session.add(
            Recipe(title=f"Recette {i}", ingredients=[], allergens=[], embedding=_unit_vector(0))
        )
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert len(suggestions) == recipe_service.SUGGESTION_COUNT


def test_get_suggestions_excludes_recipes_matching_excluded_allergens(db_session: Session) -> None:
    safe = Recipe(
        title="Sans gluten", ingredients=[], allergens=["lactose"], embedding=_unit_vector(0)
    )
    unsafe = Recipe(
        title="Avec gluten", ingredients=[], allergens=["gluten"], embedding=_unit_vector(0)
    )
    db_session.add_all([safe, unsafe])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(
        db_session, "query", [], excluded_allergens=["gluten"]
    )

    assert [s.title for s in suggestions] == ["Sans gluten"]


def test_get_suggestions_ignores_exclusion_when_none_given(db_session: Session) -> None:
    unsafe = Recipe(
        title="Avec gluten", ingredients=[], allergens=["gluten"], embedding=_unit_vector(0)
    )
    db_session.add(unsafe)
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [], excluded_allergens=None)

    assert [s.title for s in suggestions] == ["Avec gluten"]


def test_get_suggestions_excludes_recipes_above_price_budget(db_session: Session) -> None:
    cheap = Recipe(
        title="Bon marché", ingredients=[], allergens=[], price_tier=1, embedding=_unit_vector(0)
    )
    pricey = Recipe(
        title="Cher", ingredients=[], allergens=[], price_tier=3, embedding=_unit_vector(0)
    )
    db_session.add_all([cheap, pricey])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [], max_price_tier=2)

    assert [s.title for s in suggestions] == ["Bon marché"]


def test_get_suggestions_keeps_unpriced_recipes_under_budget(db_session: Session) -> None:
    # A recipe with no price_tier yet must not be dropped by the budget cap.
    unpriced = Recipe(
        title="Sans prix", ingredients=[], allergens=[], price_tier=None, embedding=_unit_vector(0)
    )
    db_session.add(unpriced)
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [], max_price_tier=1)

    assert [s.title for s in suggestions] == ["Sans prix"]


def test_get_suggestions_top_price_tier_is_indifferent(db_session: Session) -> None:
    # max_price_tier == MAX_PRICE_TIER (€€€) keeps everything, including the
    # most expensive recipes.
    pricey = Recipe(
        title="Cher", ingredients=[], allergens=[], price_tier=3, embedding=_unit_vector(0)
    )
    db_session.add(pricey)
    db_session.flush()

    suggestions = recipe_service.get_suggestions(
        db_session, "query", [], max_price_tier=recipe_service.MAX_PRICE_TIER
    )

    assert [s.title for s in suggestions] == ["Cher"]


def test_get_suggestions_orientation_ranks_matching_calories_first(db_session: Session) -> None:
    high = Recipe(
        title="Copieux",
        ingredients=[],
        allergens=[],
        calories_per_portion=900.0,
        embedding=_unit_vector(0),
    )
    low = Recipe(
        title="Léger",
        ingredients=[],
        allergens=[],
        calories_per_portion=300.0,
        embedding=_unit_vector(0),
    )
    db_session.add_all([high, low])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(
        db_session, "query", [], calorie_orientation="low"
    )

    assert [s.title for s in suggestions] == ["Léger", "Copieux"]


def test_get_suggestions_marks_watchlisted_recipes(db_session: Session) -> None:
    saved = Recipe(title="Sauvegardée", ingredients=[], allergens=[], embedding=_unit_vector(0))
    other = Recipe(title="Autre", ingredients=[], allergens=[], embedding=_unit_vector(0))
    db_session.add_all([saved, other])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(
        db_session, "query", [], watchlisted_recipe_ids={saved.id}
    )

    by_title = {s.title: s.is_watchlisted for s in suggestions}
    assert by_title == {"Sauvegardée": True, "Autre": False}


def test_get_suggestions_defaults_is_watchlisted_to_false_when_anonymous(
    db_session: Session,
) -> None:
    db_session.add(Recipe(title="Recette", ingredients=[], allergens=[], embedding=_unit_vector(0)))
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert suggestions[0].is_watchlisted is False


def test_get_suggestions_returns_ingredients_with_quantities(db_session: Session) -> None:
    ingredients = [
        {"name": "lentilles", "quantity": "200g"},
        {"name": "curry", "quantity": None},
    ]
    db_session.add(
        Recipe(title="Curry", ingredients=ingredients, allergens=[], embedding=_unit_vector(0))
    )
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert [(i.name, i.quantity) for i in suggestions[0].ingredients] == [
        ("lentilles", "200g"),
        ("curry", None),
    ]


def test_get_suggestions_returns_full_recipe_detail(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session,
        title="Curry de lentilles",
        ingredients=[{"name": "lentilles", "quantity": "200g"}],
        allergens=["gluten"],
        prep_time_minutes=30,
        servings=4,
        protein_source="lentilles",
        protein_grams=18.5,
        instructions=["Faire revenir les oignons"],
        image_filename="abc123.png",
    )
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.id == recipe.id
    assert suggestion.allergens == ["gluten"]
    assert suggestion.prep_time_minutes == 30
    assert suggestion.servings == 4
    assert suggestion.protein_source == "lentilles"
    assert suggestion.protein_grams == 18.5
    assert suggestion.instructions == ["Faire revenir les oignons"]
    assert suggestion.image_url == "/media/abc123.png"


def test_create_recipe_persists_with_embedding(db_session: Session) -> None:
    ingredients = [
        {"name": "lentilles", "quantity": "200g"},
        {"name": "curry", "quantity": "1 cuillère à soupe"},
    ]
    recipe = recipe_service.create_recipe(
        db_session,
        title="Curry de lentilles",
        ingredients=ingredients,
        allergens=["gluten"],
        prep_time_minutes=30,
        servings=4,
        protein_source="lentilles",
        protein_grams=18.5,
        instructions=["Faire revenir les oignons", "Ajouter les lentilles et le curry"],
        image_filename="abc123.png",
    )

    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.title == "Curry de lentilles"
    assert fetched.ingredients == ingredients
    assert fetched.allergens == ["gluten"]
    assert fetched.prep_time_minutes == 30
    assert fetched.servings == 4
    assert fetched.protein_source == "lentilles"
    assert fetched.protein_grams == 18.5
    assert fetched.instructions == [
        "Faire revenir les oignons",
        "Ajouter les lentilles et le curry",
    ]
    assert fetched.image_filename == "abc123.png"
    assert list(fetched.embedding) == _unit_vector(0)


def test_create_recipe_defaults_optional_fields(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )

    assert recipe.allergens == []
    assert recipe.prep_time_minutes is None
    assert recipe.servings is None
    assert recipe.protein_source is None
    assert recipe.protein_grams is None
    assert recipe.instructions == []
    assert recipe.image_filename is None


def test_create_recipe_allows_missing_quantity_without_servings(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session,
        title="Salade",
        ingredients=[{"name": "laitue", "quantity": None}],
        servings=None,
    )

    assert recipe.ingredients == [{"name": "laitue", "quantity": None}]


def test_create_recipe_rejects_missing_quantity_when_servings_set(db_session: Session) -> None:
    with pytest.raises(IngredientQuantityError):
        recipe_service.create_recipe(
            db_session,
            title="Salade",
            ingredients=[{"name": "laitue", "quantity": None}],
            servings=2,
        )


def test_validate_ingredient_quantities_reports_all_missing_names() -> None:
    with pytest.raises(IngredientQuantityError) as exc_info:
        recipe_service.validate_ingredient_quantities(
            [
                {"name": "laitue", "quantity": None},
                {"name": "tomate", "quantity": "2"},
                {"name": "concombre", "quantity": None},
            ],
            servings=2,
        )

    assert "laitue" in str(exc_info.value)
    assert "concombre" in str(exc_info.value)
    assert "tomate" not in str(exc_info.value)


def test_validate_ingredient_quantities_ignores_missing_when_no_servings() -> None:
    recipe_service.validate_ingredient_quantities(
        [{"name": "laitue", "quantity": None}], servings=None
    )


def test_validate_protein_source_accepts_known_value() -> None:
    recipe_service.validate_protein_source("tofu")


def test_validate_protein_source_accepts_none() -> None:
    recipe_service.validate_protein_source(None)


def test_validate_protein_source_rejects_unknown_value() -> None:
    with pytest.raises(ProteinSourceError):
        recipe_service.validate_protein_source("boeuf haché")


def test_create_recipe_rejects_unknown_protein_source(db_session: Session) -> None:
    with pytest.raises(ProteinSourceError):
        recipe_service.create_recipe(
            db_session,
            title="Salade",
            ingredients=[{"name": "laitue", "quantity": None}],
            protein_source="steak",
        )


def test_validate_price_tier_accepts_in_range_and_none() -> None:
    recipe_service.validate_price_tier(None)
    recipe_service.validate_price_tier(1)
    recipe_service.validate_price_tier(recipe_service.MAX_PRICE_TIER)


def test_validate_price_tier_rejects_out_of_range() -> None:
    with pytest.raises(PriceTierError):
        recipe_service.validate_price_tier(0)
    with pytest.raises(PriceTierError):
        recipe_service.validate_price_tier(recipe_service.MAX_PRICE_TIER + 1)


def test_compute_protein_density_is_grams_per_100_kcal() -> None:
    assert recipe_service.compute_protein_density(20.0, 200.0) == 10.0


def test_compute_protein_density_is_none_when_inputs_missing_or_zero() -> None:
    assert recipe_service.compute_protein_density(None, 200.0) is None
    assert recipe_service.compute_protein_density(20.0, None) is None
    assert recipe_service.compute_protein_density(20.0, 0.0) is None


def test_create_recipe_persists_calories_and_price_tier(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session,
        title="Tofu grillé",
        ingredients=[{"name": "tofu", "quantity": None}],
        protein_grams=20.0,
        calories_per_portion=200.0,
        price_tier=2,
    )

    assert recipe.calories_per_portion == 200.0
    assert recipe.price_tier == 2


def test_create_recipe_rejects_out_of_range_price_tier(db_session: Session) -> None:
    with pytest.raises(PriceTierError):
        recipe_service.create_recipe(
            db_session,
            title="Salade",
            ingredients=[{"name": "laitue", "quantity": None}],
            price_tier=5,
        )


def test_get_suggestions_computes_protein_density(db_session: Session) -> None:
    recipe_service.create_recipe(
        db_session,
        title="Tofu grillé",
        ingredients=[{"name": "tofu", "quantity": None}],
        protein_grams=20.0,
        calories_per_portion=200.0,
        price_tier=2,
    )
    db_session.flush()

    suggestion = recipe_service.get_suggestions(db_session, "query", [])[0]

    assert suggestion.calories_per_portion == 200.0
    assert suggestion.price_tier == 2
    assert suggestion.protein_density == 10.0


def test_list_protein_source_options_returns_known_vocabulary() -> None:
    options = recipe_service.list_protein_source_options()

    assert "tofu" in options
    assert "seitan" in options


def test_list_recipes_orders_by_title(db_session: Session) -> None:
    db_session.add_all(
        [
            Recipe(title="Salade", ingredients=[], allergens=[], embedding=_unit_vector(0)),
            Recipe(title="Curry", ingredients=[], allergens=[], embedding=_unit_vector(0)),
        ]
    )
    db_session.flush()

    titles = [recipe.title for recipe in recipe_service.list_recipes(db_session)]

    assert titles == ["Curry", "Salade"]


def test_get_recipe_returns_none_for_missing_id(db_session: Session) -> None:
    assert recipe_service.get_recipe(db_session, 999999) is None


def test_update_recipe_overwrites_fields_and_recomputes_embedding(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )

    updated = recipe_service.update_recipe(
        db_session,
        recipe,
        title="Grande salade",
        ingredients=[{"name": "laitue", "quantity": "200g"}, {"name": "tomate", "quantity": "2"}],
        servings=2,
        image_filename="new.png",
    )

    assert updated is recipe
    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.title == "Grande salade"
    assert fetched.ingredients == [
        {"name": "laitue", "quantity": "200g"},
        {"name": "tomate", "quantity": "2"},
    ]
    assert fetched.servings == 2
    assert fetched.image_filename == "new.png"


def test_update_recipe_rejects_missing_quantity_when_servings_set(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )

    with pytest.raises(IngredientQuantityError):
        recipe_service.update_recipe(
            db_session,
            recipe,
            title="Salade",
            ingredients=[{"name": "laitue", "quantity": None}],
            servings=2,
        )


def test_delete_recipe_removes_row(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )
    recipe_id = recipe.id

    recipe_service.delete_recipe(db_session, recipe)

    assert db_session.get(Recipe, recipe_id) is None


def test_build_candidate_exposes_what_matching_needs() -> None:
    recipe = Recipe(
        id=7,
        title="Dahl",
        ingredients=[
            {"name": "lentilles corail", "quantity": "200 g"},
            {"name": "lait de coco", "quantity": None},
        ],
        allergens=[],
        protein_source="lentilles corail",
        calories_per_portion=450.0,
        embedding=_unit_vector(2),
    )

    candidate = recipe_service.build_candidate(recipe)

    assert candidate.id == 7
    assert candidate.title_embedding == _unit_vector(2)
    assert candidate.ingredient_names == ["lentilles corail", "lait de coco"]
    assert candidate.protein_source == "lentilles corail"
    assert candidate.calories_per_portion == 450.0


def test_get_suggestions_weighs_ingredients_on_the_whole_corpus(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ingredient weights must not depend on the caller's filters: a recipe
    excluded by an allergen still counts when measuring how common an
    ingredient is."""
    captured = {}
    real = recipe_service.compute_ingredient_weights

    def spy(ingredient_lists):  # noqa: ANN001, ANN202 — passthrough spy
        lists = [list(names) for names in ingredient_lists]
        captured["lists"] = lists
        return real(lists)

    monkeypatch.setattr(recipe_service, "compute_ingredient_weights", spy)
    kept = Recipe(
        title="Gardée",
        ingredients=[{"name": "riz", "quantity": None}],
        allergens=[],
        embedding=_unit_vector(0),
    )
    excluded = Recipe(
        title="Exclue",
        ingredients=[{"name": "arachide", "quantity": None}],
        allergens=["arachide"],
        embedding=_unit_vector(1),
    )
    db_session.add_all([kept, excluded])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(
        db_session, "query", [], excluded_allergens=["arachide"]
    )

    assert [s.title for s in suggestions] == ["Gardée"]
    assert ["arachide"] in captured["lists"]


def test_validate_dish_structure_accepts_known_values() -> None:
    recipe_service.validate_dish_structure(["ragoût", "soupe"], "française")
    recipe_service.validate_dish_structure([], None)


def test_validate_dish_structure_rejects_unknown_values() -> None:
    with pytest.raises(recipe_service.DishStructureError):
        recipe_service.validate_dish_structure(["plat mystère"], None)
    with pytest.raises(recipe_service.DishStructureError):
        recipe_service.validate_dish_structure([], "martienne")


def test_create_recipe_stores_dish_structure_without_blanks_or_duplicates(
    db_session: Session,
) -> None:
    recipe = recipe_service.create_recipe(
        db_session,
        title="Lasagnes",
        ingredients=[{"name": "lentilles", "quantity": None}],
        dish_types=["gratin", "", "pâtes", "gratin"],
        cuisine="italienne",
    )

    assert recipe.dish_types == ["gratin", "pâtes"]
    assert recipe.cuisine == "italienne"


def test_build_candidate_carries_dish_structure() -> None:
    recipe = Recipe(
        id=1,
        title="Curry",
        ingredients=[],
        allergens=[],
        dish_types=["curry"],
        cuisine="indienne",
        embedding=_unit_vector(0),
    )

    candidate = recipe_service.build_candidate(recipe)

    assert list(candidate.dish_types) == ["curry"]
    assert candidate.cuisine == "indienne"


def test_get_suggestions_ranks_by_dish_structure_inferred_from_the_title(
    db_session: Session,
) -> None:
    # Same title embedding and no ingredients: only the structure view can
    # tell these two apart, and "bourguignon" names a French stew.
    stew = Recipe(
        title="Ragoût",
        ingredients=[],
        allergens=[],
        dish_types=["ragoût"],
        cuisine="française",
        embedding=_unit_vector(0),
    )
    salad = Recipe(
        title="Salade",
        ingredients=[],
        allergens=[],
        dish_types=["salade"],
        cuisine="japonaise",
        embedding=_unit_vector(0),
    )
    db_session.add_all([salad, stew])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "Bœuf bourguignon", [])

    assert [s.title for s in suggestions] == ["Ragoût", "Salade"]
