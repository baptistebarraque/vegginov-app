# FRONTEND.md — Visual direction & v1 UI brief

> **How to use this file:** commit it as `docs/FRONTEND.md` and add a line in
> `CLAUDE.md` under "Checklist before implementing a feature":
> `8. For any frontend/visual work, read docs/FRONTEND.md first and follow it exactly.`
> This document is written in English (repo convention). All **user-facing
> strings stay in French**.

---

## 0. Scope of this pass

**In scope (v1 visual pass):** design tokens, typography, dark-green theme,
motion system, and a restyle of the pages that already exist (public search +
results, admin login, admin recipe list/form).

**Out of scope — do not build:** new features, new routes, new backend
endpoints, anything from Phase 2+ in `docs/ROADMAP.md` (nutritional scoring,
vegan mode, filters, accounts, ratings). If a visual idea here would require a
new API field, skip it and note it in the final summary instead of inventing an
endpoint.

**Do not touch** `backend/` at all in this pass, except `docs/` and `CLAUDE.md`
updates required by the rules below.

---

## 1. Hard constraints (inherited from CLAUDE.md)

1. UI strings in French; identifiers, comments, commit messages in English.
2. Every new dependency must be added to the stack table in `CLAUDE.md` with a
   one-line justification, in the same commit that introduces it.
3. No new top-level folders without updating the repository structure in
   `CLAUDE.md`. New folders under `frontend/src/` also require updating it.
4. `strict: true` TypeScript. No `any`. No `@ts-ignore`.
5. ESLint + Prettier clean, `npm run lint` and `npm run test` must pass.
6. Commit convention: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
   One commit = one logical change.
7. Tailwind only — no scattered custom CSS files. The single exception is the
   theme/token layer described in §3 and a small `@keyframes` block for the
   ambient effect.

**Before writing any code:** detect the Tailwind major version in
`frontend/package.json`. Tailwind v4 uses `@theme` inside the main CSS file;
Tailwind v3 uses `theme.extend` in `tailwind.config.js`. Use the one that
matches the repo — do not migrate versions in this pass.

---

## 2. Design direction

**Concept: "potager de nuit" — a night kitchen garden.**
The product turns a meat dish into its vegetal counterpart. The interface
should feel like a dark, warm kitchen at night: deep green shadow, one fresh
green light source, and one beetroot-pink accent that marks "the dish you came
in with". Editorial and calm, not a neon dashboard.

Deliberately avoided (these are the generic AI-dark-theme defaults): pure
`#000` backgrounds, a single acid-green-on-black accent, glassmorphism cards
everywhere, purple/blue gradient blobs, emoji as icons.

**One signature element, everything else quiet:** the hero headline word swap
(§6.1). Do not add a second attention-seeking effect.

---

## 3. Tokens

Define these once, as CSS custom properties, and expose them to Tailwind.
Never hardcode a hex value in a component.

### 3.1 Colour

| Token | Hex | Role |
|---|---|---|
| `--color-nuit` | `#08120E` | page background, deepest layer |
| `--color-potager` | `#0D1A14` | app background / large sections |
| `--color-feuille` | `#13251C` | card & panel surface |
| `--color-feuille-haut` | `#1A3325` | raised surface, inputs, hover surface |
| `--color-lisiere` | `#264533` | borders, hairlines, dividers |
| `--color-sauge` | `#93AB9B` | muted text, captions, placeholders |
| `--color-craie` | `#EAF2E6` | primary text |
| `--color-pousse` | `#A6D95B` | primary action, focus ring, active state |
| `--color-pousse-clair` | `#BCE578` | primary hover |
| `--color-pousse-sourd` | `#5C7A33` | disabled primary, subtle fills |
| `--color-betterave` | `#E4577E` | accent: marks the **source** (non-veg) recipe |
| `--color-brique` | `#C24A3E` | destructive only (admin delete) |

Rules:
- Text on `--color-pousse` buttons is `--color-nuit`, never white.
- `--color-betterave` appears at most twice per screen. It is semantic (it
  means "the dish you started from"), not decorative.
- Elevation is expressed by surface colour + a 1px `--color-lisiere` border,
  not by heavy box-shadows. Max shadow: `0 1px 2px rgb(0 0 0 / 0.4)`, plus one
  soft focus glow on the primary button.
- Verify every text/background pair reaches WCAG AA (4.5:1 body, 3:1 large).

### 3.2 Typography

Three roles, self-hosted via Fontsource if the package exists for that family,
otherwise a Google Fonts `<link>` in `index.html`. Load only the weights used.

| Role | Family | Usage |
|---|---|---|
| Display | **Fraunces** (variable, use `opsz` + a little `WONK`) | `h1`, `h2`, recipe titles, the hero swap. Nothing else. |
| UI / body | **Instrument Sans** (fallback: Public Sans) | all body text, labels, buttons, forms |
| Data | **JetBrains Mono** | similarity scores, ingredient counts, admin table numerics, uppercase eyebrow labels |

Scale (`rem`): 0.75 / 0.875 / 1 / 1.125 / 1.5 / 2 / 3 / 4.
Hero uses `clamp(2.25rem, 6vw, 4rem)`.
Body line-height 1.6; display line-height 1.05 with `-0.02em` tracking.
Eyebrow labels: mono, 0.75rem, uppercase, `0.12em` tracking, `--color-sauge`.

### 3.3 Space, radius, layout

- Spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 px.
- Radius: `--radius-sm: 6px`, `--radius-md: 10px`, `--radius-lg: 16px`,
  `--radius-pill: 999px`. No radius above 16px on cards.
- Content max width: 1100px. Prose max width: 68ch. Page gutter: 24px mobile,
  48px desktop.
- Results grid: 2×2 on ≥1024px, 2×1 on ≥640px, stacked below. **Keep the four
  cards as direct siblings of one grid container** so Phase 3 can add
  `framer-motion` `layout` animations without restructuring the DOM.

### 3.4 Motion

| Token | Value |
|---|---|
| `--dur-micro` | 120ms — hover, press, colour change |
| `--dur-base` | 220ms — enter/exit, route transition |
| `--dur-enter` | 420ms — card and section reveals |
| `--ease-out` | `cubic-bezier(0.22, 1, 0.36, 1)` |
| `--ease-inout` | `cubic-bezier(0.65, 0, 0.35, 1)` |
| stagger | 60ms between siblings |
| card spring | `{ type: "spring", stiffness: 260, damping: 30, mass: 0.8 }` |

Nothing animates longer than 700ms. Nothing loops except the hero word swap.

---

## 4. Dependencies

Use `framer-motion` (already in the stack table) for **all** animation. Do not
add anime.js, GSAP, or a second animation engine — `framer-motion` v12 already
covers this pass and its `layout` FLIP is what Phase 3 needs.

Allowed additions for this pass (add each to the `CLAUDE.md` stack table with
the justification given here):

| Package | Justification line for the table |
|---|---|
| `clsx` + `tailwind-merge` | conditional Tailwind class composition via a `cn()` helper; required by every component copied from shadcn-style registries |
| `class-variance-authority` | typed variant definitions for Button/Badge, keeps variant logic out of JSX |
| `lucide-react` | icon set (ISC licence), tree-shakeable, matches the copied components' conventions |
| Fontsource packages for the 3 families | self-hosted fonts, no third-party request at runtime |
| `@radix-ui/react-*` (only the primitives actually used) | accessible unstyled primitives behind the shadcn components used for admin dialogs/labels |

Ask before adding anything else. In particular: no UI kit installed as a
runtime dependency, no icon font, no CSS-in-JS.

### 4.1 Using external component registries

Components may be adapted from free sources (21st.dev, Magic UI, Aceternity,
React Bits, skiper-ui free tier, motion.dev examples). Rules:

1. **Copy the source into the repo** under `frontend/src/components/ui/`. Never
   add the registry as a dependency.
2. **Restyle it to the tokens in §3 before committing.** A pasted component
   that still carries its original palette, radii, or font is a bug.
3. Strip Next.js-isms (`next/link`, `next/image`, `"use client"`) — this is
   Vite + `react-router`.
4. Keep one file per component, typed props, no `any`.
5. Note the source URL in a one-line comment at the top of the file.

---

## 5. Component inventory

Create under `frontend/src/components/ui/` (primitives) and
`frontend/src/components/` (app components). If this adds a subfolder, update
the tree in `CLAUDE.md`.

**Primitives:** `Button` (variants: `primary`, `secondary`, `ghost`,
`destructive`; sizes `sm`/`md`/`lg`; `loading` state), `Input`, `Textarea`,
`Label`, `FieldError`, `Card`, `Badge`, `Spinner`, `Skeleton`, `Toast` (or a
minimal inline alert if no toast exists yet), `EmptyState`.

**App components:** `AppShell` (background + gutters), `Header`,
`RecipeSearchForm`, `RecipeCard`, `ResultsGrid`, `SourceRecipeSummary`,
`AnimatedTitle`, `Logo` (SVG, animatable paths), `AdminTable`, `RecipeForm`,
`ImageDropzone` (visual only — keep the existing upload logic).

Every component: `React.forwardRef` where it wraps a DOM element, explicit prop
types, `className` prop merged through `cn()`, no default export barrels.

---

## 6. Screen briefs

### 6.1 Public — search page

The **form is the hero**. No decorative illustration, no stock food photo.

Layout, top to bottom:
1. Eyebrow (mono, uppercase): `RECHERCHE DE SUBSTITUTION`
2. `h1` in Fraunces, two lines, with **the signature word swap**:
   `Votre <span>bœuf bourguignon</span>, en version végétarienne.`
   The highlighted noun cycles every 3.2s through a short French list
   (`bœuf bourguignon`, `poulet rôti`, `carbonara`, `chili con carne`,
   `blanquette de veau`). Old word leaves upward with `y: -14, opacity: 0,
   filter: blur(4px)`, new word enters from `y: 14`, `--dur-base`,
   `--ease-out`. The swapped word is `--color-betterave`; the rest of the
   headline is `--color-craie`. Width is animated so the line does not jump —
   use a `layout` transition on the span, not a fixed width.
3. One-sentence lede in `--color-sauge`, max 68ch.
4. The form: recipe title input + ingredients textarea + primary submit
   (`Trouver des recettes`). Inputs sit on `--color-feuille-haut` with a
   `--color-lisiere` border; focus moves the border to `--color-pousse` plus a
   2px outer ring at 25% opacity.
5. Ambient: one very soft radial gradient of `--color-pousse` at ~6% opacity
   behind the headline, plus an optional 2–3% noise overlay. Static, no
   parallax, no floating particles.

On mount: headline words reveal with a 60ms stagger (`y: 12 → 0`,
`opacity: 0 → 1`, `blur(6px) → 0`), then the lede, then the form. Total
sequence under 700ms.

### 6.2 Public — results

- The submitted dish is echoed at the top in a compact `SourceRecipeSummary`
  with a `--color-betterave` left rule and a mono eyebrow (`VOTRE RECETTE`).
  It is the only beetroot element on the screen.
- Results header: `4 alternatives végétariennes` (Fraunces).
- `ResultsGrid` → four `RecipeCard`s, entering with a 60ms stagger and the card
  spring. Card: title (Fraunces, 1.5rem), ingredient list preview in body font,
  similarity score in mono inside a `Badge` (e.g. `87 % de proximité`).
- Card hover: `y: -4`, border → `--color-pousse` at 40%, image/thumb block
  scales to 1.03 inside `overflow-hidden`. Micro duration. Keep the hover
  effect on a wrapper so Phase 3 can add sibling `layout` resizing later.
- Loading: four `Skeleton` cards in the same grid, matching the real card
  heights — no spinner-in-the-void, no layout shift when results arrive.
- Empty/error: `EmptyState` with a French message that says what happened and
  what to do next (e.g. `Aucune recette proche pour l'instant. Essayez avec
  moins d'ingrédients ou un titre plus courant.`). Errors do not apologise and
  are never vague.

### 6.3 Admin — login

- Centred card, max-width 380px, on the `--color-nuit` background with the
  same soft radial glow.
- `Logo`: an SVG mark you draw yourself (a simple leaf/fork or sprout
  monogram, stroke-based so it can animate). On mount: `pathLength` 0 → 1 over
  600ms `--ease-inout`, then the wordmark fades in at 200ms. No loop after
  that.
- Card enters `scale: 0.98 → 1`, `opacity: 0 → 1`, `--dur-enter`.
- Fields: `Identifiant`, `Mot de passe`. Submit: `Se connecter`.
- Failed login: the card shakes once (`x: [0, -6, 6, -3, 0]`, 240ms) and shows
  a `FieldError` in `--color-brique`. Do not clear the identifier field.
- Keep the existing session-cookie auth flow untouched.

### 6.4 Admin — recipe list & form

Utilitarian and dense; this is a tool, not a landing page. Boldness budget is
spent on the public pages.

- Top bar: wordmark, current section, `Se déconnecter` (ghost button).
- List: `AdminTable` with sticky header, zebra rows via
  `--color-feuille` / `--color-potager`, mono for numeric columns and dates,
  row hover raises to `--color-feuille-haut`. Row actions: `Modifier` (ghost),
  `Supprimer` (destructive). Delete asks for confirmation.
- No animation on table rows beyond a 120ms hover colour change, and a
  `--dur-base` fade-out on a deleted row.
- Recipe form: single column, max 640px, grouped fieldsets, French labels,
  inline validation messages under each field. CSV import keeps its own
  clearly-labelled section with visible progress and result counts.

### 6.5 Route transitions

Wrap the router outlet in `AnimatePresence`: exit `opacity: 0`, enter
`opacity: 0 → 1, y: 8 → 0`, `--dur-base`. No slide-across, no page curl.

---

## 7. Quality floor (non-negotiable)

- **Reduced motion:** honour `prefers-reduced-motion: reduce` globally. In that
  mode: no transforms, no blur transitions, no looping word swap (show the
  first word statically), opacity-only fades capped at 120ms. Implement it once
  via a `useReducedMotion` hook + a `MotionConfig`, not per component.
- **Keyboard:** every interactive element reachable and visibly focused
  (`focus-visible` ring in `--color-pousse`, 2px, 2px offset). Never
  `outline: none` without a replacement.
- **Semantics:** one `h1` per page, real `<button>`/`<label>`/`<form>`, inputs
  linked to labels by `id`, `aria-live="polite"` on the results region and on
  error messages, `alt` text in French on images.
- **Responsive:** works down to 360px, no horizontal scroll, tap targets ≥44px.
- **Performance:** no CLS when results load (skeletons reserve the space),
  animate only `transform`/`opacity`/`filter`, no animation on `width`/`height`
  except via `layout`.
- **Copy:** active voice, sentence case, plain verbs. Buttons name what
  happens (`Enregistrer la recette`, not `Valider`). The action keeps the same
  name through the flow. Empty states invite an action.

---

## 8. Tests

`vitest` + Testing Library, in `frontend/tests/`:
- `Button` renders each variant and the loading state, and is disabled while
  loading.
- `RecipeCard` renders title, score, and ingredients from props.
- `ResultsGrid` renders exactly the number of cards it is given, and renders
  the `EmptyState` for an empty array.
- `AnimatedTitle` renders the full text in a single accessible string (the
  per-word split must not break screen-reader reading order).
- One test asserting that the reduced-motion path renders without transform
  styles.

Assert on roles and accessible names, not on class names.

---

## 9. Definition of done

- [ ] Tokens defined in one place; zero hardcoded hex outside that file.
- [ ] The three font families load, are self-hosted where possible, and only
      the used weights are fetched.
- [ ] All four screens restyled; no default white background remains anywhere,
      including scrollbars and form autofill.
- [ ] Signature word swap works, and is static under reduced motion.
- [ ] `npm run lint`, `npm run test`, and `tsc --noEmit` all pass.
- [ ] `CLAUDE.md` stack table updated for every added package.
- [ ] `CLAUDE.md` repository structure updated if folders were added.
- [ ] A short entry added to `docs/ARCHITECTURE.md`: why tokens live where they
      do, and why `framer-motion` is the single animation engine.
- [ ] Every user-facing string is French; every identifier and comment English.
- [ ] Commits split: `chore:` deps → `feat:` tokens/theme → `feat:` primitives
      → `feat:` per screen → `test:` → `docs:`.

---

## 10. Working method

Do **not** start by writing components. Work in this order, and stop after
step 2 for approval:

1. Read `CLAUDE.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, and the current
   `frontend/src` tree. Report the Tailwind version, the existing pages, and
   anything in this brief that conflicts with what is already there.
2. Produce a short plan: the exact token file and its location, the component
   list with file paths, the dependency list with justification lines, and the
   commit sequence. **Wait for approval.**
3. Implement token layer + primitives, run lint/tests.
4. Implement screens one at a time, in the order 6.1 → 6.2 → 6.3 → 6.4.
5. Self-review against §7 and §9 before the final commit. List anything you
   could not do and why. Do not mark an item done that is not done.