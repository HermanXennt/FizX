import { apiClient } from "@/lib/api-client";
import type { MeetingRecording } from "@/types/recording";

export const recordingService = {
  mine: () => apiClient.get<MeetingRecording[]>("/recordings/").then((r) => r.data),

  forMeeting: (meetingId: string) =>
    apiClient.get<MeetingRecording[]>(`/recordings/meetings/${meetingId}/`).then((r) => r.data),

  start: (meetingId: string) =>
    apiClient.post<MeetingRecording>(`/recordings/meetings/${meetingId}/`).then((r) => r.data),

  stop: (recordingId: string) =>
    apiClient.post<MeetingRecording>(`/recordings/${recordingId}/stop/`).then((r) => r.data),

  retrieve: (recordingId: string) =>
    apiClient.get<MeetingRecording>(`/recordings/${recordingId}/`).then((r) => r.data),
};
