import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/user";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setSession: (params: { user: User; access: string; refresh: string }) => void;
  setTokens: (params: { access: string; refresh: string }) => void;
  setUser: (user: User) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setSession: ({ user, access, refresh }) =>
        set({ user, accessToken: access, refreshToken: refresh, isAuthenticated: true }),
      setTokens: ({ access, refresh }) => set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),
      clearSession: () =>
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
    }),
    {
      name: "fizx-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
