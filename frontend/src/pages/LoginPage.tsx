import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { login } from "../api/auth";
import { AuthCard } from "../components/AuthCard";
import { Button } from "../components/ui/Button";
import { FieldError } from "../components/ui/FieldError";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [shakeTrigger, setShakeTrigger] = useState(0);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      if (err instanceof Error && err.message.includes("401")) {
        setError("Identifiants invalides.");
      } else {
        setError("Impossible de contacter le serveur. Vérifiez votre connexion.");
      }
      setShakeTrigger((current) => current + 1);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthCard title="Connexion" shakeTrigger={shakeTrigger}>
      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="login-email">Email</Label>
          <Input
            id="login-email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="login-password">Mot de passe</Label>
          <Input
            id="login-password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>

        <FieldError>{error}</FieldError>

        <Button type="submit" loading={isLoading} className="mt-1 w-full">
          {isLoading ? "Connexion…" : "Se connecter"}
        </Button>
      </form>

      <div className="mt-5 flex flex-col items-center gap-2 text-sm text-sauge">
        <Link
          to="/reset-password"
          className="transition-colors hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
        >
          Mot de passe oublié ?
        </Link>
        <span>
          Pas encore de compte ?{" "}
          <Link
            to="/signup"
            className="text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Créer un compte
          </Link>
        </span>
      </div>
    </AuthCard>
  );
}

export default LoginPage;
