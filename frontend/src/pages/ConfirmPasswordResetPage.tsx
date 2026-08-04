import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { confirmPasswordReset } from "../api/auth";
import { AuthCard } from "../components/AuthCard";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { FieldError } from "../components/ui/FieldError";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";

function ConfirmPasswordResetPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [shakeTrigger, setShakeTrigger] = useState(0);
  const [isDone, setIsDone] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      setShakeTrigger((current) => current + 1);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await confirmPasswordReset(token, newPassword);
      setIsDone(true);
    } catch (err) {
      if (err instanceof Error && err.message.includes("400")) {
        setError("Lien de réinitialisation invalide ou expiré.");
      } else {
        setError("Impossible de contacter le serveur. Vérifiez votre connexion.");
      }
      setShakeTrigger((current) => current + 1);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthCard title="Nouveau mot de passe" shakeTrigger={shakeTrigger}>
      {isDone ? (
        <>
          <Alert variant="success" className="mt-6">
            Mot de passe mis à jour. Vous pouvez vous connecter.
          </Alert>
          <Button className="mt-4 w-full" onClick={() => navigate("/login")}>
            Se connecter
          </Button>
        </>
      ) : !token ? (
        <Alert variant="error" className="mt-6">
          Lien invalide : aucun jeton de réinitialisation fourni.
        </Alert>
      ) : (
        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="new-password">Nouveau mot de passe</Label>
            <Input
              id="new-password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="confirm-new-password">Confirmer le mot de passe</Label>
            <Input
              id="confirm-new-password"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
            />
          </div>

          <FieldError>{error}</FieldError>

          <Button type="submit" loading={isLoading} className="mt-1 w-full">
            {isLoading ? "Mise à jour…" : "Mettre à jour le mot de passe"}
          </Button>
        </form>
      )}

      <div className="mt-5 flex justify-center text-sm text-sauge">
        <Link
          to="/login"
          className="transition-colors hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
        >
          Retour à la connexion
        </Link>
      </div>
    </AuthCard>
  );
}

export default ConfirmPasswordResetPage;
