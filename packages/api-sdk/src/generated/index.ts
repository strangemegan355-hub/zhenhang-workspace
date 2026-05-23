export type ApiPageResponse<T> = {
  code: string;
  message: string;
  data: {
    total: number;
    page: number;
    page_size: number;
    items: T[];
  };
};

export type LoginRequest = { username: string; password: string };
export type LoginResponse = { code: string; message: string; data: { access_token: string; token_type: string } };

export const AuthApi = {
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const resp = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return resp.json() as Promise<LoginResponse>;
  },
};
