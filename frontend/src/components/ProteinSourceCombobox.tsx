import { useId, useState } from "react";
import { inputClassName, labelClassName } from "./AdminRecipeForm";

interface ProteinSourceComboboxProps {
  value: string | null;
  onChange: (value: string | null) => void;
  options: string[];
}

// Accent-insensitive filtering: the vocabulary is French (e.g. "crème"), and
// typing without accents should still find a match.
function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

// protein_source is constrained to a fixed vocabulary (see
// matching/substitution.py's RECIPE_PROTEIN_VOCABULARY) so the backend's
// exact-match substitution lookup always finds it — this filters the list
// as the admin types, but only ever commits one of `options`, never raw text.
function ProteinSourceCombobox({ value, onChange, options }: ProteinSourceComboboxProps) {
  const [query, setQuery] = useState(value ?? "");
  const [isOpen, setIsOpen] = useState(false);
  const listboxId = useId();

  const filteredOptions =
    query.trim() === ""
      ? options
      : options.filter((option) => normalize(option).includes(normalize(query)));

  function commit(text: string) {
    const trimmed = text.trim();
    if (trimmed === "") {
      onChange(null);
      setQuery("");
    } else if (options.includes(trimmed)) {
      onChange(trimmed);
      setQuery(trimmed);
    } else {
      // Not one of the known values: discard the typed text, revert to the
      // last committed value rather than submitting something the backend
      // would reject anyway.
      setQuery(value ?? "");
    }
    setIsOpen(false);
  }

  function selectOption(option: string) {
    onChange(option);
    setQuery(option);
    setIsOpen(false);
  }

  return (
    <label className={labelClassName}>
      Source de protéines (optionnel)
      <div className="relative">
        <input
          type="text"
          role="combobox"
          aria-expanded={isOpen}
          aria-controls={listboxId}
          aria-autocomplete="list"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => commit(query)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              if (filteredOptions.length > 0) {
                selectOption(filteredOptions[0]);
              } else {
                commit(query);
              }
            } else if (event.key === "Escape") {
              setQuery(value ?? "");
              setIsOpen(false);
            }
          }}
          placeholder="tofu, seitan, lentilles..."
          className={`${inputClassName} w-full`}
        />
        {isOpen && filteredOptions.length > 0 && (
          <ul
            id={listboxId}
            role="listbox"
            className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-md border border-lisiere bg-feuille-haut shadow-[0_1px_2px_rgb(0_0_0/0.4)]"
          >
            {filteredOptions.map((option) => (
              <li
                key={option}
                role="option"
                aria-selected={option === value}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => selectOption(option)}
                className="cursor-pointer px-3 py-2 text-sm text-craie hover:bg-feuille aria-selected:text-pousse"
              >
                {option}
              </li>
            ))}
          </ul>
        )}
      </div>
    </label>
  );
}

export default ProteinSourceCombobox;
