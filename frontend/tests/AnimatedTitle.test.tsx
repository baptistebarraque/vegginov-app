import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AnimatedTitle } from "../src/components/AnimatedTitle";

const WORDS = ["bœuf bourguignon", "poulet rôti"];

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AnimatedTitle", () => {
  it("exposes the full sentence as a single accessible heading string", () => {
    render(
      <AnimatedTitle prefix="Votre" words={WORDS} suffix=", en version végétarienne." />,
    );

    // The per-word visual split is aria-hidden, so the heading's accessible
    // name is the one clean sentence, not a fragmented reading order.
    expect(
      screen.getByRole("heading", {
        name: "Votre bœuf bourguignon, en version végétarienne.",
      }),
    ).toBeInTheDocument();
  });

  it("shows the first word statically, without transforms, under reduced motion", () => {
    window.matchMedia = ((query: string) => ({
      matches: query.includes("reduce"),
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    })) as typeof window.matchMedia;

    render(
      <AnimatedTitle prefix="Votre" words={WORDS} suffix=", en version végétarienne." />,
    );

    const word = screen.getByText("bœuf bourguignon");
    expect(word.style.transform ?? "").not.toMatch(/translate/);
  });
});
