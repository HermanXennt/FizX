"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authService } from "@/services/auth-service";
import { useAuthStore } from "@/store/auth-store";

export function useRequestOtp() {
  return useMutation({
    mutationFn: (phone_number: string) => authService.requestOtp(phone_number),
  });
}

export function useVerifyOtp() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);

  return useMutation({
    mutationFn: (payload: { phone_number: string; code: string; first_name?: string }) =>
      authService.verifyOtp(payload),
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
