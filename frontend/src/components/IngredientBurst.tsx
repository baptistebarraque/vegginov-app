import { motion, useReducedMotion, type Variants } from "framer-motion";
import { matchIngredientImages } from "../utils/ingredientImages";
import type { IngredientEntry } from "../types/recipe";

interface IngredientBurstProps {
  ingredients: IngredientEntry[];
}

// Resting offsets (px from viewport centre) + tilt for up to 6 cut-outs
// flying out of the dish. Spread wide enough (|x| > ~300) to clear the
// max-w-lg (512px) panel, so they land on the dark backdrop beside it
// instead of hidden behind the opaque panel. Desktop-tuned for now.
const BURST_POSITIONS = [
  { x: -300, y: -140, rotate: -16 },
  { x: 300, y: -140, rotate: 16 },
  { x: -350, y: 60, rotate: 12 },
  { x: 350, y: 60, rotate: -12 },
  { x: -190, y: 210, rotate: -7 },
  { x: 190, y: 210, rotate: 7 },
];

const containerVariants: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

// Each cut-out starts small at the dish centre and springs out to its resting
// offset, so the set reads as the dish decomposing outward.
const itemVariants: Variants = {
  hidden: { opacity: 0, scale: 0.3, x: 0, y: 0, rotate: 0 },
  visible: ({ x, y, rotate }: { x: number; y: number; rotate: number }) => ({
    opacity: 1,
    scale: 1,
    x,
    y,
    rotate,
    transition: { type: "spring", stiffness: 120, damping: 14 },
  }),
};

// Purely decorative illustration of the recipe's ingredients "leaving" the
// dish — the accessible ingredient list already lives in RecipeDetailPanel's
// text content, so these images are aria-hidden.
function IngredientBurst({ ingredients }: IngredientBurstProps) {
  const prefersReducedMotion = useReducedMotion();
  const matches = matchIngredientImages(ingredients, BURST_POSITIONS.length);

  if (matches.length === 0 || prefersReducedMotion) {
    return null;
  }

  return (
    <motion.div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-40"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {matches.map((match, index) => (
        <motion.img
          key={match.key}
          src={match.imageUrl}
          alt=""
          className="absolute top-1/2 left-1/2 -mt-10 -ml-10 h-20 w-20 object-contain drop-shadow-xl"
          custom={BURST_POSITIONS[index]}
          variants={itemVariants}
        />
      ))}
    </motion.div>
  );
}

export default IngredientBurst;
