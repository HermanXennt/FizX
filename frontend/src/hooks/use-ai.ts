"use client";

import { useMutation } from "@tanstack/react-query";
import { aiService, type AskAiPayload } from "@/services/ai-service";

export function useAskAi() {
  return useMutation({
    mutationFn: (payload: AskAiPayload) => aiService.ask(payload),
  });
}
