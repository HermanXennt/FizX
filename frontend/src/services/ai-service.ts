import { apiClient } from "@/lib/api-client";

export type AiPreset = "summarize" | "action_items" | "follow_up_email" | "who_hasnt_spoken";

export interface AskAiPayload {
  message?: string;
  preset?: AiPreset;
  meeting_id?: string;
}

export const aiService = {
  ask: (payload: AskAiPayload) => apiClient.post<{ reply: string }>("/ai/ask/", payload).then((r) => r.data),
};
