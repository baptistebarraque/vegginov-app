"""The "Nutrition view": scores how well a candidate recipe's calories match a
user's calorie orientation preference (see docs/ROADMAP.md Phase 4 preferences).

Unlike the allergen/price hard filters (applied in services/recipe_service.py),
calorie orientation is a *soft* signal: it nudges the ranking rather than
excluding recipes, because calories are a continuum and a strong taste match
sitting just over a bucket boundary shouldn't be pruned. matching/fusion.py
blends this score into the final ranking with a small weight so title/ingredient
similarity stays dominant.

Pure functions only — no FastAPI or DB dependency — like the rest of matching/.
"""

# Calorie buckets in kcal per portion. Coarse and admin-tunable; they mirror the
# three-valued CALORIE_ORIENTATIONS ("low"/"balanced"/"high") in
# services/preference_service.py. A portion under LOW_MAX reads as light, over
# HIGH_MIN as hearty, and anything between as balanced.
LOW_MAX = 400.0
HIGH_MIN = 700.0

# Returned when we cannot judge the match: no orientation asked for, or the
# recipe has no calorie data yet (CIQUAL backfill still pending). Neutral rather
# than 0 so un-populated recipes aren't buried while the data lands.
NEUTRAL_SCORE = 0.5

# Ordered so adjacency can be measured by index distance: low <-> balanced <->
# high. "low" and "high" are two steps apart (opposite ends).
_ORIENTATION_ORDER = ("low", "balanced", "high")


def _calorie_bucket(calories_per_portion: float) -> str:
    if calories_per_portion < LOW_MAX:
        return "low"
    if calories_per_portion > HIGH_MIN:
        return "high"
    return "balanced"


def calorie_orientation_score(
    calories_per_portion: float | None, orientation: str | None
) -> float:
    """How well a recipe's per-portion calories match the desired orientation,
    in [0, 1]. Exact bucket match scores 1.0, an adjacent bucket 0.5, and the
    opposite end 0.0. Returns NEUTRAL_SCORE when there's nothing to judge:
    orientation is None (user is indifferent) or calories are missing."""
    if orientation is None or calories_per_portion is None:
        return NEUTRAL_SCORE
    if orientation not in _ORIENTATION_ORDER:
        return NEUTRAL_SCORE

    recipe_bucket = _calorie_bucket(calories_per_portion)
    distance = abs(_ORIENTATION_ORDER.index(recipe_bucket) - _ORIENTATION_ORDER.index(orientation))
    # distance is 0 (match), 1 (adjacent) or 2 (opposite ends) -> 1.0, 0.5, 0.0.
    return 1.0 - distance * 0.5
