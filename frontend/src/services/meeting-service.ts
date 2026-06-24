import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api";
import type {
  CreateInstantMeetingPayload,
  JoinMeetingResponse,
  Meeting,
  MeetingParticipant,
  ScheduleMeetingPayload,
} from "@/types/meeting";

export interface IceServer {
  urls: string[];
  username?: string;
  credential?: string;
}

export const meetingService = {
  iceServers: () => apiClient.get<{ ice_servers: IceServer[] }>("/meetings/ice-servers/").then((r) => r.data.ice_servers),

  list: (params?: { status?: string; workspace?: string }) =>
    apiClient.get<PaginatedResponse<Meeting>>("/meetings/", { params }).then((r) => r.data.results),

  retrieve: (id: string) => apiClient.get<Meeting>(`/meetings/${id}/`).then((r) => r.data),

  createInstant: (payload: CreateInstantMeetingPayload = {}) =>
    apiClient.post<Meeting>("/meetings/instant/", payload).then((r) => r.data),

  schedule: (payload: ScheduleMeetingPayload) =>
    apiClient.post<Meeting>("/meetings/", payload).then((r) => r.data),

  update: (id: string, payload: Partial<ScheduleMeetingPayload>) =>
    apiClient.patch<Meeting>(`/meetings/${id}/`, payload).then((r) => r.data),

  start: (id: string) => apiClient.post<Meeting>(`/meetings/${id}/start/`).then((r) => r.data),

  end: (id: string) => apiClient.post<Meeting>(`/meetings/${id}/end/`).then((r) => r.data),

  cancel: (id: string) => apiClient.post<Meeting>(`/meetings/${id}/cancel/`).then((r) => r.data),

  join: (id: string, password?: string) =>
    apiClient.post<JoinMeetingResponse>(`/meetings/${id}/join/`, { password }).then((r) => r.data),

  getToken: (id: string) => apiClient.get<JoinMeetingResponse>(`/meetings/${id}/token/`).then((r) => r.data),

  leave: (id: string) => apiClient.post(`/meetings/${id}/leave/`),

  participants: (id: string) =>
    apiClient.get<MeetingParticipant[]>(`/meetings/${id}/participants/`).then((r) => r.data),

  admitParticipant: (id: string, participantId: string) =>
    apiClient
      .post<MeetingParticipant>(`/meetings/${id}/participants/${participantId}/admit/`)
      .then((r) => r.data),

  denyParticipant: (id: string, participantId: string) =>
    apiClient
      .post<MeetingParticipant>(`/meetings/${id}/participants/${participantId}/deny/`)
      .then((r) => r.data),

  removeParticipant: (id: string, participantId: string) =>
    apiClient
      .post<MeetingParticipant>(`/meetings/${id}/participants/${participantId}/remove/`)
      .then((r) => r.data),

  muteAll: (id: string) => apiClient.post<{ muted_identities: string[] }>(`/meetings/${id}/mute_all/`).then((r) => r.data),

  setParticipantMedia: (id: string, participantId: string, payload: { mic_enabled?: boolean; camera_enabled?: boolean }) =>
    apiClient
      .patch<MeetingParticipant>(`/meetings/${id}/participants/${participantId}/media/`, payload)
      .then((r) => r.data),

  syncPermissions: (id: string) => apiClient.post(`/meetings/${id}/sync-permissions/`),

  raiseHand: (id: string, raised: boolean) =>
    apiClient.post<MeetingParticipant>(`/meetings/${id}/hand/`, { raised }).then((r) => r.data),

  markSpoken: (id: string) =>
    apiClient.post<MeetingParticipant>(`/meetings/${id}/mark-spoken/`).then((r) => r.data),
};
