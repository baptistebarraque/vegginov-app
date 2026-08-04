import { Bookmark } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { logout } from "../api/auth";
import { getWatchlist, removeFromWatchlist, updateWatchlistEntry } from "../api/watchlist";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";
import { Skeleton } from "../components/ui/Skeleton";
import { Textarea } from "../components/ui/Textarea";
import { useSession } from "../hooks/useSession";
import type { WatchlistEntry } from "../types/watchlist";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface WatchlistRowProps {
  entry: WatchlistEntry;
  onSave: (notes: string | null, plannedFor: string | null) => Promise<void>;
  onRemove: () => Promise<void>;
}

function WatchlistRow({ entry, onSave, onRemove }: WatchlistRowProps) {
  const [notes, setNotes] = useState(entry.notes ?? "");
  const [plannedFor, setPlannedFor] = useState(entry.plannedFor ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [savedMessage, setSavedMessage] = useState(false);

  async function handleSave() {
    setIsSaving(true);
    setSavedMessage(false);
    try {
      await onSave(notes.trim() === "" ? null : notes.trim(), plannedFor === "" ? null : plannedFor);
      setSavedMessage(true);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRemove() {
    setIsRemoving(true);
    try {
      await onRemove();
    } catch {
      setIsRemoving(false);
    }
  }

  return (
    <div className="flex gap-4 rounded-lg border border-lisiere bg-feuille p-4">
      {entry.imageUrl && (
        <img
          src={`${API_BASE_URL}${entry.imageUrl}`}
          alt={entry.title}
          className="h-20 w-20 shrink-0 rounded-md object-contain"
        />
      )}
      <div className="flex flex-1 flex-col gap-2">
        <h3 className="font-display text-lg text-craie">{entry.title}</h3>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`notes-${entry.recipeId}`}>Notes</Label>
          <Textarea
            id={`notes-${entry.recipeId}`}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={2}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`planned-for-${entry.recipeId}`}>Prévue pour</Label>
          <Input
            id={`planned-for-${entry.recipeId}`}
            type="date"
            value={plannedFor}
            onChange={(event) => setPlannedFor(event.target.value)}
            className="w-fit"
          />
        </div>
        <div className="mt-1 flex items-center gap-2">
          <Button size="sm" variant="secondary" loading={isSaving} onClick={handleSave}>
            Enregistrer
          </Button>
          <Button size="sm" variant="ghost" loading={isRemoving} onClick={handleRemove}>
            Retirer de ma liste
          </Button>
          {savedMessage && <span className="text-sm text-pousse">Enregistré</span>}
        </div>
      </div>
    </div>
  );
}

function WatchlistPage() {
  const { user, isChecking } = useSession();
  const [entries, setEntries] = useState<WatchlistEntry[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (user === null) {
      return;
    }
    getWatchlist()
      .then(setEntries)
      .catch(() => setLoadError("Impossible de charger votre liste."));
  }, [user]);

  async function handleSave(recipeId: number, notes: string | null, plannedFor: string | null) {
    const updated = await updateWatchlistEntry(recipeId, { notes, plannedFor });
    setEntries((current) =>
      (current ?? []).map((entry) => (entry.recipeId === recipeId ? updated : entry)),
    );
  }

  async function handleRemove(recipeId: number) {
    await removeFromWatchlist(recipeId);
    setEntries((current) => (current ?? []).filter((entry) => entry.recipeId !== recipeId));
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
        section="Ma liste"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <h1 className="font-display text-3xl text-craie">Ma liste</h1>
        <p className="mt-1 text-sm text-sauge">Les recettes que vous avez sauvegardées pour plus tard.</p>

        <div className="mt-8 flex max-w-[560px] flex-col gap-4">
          {loadError ? (
            <Alert variant="error">{loadError}</Alert>
          ) : entries === null ? (
            [0, 1, 2].map((slot) => <Skeleton key={slot} className="h-32 w-full" />)
          ) : entries.length === 0 ? (
            <EmptyState
              icon={Bookmark}
              title="Votre liste est vide"
              description="Enregistrez une recette depuis la page d'accueil pour la retrouver ici."
            />
          ) : (
            entries.map((entry) => (
              <WatchlistRow
                key={entry.recipeId}
                entry={entry}
                onSave={(notes, plannedFor) => handleSave(entry.recipeId, notes, plannedFor)}
                onRemove={() => handleRemove(entry.recipeId)}
              />
            ))
          )}
        </div>
      </main>
    </AppShell>
  );
}

export default WatchlistPage;
