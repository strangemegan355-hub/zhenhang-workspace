"use client";

import type { UserProfile } from "@zhenhang/auth";
import type { TokenPair } from "@zhenhang/http-client";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

type AuthState = {
  token?: TokenPair;
  user?: UserProfile;
  setSession: (token: TokenPair, user: UserProfile) => void;
  setTokens: (token: TokenPair) => void;
  setUser: (user: UserProfile) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: undefined,
      user: undefined,
      setSession: (token, user) => set({ token, user }),
      setTokens: (token) => set((s) => ({ ...s, token })),
      setUser: (user) => set((s) => ({ ...s, user })),
      clearSession: () => set({ token: undefined, user: undefined }),
    }),
    {
      name: "zhenhang-web-admin-auth",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
