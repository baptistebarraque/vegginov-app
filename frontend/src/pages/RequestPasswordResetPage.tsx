import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { requestPasswordReset } from "../api/auth";
import { AuthCard } from "../components/AuthCard";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { FieldError } from "../components/ui/FieldError";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";

function RequestPasswordResetPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  // The reset link is delivered out of band, never in the response — so the
  // page shows the same message whether or not the account exists.
  const [isSubmitted, setIsSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await requestPasswordReset(email);
      setIsSubmitted(true);
    } catch {
      setError("Impossible de contacter le serveur. Vérifiez votre connexion.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthCard title="Mot de passe oublié">
      {isSubmitted ? (
        <Alert variant="success" className="mt-6">
          <p>
            Si un compte existe pour cet email, un lien de réinitialisation vous sera envoyé. Il
            reste valable une heure.
          </p>
        </Alert>
      ) : (
        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reset-email">Email</Label>
            <Input
              id="reset-email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <FieldError>{error}</FieldError>

          <Button type="submit" loading={isLoading} className="mt-1 w-full">
            {isLoading ? "Envoi…" : "Réinitialiser le mot de passe"}
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

export default RequestPasswordResetPage;
