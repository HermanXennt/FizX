"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { chatService } from "@/services/chat-service";
import type { ChatMessage } from "@/types/chat";
import { useWebSocket } from "./use-websocket";

type Scope = { kind: "meeting"; id: string } | { kind: "workspace"; id: string };

function scopeKey(scope: Scope) {
  return [scope.kind === "meeting" ? "meeting-chat" : "workspace-chat", scope.id] as const;
}

export function useChat(scope: Scope) {
  const queryClient = useQueryClient();
  const queryKey = scopeKey(scope);

  const channelQuery = useQuery({
    queryKey: [...queryKey, "channel"],
    queryFn: () =>
      scope.kind === "meeting" ? chatService.meetingChannel(scope.id) : chatService.workspaceChannel(scope.id),
  });

  const messagesQuery = useQuery({
    queryKey: [...queryKey, "messages"],
    queryFn: () =>
      scope.kind === "meeting" ? chatService.meetingMessages(scope.id) : chatService.workspaceMessages(scope.id),
  });

  const onSocketMessage = useCallback(
    (data: unknown) => {
      const event = data as { type?: string; message?: ChatMessage; payload?: Record<string, unknown> };

      if (event.type === "message.created" && event.message) {
        queryClient.setQueryData<ChatMessage[]>([...queryKey, "messages"], (current) => {
          if (!current) return [event.message as ChatMessage];
          if (current.some((m) => m.id === event.message!.id)) return current;
          return [...current, event.message as ChatMessage];
        });
      }

      if (event.type === "reaction.updated" && event.payload) {
        queryClient.invalidateQueries({ queryKey: [...queryKey, "messages"] });
      }
    },
    [queryClient, queryKey]
  );

  const { send } = useWebSocket(channelQuery.data ? `/ws/chat/${channelQuery.data.id}/` : null, onSocketMessage);

  const sendMessage = useCallback(
    (content: string) => {
      send({ type: "message.send", content });
    },
    [send]
  );

  const sendTyping = useCallback(() => send({ type: "typing" }), [send]);

  // Goes over REST, not the WebSocket - the consumer's message.send handler
  // only takes JSON text, so binary attachments have to go through the same
  // multipart endpoint the one-time "Import" flows use elsewhere. The sender
  // is a member of the channel's own WS group, so the broadcasted
  // message.created event lands back in their own cache the same way it
  // does for everyone else - no separate optimistic update needed.
  const sendAttachment = useCallback(
    async (file: File, content = "") => {
      const formData = new FormData();
      formData.append("attachment", file);
      if (content) formData.append("content", content);
      if (scope.kind === "meeting") {
        await chatService.sendMeetingAttachment(scope.id, formData);
      } else {
        await chatService.sendWorkspaceAttachment(scope.id, formData);
      }
    },
    [scope.kind, scope.id]
  );

  return {
    channel: channelQuery.data,
    messages: messagesQuery.data ?? [],
    isLoading: channelQuery.isLoading || messagesQuery.isLoading,
    sendMessage,
    sendTyping,
    sendAttachment,
  };
}
