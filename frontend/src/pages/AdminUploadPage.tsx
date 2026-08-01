import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import {
  CsvImportValidationError,
  createRecipe,
  getProteinSourceOptions,
  importRecipesCsv,
} from "../api/adminRecipes";
import { getCurrentAdmin, logout } from "../api/auth";
import AdminCsvImportForm from "../components/AdminCsvImportForm";
import AdminRecipeForm from "../components/AdminRecipeForm";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Eyebrow } from "../components/ui/Eyebrow";
import type { AdminUser } from "../types/auth";
import type { CsvImportRowError, RecipeFormValues } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function AdminUploadPage() {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [proteinSourceOptions, setProteinSourceOptions] = useState<string[]>([]);
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

  useEffect(() => {
    if (admin === null) {
      return;
    }
    getProteinSourceOptions()
      .then(setProteinSourceOptions)
      .catch(() => setProteinSourceOptions([]));
  }, [admin]);

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
    <AppShell>
      <Header
        section="Ajouter"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-display text-3xl text-craie">Ajouter une recette</h1>
            <p className="mt-1 text-sm text-sauge">Connecté en tant que {admin.email}</p>
          </div>
          <Link
            to="/admin/recipes"
            className="text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Voir toutes les recettes
          </Link>
        </div>

        <div className="mt-8">
          <AdminRecipeForm
            onSubmit={handleSubmit}
            isLoading={isSubmitting}
            proteinSourceOptions={proteinSourceOptions}
          />
        </div>

        {error && (
          <Alert variant="error" className="mt-4 max-w-[640px]">
            {error}
          </Alert>
        )}
        {successMessage && (
          <div className="mt-4 flex max-w-[640px] flex-col gap-3">
            <Alert variant="success">{successMessage}</Alert>
            {createdImageUrl && (
              <img
                src={`${API_BASE_URL}${createdImageUrl}`}
                alt="Photo de la recette ajoutée"
                className="max-h-48 rounded-md border border-lisiere"
              />
            )}
          </div>
        )}

        <hr className="mt-12 max-w-[640px] border-lisiere" />

        <section className="mt-8 flex max-w-[640px] flex-col items-start gap-3">
          <Eyebrow>Import groupé</Eyebrow>
          <h2 className="font-display text-2xl text-craie">Importer plusieurs recettes (CSV)</h2>
          <p className="text-sm text-sauge">
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
            className="text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Télécharger un modèle CSV
          </a>

          <AdminCsvImportForm onSubmit={handleCsvImport} isLoading={isImporting} />

          {importSuccessMessage && (
            <Alert variant="success" className="w-full">
              {importSuccessMessage}
            </Alert>
          )}
          {importError && (
            <Alert variant="error" className="w-full">
              <p>{importError}</p>
              {importRowErrors.length > 0 && (
                <ul className="mt-1 list-disc pl-5">
                  {importRowErrors.map((rowError) => (
                    <li key={rowError.row}>
                      Ligne {rowError.row} : {rowError.message}
                    </li>
                  ))}
                </ul>
              )}
            </Alert>
          )}
        </section>
      </main>
    </AppShell>
  );
}

export default AdminUploadPage;
