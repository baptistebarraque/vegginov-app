import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import ProteinSourceCombobox from "../src/components/ProteinSourceCombobox";

const OPTIONS = ["tofu", "seitan", "crème fraîche"];

describe("ProteinSourceCombobox", () => {
  it("shows the current value in the input", () => {
    render(<ProteinSourceCombobox value="tofu" onChange={vi.fn()} options={OPTIONS} />);

    expect(screen.getByRole("combobox")).toHaveValue("tofu");
  });

  it("filters options as the admin types, accent-insensitively", async () => {
    const user = userEvent.setup();
    render(<ProteinSourceCombobox value={null} onChange={vi.fn()} options={OPTIONS} />);

    await user.type(screen.getByRole("combobox"), "creme");

    expect(screen.getByRole("option", { name: "crème fraîche" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "tofu" })).not.toBeInTheDocument();
  });

  it("commits a value when an option is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ProteinSourceCombobox value={null} onChange={onChange} options={OPTIONS} />);

    await user.type(screen.getByRole("combobox"), "sei");
    await user.click(screen.getByRole("option", { name: "seitan" }));

    expect(onChange).toHaveBeenCalledWith("seitan");
    expect(screen.getByRole("combobox")).toHaveValue("seitan");
  });

  it("selects the first filtered option on Enter", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ProteinSourceCombobox value={null} onChange={onChange} options={OPTIONS} />);

    await user.type(screen.getByRole("combobox"), "tofu{enter}");

    expect(onChange).toHaveBeenCalledWith("tofu");
  });

  it("discards unknown typed text on blur, reverting to the last committed value", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ProteinSourceCombobox value="tofu" onChange={onChange} options={OPTIONS} />);

    await user.clear(screen.getByRole("combobox"));
    await user.type(screen.getByRole("combobox"), "steak haché");
    await user.tab();

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByRole("combobox")).toHaveValue("tofu");
  });

  it("commits null when the field is cleared and left blank", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ProteinSourceCombobox value="tofu" onChange={onChange} options={OPTIONS} />);

    await user.clear(screen.getByRole("combobox"));
    await user.tab();

    expect(onChange).toHaveBeenCalledWith(null);
  });
});
