"""Interactive CLI for creating an admin account.

Run with: uv run python -m veggie_app.admin.create_admin_cli
"""

import getpass
import logging

from veggie_app.database import SessionLocal
from veggie_app.services import auth_service

# See add_recipe_cli.py for why this is a dedicated, non-propagating handler
# rather than logging.basicConfig.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)


def _prompt_email() -> str:
    while True:
        try:
            return auth_service.normalize_email(input("Email de l'admin : "))
        except auth_service.InvalidEmailError as exc:
            logger.warning(str(exc))


def _prompt_password() -> str:
    while True:
        password = getpass.getpass("Mot de passe : ")
        try:
            auth_service.validate_new_password(password)
        except auth_service.InvalidPasswordError as exc:
            logger.warning(str(exc))
            continue
        confirmation = getpass.getpass("Confirmer le mot de passe : ")
        if password != confirmation:
            logger.warning("Les mots de passe ne correspondent pas.")
            continue
        return password


def main() -> None:
    email = _prompt_email()
    password = _prompt_password()

    db = SessionLocal()
    try:
        admin = auth_service.register_user(db, email, password, is_admin=True)
        db.commit()
        admin_id = admin.id
    finally:
        db.close()

    logger.info("Admin créé : #%s %s", admin_id, email)


if __name__ == "__main__":
    main()
