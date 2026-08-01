import { useState } from "react";
import { Link } from "react-router";
import { cn } from "../utils/cn";
import { ConfirmDialog } from "./ConfirmDialog";
import { Button } from "./ui/Button";
import type { RecipeListItem } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface AdminTableProps {
  recipes: RecipeListItem[];
  onDelete: (id: number) => Promise<void>;
  deletingId: number | null;
}

// Utilitarian, dense recipe table (docs/FRONTEND.md §6.4): sticky header, zebra
// rows, a 120ms hover colour change, Modifier (ghost link) + Supprimer
// (destructive, confirmed via dialog) per row.
function AdminTable({ recipes, onDelete, deletingId }: AdminTableProps) {
  const [pendingDelete, setPendingDelete] = useState<RecipeListItem | null>(null);

  return (
    <div className="w-full overflow-x-auto rounded-lg border border-lisiere">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="sticky top-0 bg-feuille-haut">
            <th className="px-4 py-3 font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Recette
            </th>
            <th className="px-4 py-3 text-right font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {recipes.map((recipe, index) => (
            <tr
              key={recipe.id}
              className={cn(
                "border-t border-lisiere transition-colors duration-[var(--dur-micro)] hover:bg-feuille-haut",
                index % 2 === 1 ? "bg-potager" : "bg-feuille",
              )}
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  {recipe.image_url && (
                    <img
                      src={`${API_BASE_URL}${recipe.image_url}`}
                      alt=""
                      className="size-10 rounded-md border border-lisiere object-cover"
                    />
                  )}
                  <span className="text-craie">{recipe.title}</span>
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-2">
                  <Link
                    to={`/admin/recipes/${recipe.id}`}
                    className="inline-flex h-8 items-center rounded-md px-3 text-sm text-sauge transition-colors hover:bg-feuille hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
                  >
                    Modifier
                  </Link>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setPendingDelete(recipe)}
                    loading={deletingId === recipe.id}
                  >
                    Supprimer
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open) {
            setPendingDelete(null);
          }
        }}
        title="Supprimer la recette ?"
        description={
          pendingDelete
            ? `« ${pendingDelete.title} » sera définitivement supprimée. Cette action est irréversible.`
            : undefined
        }
        confirmLabel="Supprimer"
        loading={deletingId !== null}
        onConfirm={async () => {
          if (pendingDelete) {
            await onDelete(pendingDelete.id);
            setPendingDelete(null);
          }
        }}
      />
    </div>
  );
}

export { AdminTable };
