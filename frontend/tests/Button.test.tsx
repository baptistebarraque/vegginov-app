import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "../src/components/ui/Button";

describe("Button", () => {
  it("renders every variant with its accessible name", () => {
    const variants = ["primary", "secondary", "ghost", "destructive"] as const;
    for (const variant of variants) {
      const { unmount } = render(<Button variant={variant}>Enregistrer</Button>);
      expect(screen.getByRole("button", { name: "Enregistrer" })).toBeInTheDocument();
      unmount();
    }
  });

  it("is disabled and marked busy while loading", () => {
    render(<Button loading>Enregistrer</Button>);
    const button = screen.getByRole("button", { name: "Enregistrer" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("is enabled when not loading", () => {
    render(<Button>Enregistrer</Button>);
    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeEnabled();
  });
});
