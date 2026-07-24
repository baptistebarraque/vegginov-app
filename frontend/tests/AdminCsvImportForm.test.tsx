import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AdminCsvImportForm from "../src/components/AdminCsvImportForm";

describe("AdminCsvImportForm", () => {
  it("submits the selected CSV file", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AdminCsvImportForm onSubmit={onSubmit} isLoading={false} />);
    const file = new File(["title,ingredients\nSalade,laitue\n"], "recipes.csv", {
      type: "text/csv",
    });

    await user.upload(screen.getByLabelText(/fichier csv/i), file);
    await user.click(screen.getByRole("button", { name: /importer le csv/i }));

    expect(onSubmit).toHaveBeenCalledWith(file);
  });

  it("disables the submit button until a file is selected", () => {
    render(<AdminCsvImportForm onSubmit={vi.fn()} isLoading={false} />);
    expect(screen.getByRole("button", { name: /importer le csv/i })).toBeDisabled();
  });

  it("disables the submit button while loading", () => {
    render(<AdminCsvImportForm onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
