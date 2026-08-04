import { useState } from "react";
import { useNavigate } from "react-router";
import { updatePreferences } from "../api/preferences";
import { AuthCard } from "../components/AuthCard";
import PreferenceForm from "../components/PreferenceForm";
import { Alert } from "../components/ui/Alert";
import { useSession } from "../hooks/useSession";
import type { Preferences } from "../types/preference";

// Shown once right after signup (redirect target of SignupPage), skippable —
// accounts and their preferences are both optional (docs/ROADMAP.md Phase 4).
function OnboardingPage() {
  const { isChecking } = useSession();
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleSubmit(values: Preferences) {
    setIsSaving(true);
    setError(null);
    try {
      await updatePreferences(values);
      navigate("/");
    } catch {
      setError("Impossible d'enregistrer vos préférences pour le moment.");
    } finally {
      setIsSaving(false);
    }
  }

  if (isChecking) {
    return null;
  }

  return (
    <AuthCard title="Vos préférences">
      <p className="mt-2 text-center text-sm text-sauge">
        Facultatif — elles filtrent les recettes qui contiennent un de vos allergènes. Vous
        pourrez les modifier à tout moment depuis votre compte.
      </p>

      <div className="mt-6">
        <PreferenceForm
          onSubmit={handleSubmit}
          isLoading={isSaving}
          submitLabel="Enregistrer et continuer"
        />
      </div>

      {error && (
        <Alert variant="error" className="mt-4">
          {error}
        </Alert>
      )}

      <div className="mt-5 flex justify-center text-sm text-sauge">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="rounded-sm transition-colors hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
        >
          Passer cette étape
        </button>
      </div>
    </AuthCard>
  );
}

export default OnboardingPage;
