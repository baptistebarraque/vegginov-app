import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { AdminUsersTable } from "../src/components/AdminUsersTable";
import type { AdminUserListItem } from "../src/types/adminUser";

function buildUser(overrides: Partial<AdminUserListItem> = {}): AdminUserListItem {
  return {
    id: 1,
    email: "person@example.com",
    isAdmin: false,
    createdAt: "2026-08-30T10:15:00Z",
    watchlistCount: 0,
    likeCount: 0,
    hasPreferences: false,
    ...overrides,
  };
}

function renderTable(users: AdminUserListItem[]) {
  return render(
    <MemoryRouter>
      <AdminUsersTable users={users} />
    </MemoryRouter>,
  );
}

describe("AdminUsersTable", () => {
  it("renders one row per account with its counts", () => {
    renderTable([
      buildUser({ id: 2, email: "person@example.com", watchlistCount: 3, likeCount: 1 }),
      buildUser({ id: 1, email: "admin@example.com", isAdmin: true }),
    ]);

    const rows = screen.getAllByRole("row").slice(1); // drop the header row
    expect(rows).toHaveLength(2);
    expect(within(rows[0]).getByText("person@example.com")).toBeInTheDocument();
    expect(within(rows[0]).getByText("3")).toBeInTheDocument();
    expect(within(rows[0]).getByText("1")).toBeInTheDocument();
  });

  it("marks admin accounts and links each row to its detail page", () => {
    renderTable([buildUser({ id: 4, email: "admin@example.com", isAdmin: true })]);

    expect(screen.getByText("Admin")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voir le détail" })).toHaveAttribute(
      "href",
      "/admin/users/4",
    );
  });

  it("says whether the account saved preferences", () => {
    renderTable([
      buildUser({ id: 1, email: "with@example.com", hasPreferences: true }),
      buildUser({ id: 2, email: "without@example.com", hasPreferences: false }),
    ]);

    expect(screen.getByText("Renseignées")).toBeInTheDocument();
    expect(screen.getByText("Aucune")).toBeInTheDocument();
  });

  it("falls back to a dash when the signup date is unparseable", () => {
    renderTable([buildUser({ createdAt: "not-a-date" })]);

    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
