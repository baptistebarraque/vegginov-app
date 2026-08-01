import { useState, type FormEvent } from "react";
import { Button } from "./ui/Button";

interface AdminCsvImportFormProps {
  onSubmit: (file: File) => void;
  isLoading: boolean;
}

function AdminCsvImportForm({ onSubmit, isLoading }: AdminCsvImportFormProps) {
  const [file, setFile] = useState<File | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (file !== null) {
      onSubmit(file);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-[640px] flex-col gap-3">
      <label className="flex flex-col gap-1 text-left text-sm font-medium text-craie">
        Fichier CSV
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="rounded-md border border-lisiere bg-feuille-haut px-3 py-2 text-craie focus:border-pousse focus:ring-2 focus:ring-pousse/25 focus:outline-none"
        />
      </label>
      <Button type="submit" variant="secondary" loading={isLoading} disabled={file === null} className="self-start">
        {isLoading ? "Import…" : "Importer le CSV"}
      </Button>
    </form>
  );
}

export default AdminCsvImportForm;
