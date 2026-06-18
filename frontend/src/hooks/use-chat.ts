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

  return {
    channel: channelQuery.data,
    messages: messagesQuery.data ?? [],
    isLoading: channelQuery.isLoading || messagesQuery.isLoading,
    sendMessage,
    sendTyping,
  };
}
