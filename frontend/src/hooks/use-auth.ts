"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authService, type LoginPayload, type RegisterPayload } from "@/services/auth-service";
import { useAuthStore } from "@/store/auth-store";

export function useLogin() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);

  return useMutation({
    mutationFn: (payload: LoginPayload) => authService.login(payload),
    onSuccess: (data) => {
      setSession(data);
      router.push("/");
    },
  });
}

export function useRegister() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);

  return useMutation({
    mutationFn: (payload: RegisterPayload) => authService.register(payload),
    onSuccess: (data) => {
      setSession(data);
      router.push("/");
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const clearSession = useAuthStore((s) => s.clearSession);

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await authService.logout(refreshToken).catch(() => undefined);
      }
    },
    onSuccess: () => {
      clearSession();
      router.push("/login");
    },
  });
}
