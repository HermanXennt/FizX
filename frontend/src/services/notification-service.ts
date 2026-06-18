import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api";
import type { AppNotification } from "@/types/notification";

export const notificationService = {
  list: (unreadOnly = false) =>
    apiClient
      .get<PaginatedResponse<AppNotification>>("/notifications/", {
        params: unreadOnly ? { unread: "true" } : undefined,
      })
      .then((r) => r.data),

  unreadCount: () => apiClient.get<{ count: number }>("/notifications/unread-count/").then((r) => r.data.count),

  markRead: (id: string) =>
    apiClient.post<AppNotification>(`/notifications/${id}/read/`).then((r) => r.data),

  markAllRead: () => apiClient.post<{ marked_read: number }>("/notifications/read-all/").then((r) => r.data),
};
