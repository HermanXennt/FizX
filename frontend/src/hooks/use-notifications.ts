"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { notificationService } from "@/services/notification-service";
import type { AppNotification } from "@/types/notification";
import { useAuthStore } from "@/store/auth-store";
import { useWebSocket } from "./use-websocket";

export function useNotifications() {
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const listQuery = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationService.list(),
    enabled: isAuthenticated,
  });

  const unreadCountQuery = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => notificationService.unreadCount(),
    enabled: isAuthenticated,
  });

  const onSocketMessage = useCallback(
    (data: unknown) => {
      const event = data as { type?: string; notification?: AppNotification };
      if (event.type === "notification.created" && event.notification) {
        queryClient.setQueryData<{ results: AppNotification[] } | undefined>(["notifications"], (current) => {
          if (!current) return current;
          return { ...current, results: [event.notification as AppNotification, ...current.results] };
        });
        queryClient.setQueryData<number>(["notifications", "unread-count"], (count) => (count ?? 0) + 1);
      }
    },
    [queryClient]
  );

  useWebSocket(isAuthenticated ? "/ws/notifications/" : null, onSocketMessage);

  const markRead = useMutation({
    mutationFn: (id: string) => notificationService.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAllRead = useMutation({
    mutationFn: () => notificationService.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return {
    notifications: listQuery.data?.results ?? [],
    unreadCount: unreadCountQuery.data ?? 0,
    isLoading: listQuery.isLoading,
    markRead: markRead.mutate,
    markAllRead: markAllRead.mutate,
  };
}
