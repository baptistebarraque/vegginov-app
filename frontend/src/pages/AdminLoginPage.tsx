import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { login } from "../api/auth";

function AdminLoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
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
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen flex-col items-center gap-6 bg-white px-4 py-12 dark:bg-neutral-900">
      <Link
        to="/"
        className="absolute top-4 left-4 text-sm text-neutral-500 underline hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
      >
        Retour à l'accueil
      </Link>

      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-semibold text-green-800 dark:text-green-400">
          Connexion admin
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="flex w-full max-w-md flex-col gap-3">
        <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
          />
        </label>
        <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
          Mot de passe
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
          />
        </label>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={isLoading}
          className="rounded bg-green-700 px-4 py-2 font-medium text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </main>
  );
}

export default AdminLoginPage;
