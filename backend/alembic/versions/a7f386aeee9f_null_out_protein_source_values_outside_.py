"""null out protein_source values outside the substitution vocabulary

Revision ID: a7f386aeee9f
Revises: be16d5b1145d
Create Date: 2026-07-26 18:57:35.201134

protein_source moves from freeform admin text to a constrained vocabulary
(see matching/substitution.py's RECIPE_PROTEIN_VOCABULARY) so it always
matches a substitution-table entry exactly. Existing rows with a value
outside that vocabulary are nulled out rather than guessed at — the admin
can re-tag them from the (now dropdown) recipe edit form. The vocabulary is
inlined here rather than imported, since a migration must stay stable even
after the app's vocabulary changes further.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7f386aeee9f'
down_revision: str | Sequence[str] | None = 'be16d5b1145d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Snapshot of RECIPE_PROTEIN_VOCABULARY at the time this migration was written.
_KNOWN_PROTEIN_SOURCES = [
    "aubergine", "carotte fumee", "champignon", "champignon pleurote",
    "champignons haches", "champignons shiitake seches", "coeur de palmier",
    "haricots rouges", "haricots rouges epices", "jacque", "lentilles",
    "lentilles corail", "noix de coco fumee", "pois chiches",
    "pois chiches ecrases", "proteines de soja texturees", "seitan",
    "seitan epice", "seitan hache", "tempeh", "tempeh fume", "tofu",
    "tofu emiette", "tofu ferme", "tofu fume", "tomate marinee",
]


def upgrade() -> None:
    """Data migration: no schema change."""
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE recipes SET protein_source = NULL "
            "WHERE protein_source IS NOT NULL AND protein_source NOT IN :vocabulary"
        ).bindparams(sa.bindparam("vocabulary", expanding=True)),
        {"vocabulary": _KNOWN_PROTEIN_SOURCES},
    )


def downgrade() -> None:
    """Irreversible: the original freeform values were overwritten with NULL
    and aren't recoverable."""
    pass
