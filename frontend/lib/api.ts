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
  // Non seguire redirect del backend: possono droppare Authorization.
  maxRedirects: 0,
  validateStatus: (status) => status >= 200 && status < 300,
});

apiClient.interceptors.request.use(async (config) => {
  const token = await getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function authError(message: string) {
  if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
    // Soft redirect: evita Unhandled Runtime Error su pagine protette
    window.location.assign("/it/login");
  }
  return new Error(message);
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 307 || error.response?.status === 308) {
      return Promise.reject(
        authError("Richiesta API reindirizzata (trailing slash). Aggiorna la pagina.")
      );
    }
    const detail =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      "";
    const status = error.response?.status;
    if (status === 401 || status === 403) {
      const message =
        detail === "Not authenticated" || detail === "Token scaduto" || detail === "Token non valido"
          ? "Sessione non valida. Accedi di nuovo."
          : detail || "Non autorizzato";
      return Promise.reject(authError(message));
    }
    const message = detail || error.message || "API request failed";
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
    if (!token) {
      throw authError("Sessione non valida. Accedi di nuovo.");
    }
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
