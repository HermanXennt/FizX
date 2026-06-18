"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsService } from "@/services/analytics-service";

export function useMyStats() {
  return useQuery({ queryKey: ["analytics", "me"], queryFn: analyticsService.myStats });
}

export function useWorkspaceOverview(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ["analytics", "workspace", workspaceId],
    queryFn: () => analyticsService.workspaceOverview(workspaceId as string),
    enabled: Boolean(workspaceId),
  });
}
