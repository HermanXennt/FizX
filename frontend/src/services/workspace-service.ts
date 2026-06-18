import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api";
import type { Invitation, Workspace, WorkspaceMember, WorkspaceRole } from "@/types/workspace";

export const workspaceService = {
  list: () => apiClient.get<PaginatedResponse<Workspace>>("/workspaces/").then((r) => r.data.results),

  retrieve: (id: string) => apiClient.get<Workspace>(`/workspaces/${id}/`).then((r) => r.data),

  create: (payload: { name: string; description?: string }) =>
    apiClient.post<Workspace>("/workspaces/", payload).then((r) => r.data),

  update: (id: string, payload: Partial<Pick<Workspace, "name" | "description">>) =>
    apiClient.patch<Workspace>(`/workspaces/${id}/`, payload).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/workspaces/${id}/`),

  leave: (id: string) => apiClient.post(`/workspaces/${id}/leave/`),

  members: (id: string, search?: string) =>
    apiClient
      .get<WorkspaceMember[]>(`/workspaces/${id}/members/`, { params: search ? { q: search } : undefined })
      .then((r) => r.data),

  changeMemberRole: (id: string, userId: string, role: WorkspaceRole) =>
    apiClient.patch<WorkspaceMember>(`/workspaces/${id}/members/${userId}/`, { role }).then((r) => r.data),

  removeMember: (id: string, userId: string) => apiClient.delete(`/workspaces/${id}/members/${userId}/`),

  invitations: (id: string) =>
    apiClient.get<Invitation[]>(`/workspaces/${id}/invitations/`).then((r) => r.data),

  invite: (id: string, phone_number: string, role: "admin" | "member") =>
    apiClient.post<Invitation>(`/workspaces/${id}/invitations/`, { phone_number, role }).then((r) => r.data),

  revokeInvitation: (id: string, invitationId: string) =>
    apiClient.post(`/workspaces/${id}/invitations/${invitationId}/revoke/`),

  previewInvitation: (token: string) =>
    apiClient.get<Invitation>(`/workspaces/invitations/${token}/`).then((r) => r.data),

  acceptInvitation: (token: string) =>
    apiClient.post<WorkspaceMember>(`/workspaces/invitations/${token}/accept/`).then((r) => r.data),

  declineInvitation: (token: string) =>
    apiClient.post<Invitation>(`/workspaces/invitations/${token}/decline/`).then((r) => r.data),
};
