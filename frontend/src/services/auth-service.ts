import { apiClient } from "@/lib/api-client";
import type { AuthResponse, User } from "@/types/user";

export const authService = {
  requestOtp: (phone_number: string) => apiClient.post("/auth/otp/request/", { phone_number }),

  verifyOtp: (payload: {
    phone_number: string;
    code: string;
    first_name?: string;
    account_type?: "teacher" | "student";
  }) => apiClient.post<AuthResponse>("/auth/otp/verify/", payload).then((r) => r.data),

  logout: (refresh: string) => apiClient.post("/auth/logout/", { refresh }),

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
};
