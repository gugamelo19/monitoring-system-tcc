const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

type RequestOptions = RequestInit & {
  token?: string | null;
};

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Erro na requisição.");
  }

  return response.json();
}

export async function loginRequest(username: string, password: string) {
  return apiFetch<{ access: string; refresh: string }>("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function updateAlertStatus(
  alertId: string,
  status: string,
  token: string,
) {
  return apiFetch(`/api/alerts/${alertId}/`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ status }),
  });
}

export async function createAsset(
  payload: Record<string, unknown>,
  token: string,
) {
  return apiFetch("/api/assets/", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function updateAsset(
  assetId: string,
  payload: Record<string, unknown>,
  token: string,
) {
  return apiFetch(`/api/assets/${assetId}/`, {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}
