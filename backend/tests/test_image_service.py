from pathlib import Path

import pytest

from veggie_app.services import image_service

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-png-bytes"


@pytest.fixture(autouse=True)
def _tmp_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_service.settings, "upload_dir", tmp_path / "uploads")


def test_save_recipe_image_writes_file_with_generated_name() -> None:
    stored_filename = image_service.save_recipe_image("photo.PNG", PNG_BYTES)

    assert stored_filename.endswith(".png")
    saved_path = image_service.settings.upload_dir / stored_filename
    assert saved_path.read_bytes() == PNG_BYTES


def test_save_recipe_image_rejects_disallowed_extension() -> None:
    with pytest.raises(image_service.InvalidImageError):
        image_service.save_recipe_image("recipe.gif", b"data")


def test_save_recipe_image_rejects_oversized_file() -> None:
    oversized = b"0" * (image_service.MAX_IMAGE_SIZE_BYTES + 1)
    with pytest.raises(image_service.InvalidImageError):
        image_service.save_recipe_image("photo.jpg", oversized)


def test_image_url_returns_none_for_no_filename() -> None:
    assert image_service.image_url(None) is None


def test_image_url_builds_media_path() -> None:
    assert image_service.image_url("abc123.png") == "/media/abc123.png"


def test_delete_recipe_image_removes_the_file() -> None:
    stored_filename = image_service.save_recipe_image("photo.png", PNG_BYTES)
    saved_path = image_service.settings.upload_dir / stored_filename
    assert saved_path.exists()

    image_service.delete_recipe_image(stored_filename)

    assert not saved_path.exists()


def test_delete_recipe_image_does_nothing_for_none() -> None:
    image_service.delete_recipe_image(None)  # must not raise


def test_delete_recipe_image_does_nothing_for_missing_file() -> None:
    image_service.delete_recipe_image("does-not-exist.png")  # must not raise


def test_save_recipe_image_rejects_content_that_is_not_the_claimed_format() -> None:
    # An HTML page renamed .png must not be stored and served from /media.
    with pytest.raises(image_service.InvalidImageError, match="pas une image"):
        image_service.save_recipe_image("photo.png", b"<html><script>alert(1)</script></html>")


def test_save_recipe_image_rejects_png_bytes_named_jpg() -> None:
    with pytest.raises(image_service.InvalidImageError):
        image_service.save_recipe_image("photo.jpg", PNG_BYTES)


def test_save_recipe_image_accepts_jpeg_signature() -> None:
    stored_filename = image_service.save_recipe_image("photo.jpeg", b"\xff\xd8\xff\xe0rest")

    assert stored_filename.endswith(".jpeg")
