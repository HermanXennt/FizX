import { apiClient } from "@/lib/api-client";
import type { AuthResponse, User } from "@/types/user";

export interface RegisterPayload {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authService = {
  register: (payload: RegisterPayload) =>
    apiClient.post<AuthResponse>("/auth/register/", payload).then((r) => r.data),

  login: (payload: LoginPayload) =>
    apiClient.post<AuthResponse>("/auth/login/", payload).then((r) => r.data),

  logout: (refresh: string) => apiClient.post("/auth/logout/", { refresh }),

  googleLogin: (idToken: string) =>
    apiClient.post<AuthResponse>("/auth/google/", { id_token: idToken }).then((r) => r.data),

  requestPasswordReset: (email: string) => apiClient.post("/auth/password-reset/", { email }),

  confirmPasswordReset: (payload: { uid: string; token: string; new_password: string }) =>
    apiClient.post("/auth/password-reset/confirm/", payload),

  verifyEmail: (payload: { uid: string; token: string }) =>
    apiClient.post<User>("/auth/email/verify/confirm/", payload).then((r) => r.data),

  resendVerification: () => apiClient.post("/auth/email/verify/resend/"),

  me: () => apiClient.get<User>("/users/me/").then((r) => r.data),

  updateProfile: (payload: Partial<Pick<User, "first_name" | "last_name" | "timezone">>) =>
    apiClient.patch<User>("/users/me/", payload).then((r) => r.data),

  uploadAvatar: (file: File) => {
    const form = new FormData();
    form.append("avatar", file);
    return apiClient.post<User>("/users/me/avatar/", form).then((r) => r.data);
  },

  updatePresence: (presence_status: string) =>
    apiClient.patch<User>("/users/me/presence/", { presence_status }).then((r) => r.data),

  changePassword: (payload: { old_password: string; new_password: string }) =>
    apiClient.post("/users/me/password/", payload),
};
