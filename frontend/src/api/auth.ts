import type { User } from "../types/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface UserResponseBody {
  email: string;
  is_admin: boolean;
}

function toUser(body: UserResponseBody): User {
  return { email: body.email, isAdmin: body.is_admin };
}

/** A non-2xx API response. `serverMessage` is the backend's `detail` when it
 * sent a plain string — always French, safe to show as-is. */
export class ApiError extends Error {
  readonly status: number;
  readonly serverMessage: string | null;

  constructor(status: number, serverMessage: string | null, fallback: string) {
    super(serverMessage ?? fallback);
    this.name = "ApiError";
    this.status = status;
    this.serverMessage = serverMessage;
  }
}

async function toApiError(response: Response, fallback: string): Promise<ApiError> {
  let serverMessage: string | null = null;
  try {
    const body = (await response.json()) as { detail?: unknown };
    // 422 validation errors carry a list, not a sentence: not shown as-is.
    if (typeof body.detail === "string") {
      serverMessage = body.detail;
    }
  } catch {
    // No JSON body: fall back to the generic message.
  }
  return new ApiError(response.status, serverMessage, fallback);
}

/** What to show the user for a failed auth call: the server's own French
 * message when there is one (wrong password, too many attempts, password
 * too short...), else `fallback` (network down, server error). */
export function describeAuthError(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.serverMessage) {
    return err.serverMessage;
  }
  return fallback;
}

export async function login(email: string, password: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw await toApiError(response, `Login request failed: ${response.status}`);
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
    throw await toApiError(response, `Signup request failed: ${response.status}`);
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
    throw await toApiError(response, `Request failed: ${response.status}`);
  }
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/password-reset/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });

  if (!response.ok) {
    throw await toApiError(response, `Request failed: ${response.status}`);
  }
}

export async function updateAccount(updates: {
  currentPassword: string;
  email?: string;
  password?: string;
}): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/account`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      current_password: updates.currentPassword,
      email: updates.email,
      password: updates.password,
    }),
  });

  if (!response.ok) {
    throw await toApiError(response, `Request failed: ${response.status}`);
  }

  return toUser((await response.json()) as UserResponseBody);
}

export async function deleteAccount(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/account`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    throw await toApiError(response, `Request failed: ${response.status}`);
  }
}
