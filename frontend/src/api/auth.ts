import type { AdminUser } from "../types/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function login(email: string, password: string): Promise<AdminUser> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(`Login request failed: ${response.status}`);
  }

  return response.json() as Promise<AdminUser>;
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function getCurrentAdmin(): Promise<AdminUser | null> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    credentials: "include",
  });

  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch current admin: ${response.status}`);
  }

  return response.json() as Promise<AdminUser>;
}
