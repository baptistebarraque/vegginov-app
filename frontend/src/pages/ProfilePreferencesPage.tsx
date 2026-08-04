import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { getPreferences, updatePreferences } from "../api/preferences";
import { logout } from "../api/auth";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import PreferenceForm from "../components/PreferenceForm";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";
import { useSession } from "../hooks/useSession";
import type { Preferences } from "../types/preference";

function ProfilePreferencesPage() {
  const { user, isChecking } = useSession();
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (user === null) {
      return;
    }
    getPreferences()
      .then(setPreferences)
      .catch(() => setLoadError("Impossible de charger vos préférences."));
  }, [user]);

  async function handleSubmit(values: Preferences) {
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccessMessage(null);
    try {
      const updated = await updatePreferences(values);
      setPreferences(updated);
      setSaveSuccessMessage("Préférences enregistrées.");
    } catch {
      setSaveError("Impossible d'enregistrer vos préférences.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  if (isChecking || user === null) {
    return null;
  }

  return (
    <AppShell>
      <Header
        section="Préférences"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-3xl text-craie">Mes préférences</h1>
          <Link
            to="/account"
            className="text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            ← Mon compte
          </Link>
        </div>
        <p className="mt-1 text-sm text-sauge">
          Appliquées par défaut à vos recherches de suggestions — un allergène déclaré exclut les
          recettes qui le contiennent.
        </p>

        {loadError ? (
          <Alert variant="error" className="mt-8 max-w-[420px]">
            {loadError}
          </Alert>
        ) : preferences === null ? (
          <div className="mt-8 flex max-w-[420px] flex-col gap-4">
            {[0, 1, 2, 3].map((slot) => (
              <Skeleton key={slot} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <div className="mt-8 max-w-[420px]">
            <PreferenceForm initialValues={preferences} onSubmit={handleSubmit} isLoading={isSaving} />

            {saveError && (
              <Alert variant="error" className="mt-4">
                {saveError}
              </Alert>
            )}
            {saveSuccessMessage && (
              <Alert variant="success" className="mt-4">
                {saveSuccessMessage}
              </Alert>
            )}
          </div>
        )}
      </main>
    </AppShell>
  );
}

export default ProfilePreferencesPage;
