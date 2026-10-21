import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  confirmPasswordReset,
  describeAuthError,
  deleteAccount,
  getCurrentUser,
  login,
  logout,
  requestPasswordReset,
  signup,
  updateAccount,
} from "../src/api/auth";

describe("login", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs credentials with credentials included and maps the response to camelCase", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ email: "admin@example.com", is_admin: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await login("admin@example.com", "secret");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/login$/),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ email: "admin@example.com", password: "secret" }),
      }),
    );
    expect(result).toEqual({ email: "admin@example.com", isAdmin: true });
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: () => Promise.resolve({}) }),
    );

    await expect(login("admin@example.com", "wrong")).rejects.toThrow("401");
  });
});

describe("signup", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs credentials and maps the response, defaulting is_admin to false", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ email: "person@example.com", is_admin: false }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await signup("person@example.com", "secret");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/signup$/),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ email: "person@example.com", password: "secret" }),
      }),
    );
    expect(result).toEqual({ email: "person@example.com", isAdmin: false });
  });

  it("surfaces the server's detail message on a duplicate-email conflict", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: () => Promise.resolve({ detail: "Cet email est déjà utilisé" }),
      }),
    );

    await expect(signup("taken@example.com", "secret")).rejects.toThrow(
      "Cet email est déjà utilisé",
    );
  });
});

describe("logout", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs to /auth/logout with credentials included", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await logout();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/logout$/),
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });
});

describe("getCurrentUser", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the mapped user when the session is valid", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ email: "person@example.com", is_admin: false }),
      }),
    );

    await expect(getCurrentUser()).resolves.toEqual({
      email: "person@example.com",
      isAdmin: false,
    });
  });

  it("returns null when the session is missing or invalid (401)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: () => Promise.resolve({}) }),
    );

    await expect(getCurrentUser()).resolves.toBeNull();
  });

  it("throws for other error statuses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, json: () => Promise.resolve({}) }),
    );

    await expect(getCurrentUser()).rejects.toThrow("500");
  });
});

describe("requestPasswordReset", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the email and resolves without exposing any token", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: "ok" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestPasswordReset("person@example.com")).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/password-reset\/request$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "person@example.com" }),
      }),
    );
  });

  it("throws when the server responds with an error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({}),
      }),
    );

    await expect(requestPasswordReset("person@example.com")).rejects.toThrow();
  });
});

describe("confirmPasswordReset", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the token and new password", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await confirmPasswordReset("abc123", "new password");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/password-reset\/confirm$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ token: "abc123", new_password: "new password" }),
      }),
    );
  });

  it("throws when the token is invalid or expired", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Lien de réinitialisation invalide ou expiré" }),
      }),
    );

    await expect(confirmPasswordReset("bad-token", "new password")).rejects.toThrow(
      "Lien de réinitialisation invalide ou expiré",
    );
  });
});

describe("updateAccount", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("PATCHes the given fields and maps the response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ email: "new@example.com", is_admin: false }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await updateAccount({
      currentPassword: "old password",
      email: "new@example.com",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/account$/),
      expect.objectContaining({
        method: "PATCH",
        credentials: "include",
        body: JSON.stringify({ current_password: "old password", email: "new@example.com" }),
      }),
    );
    expect(result).toEqual({ email: "new@example.com", isAdmin: false });
  });
});

describe("ApiError / describeAuthError", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("carries the status and the server's French message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: "Identifiants invalides" }),
      }),
    );

    const error = await login("person@example.com", "wrong").catch((err: unknown) => err);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(401);
    expect(describeAuthError(error, "fallback")).toBe("Identifiants invalides");
  });

  it("ignores non-string details such as 422 validation lists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: () => Promise.resolve({ detail: [{ msg: "Field required" }] }),
      }),
    );

    const error = await login("person@example.com", "x").catch((err: unknown) => err);

    expect(describeAuthError(error, "fallback")).toBe("fallback");
  });

  it("falls back for network failures", () => {
    expect(describeAuthError(new TypeError("Failed to fetch"), "fallback")).toBe("fallback");
  });
});

describe("deleteAccount", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("DELETEs the current account with credentials included", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await deleteAccount();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/account$/),
      expect.objectContaining({ method: "DELETE", credentials: "include" }),
    );
  });
});
