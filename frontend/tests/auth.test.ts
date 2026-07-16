import { afterEach, describe, expect, it, vi } from "vitest";
import { getCurrentAdmin, login, logout } from "../src/api/auth";

describe("login", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs credentials with credentials included and returns the parsed response", async () => {
    const mockResponse = { email: "admin@example.com" };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
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
    expect(result).toEqual(mockResponse);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: () => Promise.resolve({}) }),
    );

    await expect(login("admin@example.com", "wrong")).rejects.toThrow("401");
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

describe("getCurrentAdmin", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the parsed admin when the session is valid", async () => {
    const mockResponse = { email: "admin@example.com" };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      }),
    );

    await expect(getCurrentAdmin()).resolves.toEqual(mockResponse);
  });

  it("returns null when the session is missing or invalid (401)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: () => Promise.resolve({}) }),
    );

    await expect(getCurrentAdmin()).resolves.toBeNull();
  });

  it("throws for other error statuses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, json: () => Promise.resolve({}) }),
    );

    await expect(getCurrentAdmin()).rejects.toThrow("500");
  });
});
