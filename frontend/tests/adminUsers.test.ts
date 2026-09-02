import { afterEach, describe, expect, it, vi } from "vitest";
import { getUser, listUsers } from "../src/api/adminUsers";

const listBody = [
  {
    id: 2,
    email: "person@example.com",
    is_admin: false,
    created_at: "2026-08-30T10:15:00Z",
    watchlist_count: 3,
    like_count: 1,
    has_preferences: true,
  },
  {
    id: 1,
    email: "admin@example.com",
    is_admin: true,
    created_at: "2026-07-01T08:00:00Z",
    watchlist_count: 0,
    like_count: 0,
    has_preferences: false,
  },
];

describe("listUsers", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("GETs /admin/users with credentials and maps snake_case to camelCase", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(listBody),
    });
    vi.stubGlobal("fetch", fetchMock);

    const users = await listUsers();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/users$/);
    expect(init.credentials).toBe("include");
    expect(users).toEqual([
      {
        id: 2,
        email: "person@example.com",
        isAdmin: false,
        createdAt: "2026-08-30T10:15:00Z",
        watchlistCount: 3,
        likeCount: 1,
        hasPreferences: true,
      },
      {
        id: 1,
        email: "admin@example.com",
        isAdmin: true,
        createdAt: "2026-07-01T08:00:00Z",
        watchlistCount: 0,
        likeCount: 0,
        hasPreferences: false,
      },
    ]);
  });

  it("throws when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 403 }));

    await expect(listUsers()).rejects.toThrow("403");
  });
});

describe("getUser", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps preferences, watchlist and likes", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          id: 2,
          email: "person@example.com",
          is_admin: false,
          created_at: "2026-08-30T10:15:00Z",
          watchlist_count: 1,
          like_count: 1,
          has_preferences: true,
          preferences: {
            calorie_orientation: "balanced",
            diet: "vegetarian",
            allergens: ["gluten"],
            price_range: 2,
          },
          watchlist: [
            {
              recipe_id: 7,
              title: "Curry de lentilles",
              image_url: "/media/curry.jpg",
              notes: "Pour dimanche",
              planned_for: "2026-09-06",
            },
          ],
          likes: [{ recipe_id: 9, title: "Dahl de pois cassés", image_url: null }],
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = await getUser(2);

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/users\/2$/);
    expect(user.preferences).toEqual({
      calorieOrientation: "balanced",
      diet: "vegetarian",
      allergens: ["gluten"],
      priceRange: 2,
    });
    expect(user.watchlist).toEqual([
      {
        recipeId: 7,
        title: "Curry de lentilles",
        imageUrl: "/media/curry.jpg",
        notes: "Pour dimanche",
        plannedFor: "2026-09-06",
      },
    ]);
    expect(user.likes).toEqual([
      { recipeId: 9, title: "Dahl de pois cassés", imageUrl: null },
    ]);
  });

  it("keeps preferences null when the account never saved any", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            id: 3,
            email: "fresh@example.com",
            is_admin: false,
            created_at: "2026-08-30T10:15:00Z",
            watchlist_count: 0,
            like_count: 0,
            has_preferences: false,
            preferences: null,
            watchlist: [],
            likes: [],
          }),
      }),
    );

    const user = await getUser(3);

    expect(user.preferences).toBeNull();
    expect(user.watchlist).toEqual([]);
    expect(user.likes).toEqual([]);
  });

  it("throws when the user does not exist", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404 }));

    await expect(getUser(999)).rejects.toThrow("404");
  });
});
