import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { deleteAccount, describeAuthError, logout, updateAccount } from "../api/auth";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { FieldError } from "../components/ui/FieldError";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";
import { useSession } from "../hooks/useSession";

function AccountPage() {
  const { user, isChecking } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccessMessage(null);
    try {
      const updates: { currentPassword: string; email?: string; password?: string } = {
        currentPassword,
      };
      if (email.trim() !== "") {
        updates.email = email.trim();
      }
      if (password !== "") {
        updates.password = password;
      }
      await updateAccount(updates);
      setEmail("");
      setPassword("");
      setCurrentPassword("");
      setSaveSuccessMessage("Compte mis à jour.");
    } catch (err) {
      setSaveError(describeAuthError(err, "Impossible de mettre à jour le compte."));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteAccount();
      navigate("/");
    } catch {
      setDeleteError("Impossible de supprimer le compte.");
      setIsDeleting(false);
      setIsConfirmOpen(false);
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
        section="Mon compte"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <h1 className="font-display text-3xl text-craie">Mon compte</h1>
        <p className="mt-1 text-sm text-sauge">Connecté en tant que {user.email}</p>
        <div className="mt-2 flex flex-col gap-1">
          <Link
            to="/preferences"
            className="inline-block text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Modifier mes préférences →
          </Link>
          <Link
            to="/watchlist"
            className="inline-block text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Voir ma liste →
          </Link>
          <Link
            to="/likes"
            className="inline-block text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Voir mes coups de cœur →
          </Link>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 flex max-w-[420px] flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="account-email">Nouvel email</Label>
            <Input
              id="account-email"
              type="email"
              autoComplete="username"
              placeholder={user.email}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="account-password">Nouveau mot de passe</Label>
            <Input
              id="account-password"
              type="password"
              autoComplete="new-password"
              placeholder="Laisser vide pour ne pas changer"
              minLength={10}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="account-current-password">Mot de passe actuel</Label>
            <Input
              id="account-current-password"
              type="password"
              autoComplete="current-password"
              placeholder="Requis pour toute modification"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              required
            />
          </div>

          <FieldError>{saveError}</FieldError>
          {saveSuccessMessage && <Alert variant="success">{saveSuccessMessage}</Alert>}

          <Button type="submit" loading={isSaving} className="mt-1 w-full">
            {isSaving ? "Enregistrement…" : "Enregistrer"}
          </Button>
        </form>

        <hr className="mt-12 max-w-[420px] border-lisiere" />

        <div className="mt-8 flex max-w-[420px] flex-col items-start gap-3">
          <ConfirmDialog
            open={isConfirmOpen}
            onOpenChange={setIsConfirmOpen}
            trigger={
              <Button variant="destructive" loading={isDeleting}>
                Supprimer le compte
              </Button>
            }
            title="Supprimer le compte ?"
            description="Votre compte et toutes les données associées (préférences, liste, coups de cœur) seront définitivement supprimés. Cette action est irréversible."
            confirmLabel="Supprimer"
            loading={isDeleting}
            onConfirm={handleDelete}
          />
          {deleteError && (
            <Alert variant="error" className="w-full">
              {deleteError}
            </Alert>
          )}
        </div>
      </main>
    </AppShell>
  );
}

export default AccountPage;
