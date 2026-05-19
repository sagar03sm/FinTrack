import { api } from "./api";

export interface AuthResponse {
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
    is_active: boolean;
    created_at: string;
  };
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
}

const ACCESS_KEY = "fintrack_access";
const REFRESH_KEY = "fintrack_refresh";
const USER_KEY = "fintrack_user";

export function setTokens(tokens: AuthResponse["tokens"]) {
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function setUser(user: AuthResponse["user"]) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getUser(): AuthResponse["user"] | null {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function register(email: string, password: string, name: string) {
  const res = await api.post<AuthResponse>("/auth/register", { email, password, name });
  setTokens(res.data.tokens);
  setUser(res.data.user);
  return res.data;
}

export async function login(email: string, password: string) {
  const res = await api.post<AuthResponse>("/auth/login", { email, password });
  setTokens(res.data.tokens);
  setUser(res.data.user);
  return res.data;
}

export async function logout() {
  clearTokens();
  window.location.href = "/login";
}

export async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return null;
  try {
    const res = await api.post<{ access_token: string; refresh_token: string; token_type: string }>(
      "/auth/refresh",
      { refresh_token: refresh }
    );
    setTokens(res.data);
    return res.data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

// Add access token to every request
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return api.request(error.config);
      }
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
