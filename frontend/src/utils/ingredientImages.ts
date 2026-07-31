import type { IngredientEntry } from "../types/recipe";

export interface IngredientImageMatch {
  key: string;
  name: string;
  imageUrl: string;
}

interface ManifestEntry {
  key: string;
  keywords: string[];
}

// One PNG per key must exist in public/ingredients/ (cutout, transparent
// background — see the decomposition burst in RecipeDetailPanel). Keep this
// list in sync with that folder: an entry with no matching file just never
// gets returned by matchIngredientImages, so nothing breaks, but it's dead
// weight. Order matters where two entries share a root word (e.g. "oignon"
// vs "oignon rouge") — the more specific keyword must come first so it wins.
const MANIFEST: ManifestEntry[] = [
  { key: "red-onion", keywords: ["oignon rouge"] },
  { key: "rice-noodles", keywords: ["nouilles de riz"] },
  { key: "sweet-potato", keywords: ["patate douce", "patates douces"] },
  { key: "onion", keywords: ["oignon"] },
  { key: "rice", keywords: ["riz"] },
  { key: "potato", keywords: ["pomme de terre", "pommes de terre"] },
  { key: "bell-pepper", keywords: ["poivron"] },
  { key: "black-beans", keywords: ["haricots noirs", "haricot noir"] },
  { key: "green-beans", keywords: ["haricots verts", "haricot vert"] },
  { key: "kidney-beans", keywords: ["haricots rouges", "haricot rouge"] },
  { key: "broccoli", keywords: ["brocoli"] },
  { key: "carrot", keywords: ["carotte"] },
  { key: "cauliflower", keywords: ["chou-fleur", "chou fleur"] },
  { key: "celery", keywords: ["céleri"] },
  { key: "chickpeas", keywords: ["pois chiche"] },
  { key: "corn", keywords: ["maïs"] },
  { key: "cucumber", keywords: ["concombre"] },
  { key: "eggplant", keywords: ["aubergine"] },
  { key: "eggs", keywords: ["œuf", "oeuf"] },
  { key: "feta", keywords: ["feta"] },
  { key: "garlic", keywords: ["ail"] },
  { key: "greek-yogurt", keywords: ["yaourt grec"] },
  { key: "green-lentils", keywords: ["lentilles vertes", "lentille verte"] },
  { key: "red-lentils", keywords: ["lentilles corail", "lentille corail"] },
  { key: "leek", keywords: ["poireau"] },
  { key: "mozzarella", keywords: ["mozzarella"] },
  { key: "oats", keywords: ["flocons d'avoine", "avoine"] },
  { key: "parmesan", keywords: ["parmesan"] },
  { key: "pasta", keywords: ["pâtes"] },
  { key: "pumpkin", keywords: ["potiron", "citrouille"] },
  { key: "quinoa", keywords: ["quinoa"] },
  { key: "spinach", keywords: ["épinard"] },
  { key: "tofu", keywords: ["tofu"] },
  { key: "tomato", keywords: ["tomate"] },
  { key: "zucchini", keywords: ["courgette"] },
];

function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const NORMALIZED_MANIFEST = MANIFEST.map((entry) => ({
  key: entry.key,
  patterns: entry.keywords.map((keyword) => new RegExp(`\\b${escapeRegExp(normalize(keyword))}`)),
}));

// Only returns ingredients with a recognized photo — no generic fallback, by
// design, so unmatched ingredients (herbs, spices, one-off items) are simply
// left out of the decomposition animation rather than shown as a placeholder.
export function matchIngredientImages(
  ingredients: IngredientEntry[],
  maxCount = 6,
): IngredientImageMatch[] {
  const matches: IngredientImageMatch[] = [];
  const seenKeys = new Set<string>();

  for (const ingredient of ingredients) {
    if (matches.length >= maxCount) {
      break;
    }
    const normalizedName = normalize(ingredient.name);
    const entry = NORMALIZED_MANIFEST.find((candidate) =>
      candidate.patterns.some((pattern) => pattern.test(normalizedName)),
    );
    if (!entry || seenKeys.has(entry.key)) {
      continue;
    }
    seenKeys.add(entry.key);
    matches.push({
      key: entry.key,
      name: ingredient.name,
      imageUrl: `/ingredients/${entry.key}.png`,
    });
  }

  return matches;
}
