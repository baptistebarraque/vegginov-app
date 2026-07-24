"""/admin/recipes(...) — admin-only, validate input, call the service,
serialize output.

multipart/form-data, not JSON: an optional image upload requires it. Text
list fields (allergens/instructions) arrive as repeated form fields
(FastAPI collects them into a list). `ingredients` is the exception: each
entry is a {name, quantity} pair, which multipart's flat key-value fields
can't express as repeated fields, so it travels as one JSON-encoded string
field instead, validated against IngredientEntrySchema.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.schemas.recipe import (
    CsvImportResponse,
    CsvImportRowError,
    IngredientEntrySchema,
    RecipeListItem,
    RecipeResponse,
)
from veggie_app.services import auth_service, image_service, recipe_import_service, recipe_service
from veggie_app.services.image_service import InvalidImageError
from veggie_app.services.recipe_import_service import CsvImportError
from veggie_app.services.recipe_service import IngredientQuantityError

router = APIRouter(prefix="/admin")

_ingredients_adapter = TypeAdapter(list[IngredientEntrySchema])


def _parse_ingredients_field(ingredients: str) -> list[dict]:
    try:
        parsed = _ingredients_adapter.validate_json(ingredients)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="Le champ 'ingredients' est invalide.") from exc
    return [entry.model_dump() for entry in parsed]


def _get_recipe_or_404(db: Session, recipe_id: int) -> Recipe:
    recipe = recipe_service.get_recipe(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable.")
    return recipe


def _to_response(recipe: Recipe) -> RecipeResponse:
    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        ingredients=recipe.ingredients,
        allergens=recipe.allergens,
        prep_time_minutes=recipe.prep_time_minutes,
        servings=recipe.servings,
        protein_source=recipe.protein_source,
        protein_grams=recipe.protein_grams,
        instructions=recipe.instructions,
        image_url=image_service.image_url(recipe.image_filename),
    )


@router.get("/recipes", response_model=list[RecipeListItem])
def list_recipes(
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> list[RecipeListItem]:
    return [
        RecipeListItem(
            id=recipe.id,
            title=recipe.title,
            image_url=image_service.image_url(recipe.image_filename),
        )
        for recipe in recipe_service.list_recipes(db)
    ]


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> RecipeResponse:
    return _to_response(_get_recipe_or_404(db, recipe_id))


@router.post("/recipes", response_model=RecipeResponse)
def create_recipe(
    title: str = Form(...),
    ingredients: str = Form(...),
    allergens: list[str] = Form([]),
    prep_time_minutes: int | None = Form(None),
    servings: int | None = Form(None),
    protein_source: str | None = Form(None),
    protein_grams: float | None = Form(None),
    instructions: list[str] = Form([]),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> RecipeResponse:
    ingredient_entries = _parse_ingredients_field(ingredients)

    image_filename = None
    if image is not None and image.filename:
        try:
            image_filename = image_service.save_recipe_image(image.filename, image.file.read())
        except InvalidImageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        recipe = recipe_service.create_recipe(
            db,
            title=title,
            ingredients=ingredient_entries,
            allergens=allergens,
            prep_time_minutes=prep_time_minutes,
            servings=servings,
            protein_source=protein_source,
            protein_grams=protein_grams,
            instructions=instructions,
            image_filename=image_filename,
        )
    except IngredientQuantityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return _to_response(recipe)


@router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    title: str = Form(...),
    ingredients: str = Form(...),
    allergens: list[str] = Form([]),
    prep_time_minutes: int | None = Form(None),
    servings: int | None = Form(None),
    protein_source: str | None = Form(None),
    protein_grams: float | None = Form(None),
    instructions: list[str] = Form([]),
    image: UploadFile | None = File(None),
    remove_image: bool = Form(False),
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> RecipeResponse:
    recipe = _get_recipe_or_404(db, recipe_id)
    ingredient_entries = _parse_ingredients_field(ingredients)

    image_filename = recipe.image_filename
    if image is not None and image.filename:
        try:
            new_filename = image_service.save_recipe_image(image.filename, image.file.read())
        except InvalidImageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        image_service.delete_recipe_image(image_filename)
        image_filename = new_filename
    elif remove_image:
        image_service.delete_recipe_image(image_filename)
        image_filename = None

    try:
        recipe_service.update_recipe(
            db,
            recipe,
            title=title,
            ingredients=ingredient_entries,
            allergens=allergens,
            prep_time_minutes=prep_time_minutes,
            servings=servings,
            protein_source=protein_source,
            protein_grams=protein_grams,
            instructions=instructions,
            image_filename=image_filename,
        )
    except IngredientQuantityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return _to_response(recipe)


@router.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> None:
    recipe = _get_recipe_or_404(db, recipe_id)
    image_service.delete_recipe_image(recipe.image_filename)
    recipe_service.delete_recipe(db, recipe)
    db.commit()


@router.post("/recipes/import", response_model=CsvImportResponse)
def import_recipes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> CsvImportResponse:
    content = file.file.read().decode("utf-8-sig")
    try:
        recipes = recipe_import_service.import_recipes_from_csv(db, content)
    except CsvImportError as exc:
        raise HTTPException(
            status_code=400,
            detail=[
                CsvImportRowError(row=error.row_number, message=error.message).model_dump()
                for error in exc.errors
            ],
        ) from exc
    db.commit()
    return CsvImportResponse(created_count=len(recipes))
