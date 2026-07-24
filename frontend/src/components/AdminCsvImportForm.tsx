import { useState, type FormEvent } from "react";

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
    <form onSubmit={handleSubmit} className="flex w-full max-w-md flex-col gap-3">
      <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
        Fichier CSV
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
        />
      </label>
      <button
        type="submit"
        disabled={isLoading || file === null}
        className="rounded bg-green-700 px-4 py-2 font-medium text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? "Import..." : "Importer le CSV"}
      </button>
    </form>
  );
}

export default AdminCsvImportForm;
