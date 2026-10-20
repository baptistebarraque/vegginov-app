import type { User } from "../types/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface UserResponseBody {
  email: string;
  is_admin: boolean;
}

function toUser(body: UserResponseBody): User {
  return { email: body.email, isAdmin: body.is_admin };
}

async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function login(email: string, password: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Login request failed: ${response.status}`));
  }

  return toUser((await response.json()) as UserResponseBody);
}

export async function signup(email: string, password: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Signup request failed: ${response.status}`));
  }

  return toUser((await response.json()) as UserResponseBody);
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function getCurrentUser(): Promise<User | null> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    credentials: "include",
  });

  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch current user: ${response.status}`);
  }

  return toUser((await response.json()) as UserResponseBody);
}

export async function requestPasswordReset(email: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/password-reset/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Request failed: ${response.status}`));
  }
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/password-reset/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Request failed: ${response.status}`));
  }
}

export async function updateAccount(
  updates: { email?: string; password?: string }
): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/account`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Request failed: ${response.status}`));
  }

  return toUser((await response.json()) as UserResponseBody);
}

export async function deleteAccount(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/account`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Request failed: ${response.status}`));
  }
}
