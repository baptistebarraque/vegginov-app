"""Local-disk storage for recipe images (see docs/ARCHITECTURE.md "Recipe
image storage"). Files are saved under `settings.upload_dir` and served back
via the `/media` static mount in main.py.
"""

import uuid
from pathlib import Path

from veggie_app.config import settings

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
# The bytes every real file of each format starts with ("magic numbers").
# The extension alone is just a name: without this, an HTML or script file
# renamed photo.png would be stored and served back from /media.
_SIGNATURES = {
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
}


class InvalidImageError(ValueError):
    """Raised when an uploaded recipe image fails validation."""


def save_recipe_image(filename: str, contents: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidImageError("L'image doit être au format PNG ou JPEG.")
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise InvalidImageError("L'image dépasse la taille maximale de 5 Mo.")
    if not contents.startswith(_SIGNATURES[extension]):
        raise InvalidImageError("Le fichier n'est pas une image PNG ou JPEG valide.")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    (settings.upload_dir / stored_filename).write_bytes(contents)
    return stored_filename


def image_url(stored_filename: str | None) -> str | None:
    if stored_filename is None:
        return None
    return f"/media/{stored_filename}"


def delete_recipe_image(stored_filename: str | None) -> None:
    if stored_filename is None:
        return
    (settings.upload_dir / stored_filename).unlink(missing_ok=True)
