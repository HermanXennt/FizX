import { apiClient } from "@/lib/api-client";
import type { StudentRosterEntry, UserStats, WorkspaceOverview } from "@/types/analytics";

export const analyticsService = {
  myStats: () => apiClient.get<UserStats>("/analytics/me/").then((r) => r.data),

  workspaceOverview: (workspaceId: string) =>
    apiClient.get<WorkspaceOverview>(`/analytics/workspaces/${workspaceId}/overview/`).then((r) => r.data),

  workspaceStudentRoster: (workspaceId: string) =>
    apiClient.get<StudentRosterEntry[]>(`/analytics/workspaces/${workspaceId}/students/`).then((r) => r.data),

  logEvent: (payload: { event_type: string; name: string; workspace?: string; metadata?: Record<string, unknown> }) =>
    apiClient.post("/analytics/events/", payload),
};
