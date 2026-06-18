import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth-store";

// Relative by default: nginx proxies both the frontend and /api/ from the
// same origin, so a relative base URL resolves correctly no matter which
// host the browser used to load the page (localhost, a LAN IP, or a real
// domain) without needing a separate build per environment. Only set
// NEXT_PUBLIC_API_URL explicitly if the API truly lives on a different origin.
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Separate, interceptor-free instance for the refresh call itself - using
// `apiClient` here would recurse into the 401 handler below forever.
const refreshClient = axios.create({ baseURL: API_BASE_URL });

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = useAuthStore.getState().refreshToken;
  if (!refresh) return null;

  try {
    const { data } = await refreshClient.post<{ access: string; refresh?: string }>(
      "/auth/refresh/",
      { refresh }
    );
    useAuthStore.getState().setTokens({ access: data.access, refresh: data.refresh ?? refresh });
    return data.access;
  } catch {
    useAuthStore.getState().clearSession();
    return null;
  }
}

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined;

    if (error.response?.status === 401 && config && !config._retried) {
      config._retried = true;
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
      const newAccess = await refreshPromise;

      if (newAccess) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${newAccess}`;
        return apiClient(config);
      }

      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { error?: { message?: unknown } } | undefined;
    const message = data?.error?.message;
    if (typeof message === "string") return message;
    if (message && typeof message === "object") {
      const first = Object.values(message as Record<string, string[]>)[0];
      if (Array.isArray(first)) return first[0];
    }
    return error.message;
  }
  return "Something went wrong. Please try again.";
}
