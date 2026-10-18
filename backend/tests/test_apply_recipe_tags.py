import json
from pathlib import Path

import pytest

from scripts.apply_recipe_tags import DEFAULT_TAGS_PATH, load_tags
from veggie_app.services.recipe_service import DishStructureError


def test_load_tags_reads_dish_types_and_cuisine(tmp_path: Path) -> None:
    path = tmp_path / "tags.json"
    path.write_text(
        json.dumps({"tags": {"Dahl": {"dish_types": ["curry"], "cuisine": "indienne"}}}),
        encoding="utf-8",
    )

    assert load_tags(path) == {"Dahl": (["curry"], "indienne")}


def test_load_tags_rejects_an_invalid_entry_naming_its_title(tmp_path: Path) -> None:
    path = tmp_path / "tags.json"
    path.write_text(
        json.dumps({"tags": {"Dahl": {"dish_types": ["plat mystère"], "cuisine": None}}}),
        encoding="utf-8",
    )

    with pytest.raises(DishStructureError, match="Dahl"):
        load_tags(path)


def test_committed_tags_file_is_valid() -> None:
    assert load_tags(DEFAULT_TAGS_PATH)
