import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { CsvImportValidationError, createRecipe, importRecipesCsv } from "../api/adminRecipes";
import { getCurrentAdmin, logout } from "../api/auth";
import AdminCsvImportForm from "../components/AdminCsvImportForm";
import AdminRecipeForm from "../components/AdminRecipeForm";
import type { AdminUser } from "../types/auth";
import type { CsvImportRowError, RecipeFormValues } from "../types/recipe";

function AdminUploadPage() {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [createdImageUrl, setCreatedImageUrl] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importRowErrors, setImportRowErrors] = useState<CsvImportRowError[]>([]);
  const [importSuccessMessage, setImportSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getCurrentAdmin().then((current) => {
      if (current === null) {
        navigate("/admin/login");
      } else {
        setAdmin(current);
        setIsCheckingSession(false);
      }
    });
  }, [navigate]);

  async function handleSubmit(values: RecipeFormValues) {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    setCreatedImageUrl(null);
    try {
      const recipe = await createRecipe(values);
      setSuccessMessage(`Recette ajoutée : ${recipe.title}`);
      setCreatedImageUrl(recipe.image_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'ajouter la recette.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCsvImport(file: File) {
    setIsImporting(true);
    setImportError(null);
    setImportRowErrors([]);
    setImportSuccessMessage(null);
    try {
      const result = await importRecipesCsv(file);
      setImportSuccessMessage(`${result.created_count} recette(s) importée(s) avec succès.`);
    } catch (err) {
      if (err instanceof CsvImportValidationError) {
        setImportError("Le fichier contient des erreurs, rien n'a été importé :");
        setImportRowErrors(err.rowErrors);
      } else {
        setImportError("Impossible d'importer le fichier CSV.");
      }
    } finally {
      setIsImporting(false);
    }
  }

  async function handleLogout() {
    await logout();
    navigate("/admin/login");
  }

  if (isCheckingSession || admin === null) {
    return null;
  }

  return (
    <main className="flex min-h-screen flex-col items-center gap-6 bg-white px-4 py-12 dark:bg-neutral-900">
      <div className="flex w-full max-w-md items-center justify-between">
        <h1 className="text-3xl font-semibold text-green-800 dark:text-green-400">
          Ajouter une recette
        </h1>
        <button
          type="button"
          onClick={handleLogout}
          className="text-sm text-neutral-500 underline hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
        >
          Déconnexion
        </button>
      </div>
      <p className="text-neutral-600 dark:text-neutral-300">Connecté en tant que {admin.email}</p>
      <Link
        to="/admin/recipes"
        className="self-start text-sm text-green-700 underline hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
      >
        Voir toutes les recettes
      </Link>

      <AdminRecipeForm onSubmit={handleSubmit} isLoading={isSubmitting} />

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {successMessage && (
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm text-green-700 dark:text-green-400">{successMessage}</p>
          {createdImageUrl && (
            <img
              src={`${import.meta.env.VITE_API_BASE_URL}${createdImageUrl}`}
              alt="Photo de la recette ajoutée"
              className="max-h-48 rounded shadow"
            />
          )}
        </div>
      )}

      <hr className="w-full max-w-md border-neutral-300 dark:border-neutral-700" />

      <div className="flex w-full max-w-md flex-col items-start gap-3">
        <h2 className="text-xl font-semibold text-green-800 dark:text-green-400">
          Importer plusieurs recettes (CSV)
        </h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">
          Colonnes : <code>title</code>, <code>ingredients</code> (obligatoires),{" "}
          <code>allergens</code>, <code>prep_time_minutes</code>, <code>servings</code>,{" "}
          <code>protein_source</code>, <code>protein_grams</code>, <code>instructions</code>{" "}
          (optionnelles). Dans une cellule, séparez plusieurs valeurs par un point-virgule (
          <code>;</code>). Pour les ingrédients, ajoutez la quantité après deux-points, ex.{" "}
          <code>riz:200g; curry</code> — obligatoire si <code>servings</code> est renseigné.
        </p>
        <a
          href="/recipe-import-template.csv"
          download
          className="text-sm text-green-700 underline hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
        >
          Télécharger un modèle CSV
        </a>

        <AdminCsvImportForm onSubmit={handleCsvImport} isLoading={isImporting} />

        {importSuccessMessage && (
          <p className="text-sm text-green-700 dark:text-green-400">{importSuccessMessage}</p>
        )}
        {importError && (
          <div className="flex flex-col gap-1">
            <p className="text-sm text-red-600 dark:text-red-400">{importError}</p>
            {importRowErrors.length > 0 && (
              <ul className="list-disc pl-5 text-sm text-red-600 dark:text-red-400">
                {importRowErrors.map((rowError) => (
                  <li key={rowError.row}>
                    Ligne {rowError.row} : {rowError.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

export default AdminUploadPage;
