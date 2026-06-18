import { apiClient } from "@/lib/api-client";
import type { ChatMessage } from "@/types/chat";

interface Channel {
  id: string;
  type: "meeting" | "workspace";
  name: string;
  workspace: string | null;
  meeting: string | null;
  created_at: string;
}

export const chatService = {
  meetingChannel: (meetingId: string) =>
    apiClient.get<Channel>(`/chat/meetings/${meetingId}/channel/`).then((r) => r.data),

  workspaceChannel: (workspaceId: string) =>
    apiClient.get<Channel>(`/chat/workspaces/${workspaceId}/channel/`).then((r) => r.data),

  meetingMessages: (meetingId: string) =>
    apiClient.get<ChatMessage[]>(`/chat/meetings/${meetingId}/messages/`).then((r) => r.data),

  sendMeetingMessage: (meetingId: string, content: string) =>
    apiClient.post<ChatMessage>(`/chat/meetings/${meetingId}/messages/`, { content }).then((r) => r.data),

  workspaceMessages: (workspaceId: string) =>
    apiClient.get<ChatMessage[]>(`/chat/workspaces/${workspaceId}/messages/`).then((r) => r.data),

  sendWorkspaceMessage: (workspaceId: string, content: string) =>
    apiClient.post<ChatMessage>(`/chat/workspaces/${workspaceId}/messages/`, { content }).then((r) => r.data),

  editMessage: (messageId: string, content: string) =>
    apiClient.patch<ChatMessage>(`/chat/messages/${messageId}/`, { content }).then((r) => r.data),

  deleteMessage: (messageId: string) =>
    apiClient.delete<ChatMessage>(`/chat/messages/${messageId}/`).then((r) => r.data),

  toggleReaction: (messageId: string, emoji: string) =>
    apiClient.post(`/chat/messages/${messageId}/reactions/`, { emoji }).then((r) => r.data),
};
