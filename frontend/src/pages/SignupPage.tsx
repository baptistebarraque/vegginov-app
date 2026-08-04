import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { signup } from "../api/auth";
import { AuthCard } from "../components/AuthCard";
import { Button } from "../components/ui/Button";
import { FieldError } from "../components/ui/FieldError";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";

function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [shakeTrigger, setShakeTrigger] = useState(0);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      setShakeTrigger((current) => current + 1);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await signup(email, password);
      navigate("/onboarding");
    } catch (err) {
      if (err instanceof Error && err.message.includes("409")) {
        setError("Cet email est déjà utilisé.");
      } else {
        setError("Impossible de créer le compte. Vérifiez votre connexion.");
      }
      setShakeTrigger((current) => current + 1);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthCard title="Créer un compte" shakeTrigger={shakeTrigger}>
      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="signup-email">Email</Label>
          <Input
            id="signup-email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="signup-password">Mot de passe</Label>
          <Input
            id="signup-password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="signup-confirm-password">Confirmer le mot de passe</Label>
          <Input
            id="signup-confirm-password"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />
        </div>

        <FieldError>{error}</FieldError>

        <Button type="submit" loading={isLoading} className="mt-1 w-full">
          {isLoading ? "Création…" : "Créer le compte"}
        </Button>
      </form>

      <div className="mt-5 flex justify-center text-sm text-sauge">
        <span>
          Déjà un compte ?{" "}
          <Link
            to="/login"
            className="text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Se connecter
          </Link>
        </span>
      </div>
    </AuthCard>
  );
}

export default SignupPage;
