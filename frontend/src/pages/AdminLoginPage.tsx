import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { login } from "../api/auth";
import { AuthCard } from "../components/AuthCard";
import { Button } from "../components/ui/Button";
import { FieldError } from "../components/ui/FieldError";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";

function AdminLoginPage() {
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
      navigate("/admin");
    } catch (err) {
      if (err instanceof Error && err.message.includes("401")) {
        setError("Identifiants invalides.");
      } else {
        setError("Impossible de contacter le serveur. Vérifiez votre connexion.");
      }
      // The card shakes once on failure; the identifier is never cleared (§6.3).
      setShakeTrigger((current) => current + 1);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthCard title="Connexion admin" shakeTrigger={shakeTrigger}>
      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="admin-identifiant">Identifiant</Label>
          <Input
            id="admin-identifiant"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="admin-password">Mot de passe</Label>
          <Input
            id="admin-password"
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
    </AuthCard>
  );
}

export default AdminLoginPage;
