import { motion, useAnimationControls, useReducedMotion } from "framer-motion";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { login } from "../api/auth";
import { Logo } from "../components/Logo";
import { Button } from "../components/ui/Button";
import { FieldError } from "../components/ui/FieldError";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";
import { DURATION } from "../utils/motion";

function AdminLoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const shake = useAnimationControls();
  const reduce = useReducedMotion();

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
      if (!reduce) {
        shake.start({ x: [0, -6, 6, -3, 0], transition: { duration: 0.24 } });
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-nuit px-6">
      <Link
        to="/"
        className="absolute top-5 left-5 rounded-md px-3 py-2 text-sm text-sauge transition-colors hover:bg-feuille-haut hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
      >
        Retour à l'accueil
      </Link>

      {/* Same soft radial glow as the public hero (§6.3). */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-1/2 h-[480px] w-[560px] max-w-full -translate-x-1/2 -translate-y-1/2"
        style={{
          background:
            "radial-gradient(circle at center, color-mix(in oklab, var(--color-pousse) 7%, transparent) 0%, transparent 68%)",
        }}
      />

      <motion.div
        initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.98 }}
        animate={reduce ? { opacity: 1 } : { opacity: 1, scale: 1 }}
        transition={{ duration: reduce ? 0.12 : DURATION.enter }}
        className="relative z-10 w-full max-w-[380px]"
      >
        <motion.div
          animate={shake}
          className="rounded-lg border border-lisiere bg-feuille p-8 shadow-[0_1px_2px_rgb(0_0_0/0.4)]"
        >
          <div className="flex flex-col items-center gap-3">
            <Logo size={44} animate />
            <motion.span
              initial={reduce ? { opacity: 1 } : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: reduce ? 0 : 0.7, duration: 0.2 }}
              className="font-display text-2xl text-craie"
            >
              Vegginov
            </motion.span>
          </div>

          <h1 className="mt-6 text-center font-display text-xl text-craie">Connexion admin</h1>

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
        </motion.div>
      </motion.div>
    </div>
  );
}

export default AdminLoginPage;
