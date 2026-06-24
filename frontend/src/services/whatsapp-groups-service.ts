import { apiClient } from "@/lib/api-client";

export type WhatsAppSessionStatus = "disconnected" | "connecting" | "qr" | "open" | "closed";

export interface WhatsAppGroup {
  id: string;
  name: string;
  participantCount: number;
}

export interface ImportWhatsAppGroupResult {
  added: number;
  invited: number;
  skipped: number;
}

export const whatsappGroupsService = {
  connect: () =>
    apiClient.post<{ status: WhatsAppSessionStatus }>("/users/me/whatsapp-groups/connect/").then((r) => r.data),

  disconnect: () =>
    apiClient.post<{ status: string }>("/users/me/whatsapp-groups/disconnect/").then((r) => r.data),

  status: () =>
    apiClient.get<{ status: WhatsAppSessionStatus }>("/users/me/whatsapp-groups/status/").then((r) => r.data),

  qr: () => apiClient.get<{ qr: string | null }>("/users/me/whatsapp-groups/qr/").then((r) => r.data),

  groups: () => apiClient.get<{ groups: WhatsAppGroup[] }>("/users/me/whatsapp-groups/groups/").then((r) => r.data),

  importGroup: (workspaceId: string, groupId: string, groupName: string) =>
    apiClient
      .post<ImportWhatsAppGroupResult>(`/workspaces/${workspaceId}/import-whatsapp-group/`, {
        group_id: groupId,
        group_name: groupName,
      })
      .then((r) => r.data),

  unlinkGroup: (workspaceId: string) =>
    apiClient.post(`/workspaces/${workspaceId}/unlink-whatsapp-group/`),
};
