import axios from "axios";
import { getAuthToken } from "./auth";

/**
 * Axios client con baseURL relativa.
 * Tutte le chiamate a /api/v1/* vengono intercettate da Next.js
 * (next.config.ts rewrites) e proxate al backend FastAPI.
 * Questo elimina CORS: il browser parla sempre con localhost:3000.
 */
const apiClient = axios.create({
  baseURL: "",
});

apiClient.interceptors.request.use(async (config) => {
  const token = await getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "API request failed";
    return Promise.reject(new Error(message));
  }
);

export default apiClient;

// Compatibility wrapper: traduce fetch-style options in chiamate Axios
interface ApiFetchOptions extends RequestInit {
  requireAuth?: boolean;
}

export async function apiFetch(endpoint: string, options: ApiFetchOptions = {}) {
  const { method = "GET", body, requireAuth = true } = options;

  const headers: Record<string, string> = {};
  if (requireAuth) {
    const token = await getAuthToken();
    if (!token) throw new Error("No auth token available. User might be logged out.");
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await apiClient.request({
    url: endpoint,
    method: method as string,
    data: body ? JSON.parse(body as string) : undefined,
    headers,
  });

  return response.data;
}
