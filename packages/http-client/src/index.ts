import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

export type TokenPair = { accessToken: string; refreshToken: string };
export type RefreshResult = TokenPair | null;

type TokenStore = {
  getAccessToken: () => string | undefined;
  getRefreshToken: () => string | undefined;
  setTokens: (tokens: TokenPair) => void;
  clearTokens: () => void;
};

const tokenStore: TokenStore = {
  getAccessToken: () => undefined,
  getRefreshToken: () => undefined,
  setTokens: () => undefined,
  clearTokens: () => undefined,
};

let refreshHandler: (() => Promise<RefreshResult>) | null = null;
let refreshingPromise: Promise<RefreshResult> | null = null;

export function registerTokenStore(store: TokenStore) {
  tokenStore.getAccessToken = store.getAccessToken;
  tokenStore.getRefreshToken = store.getRefreshToken;
  tokenStore.setTokens = store.setTokens;
  tokenStore.clearTokens = store.clearTokens;
}

export function registerRefreshHandler(handler: () => Promise<RefreshResult>) {
  refreshHandler = handler;
}

function resolveDefaultApiBaseUrl(): string {
  // Next injects process.env; Vite browsers do not — guard so mobile/workshop can load.
  if (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  // Prefer 127.0.0.1 on Windows: `localhost` can resolve to ::1 first and stall.
  return "http://127.0.0.1:8000";
}

export const apiClient = axios.create({
  baseURL: resolveDefaultApiBaseUrl(),
  timeout: 15000,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status;
    const url = original?.url ?? "";
    const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/refresh");
    if (
      status !== 401 ||
      original?._retry ||
      isAuthEndpoint ||
      !refreshHandler ||
      !tokenStore.getRefreshToken()
    ) {
      throw error;
    }
    original._retry = true;
    if (!refreshingPromise) {
      refreshingPromise = refreshHandler().finally(() => {
        refreshingPromise = null;
      });
    }
    const refreshed = await refreshingPromise;
    if (!refreshed) {
      tokenStore.clearTokens();
      throw error;
    }
    tokenStore.setTokens(refreshed);
    original.headers.Authorization = `Bearer ${refreshed.accessToken}`;
    return apiClient.request(original);
  },
);
