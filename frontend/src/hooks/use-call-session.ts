"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { meetingService } from "@/services/meeting-service";
import { extractErrorMessage } from "@/lib/api-client";
import type { JoinMeetingResponse } from "@/types/meeting";

type SessionState =
  | { phase: "joining" }
  | { phase: "needs-password"; error?: string }
  | { phase: "waiting"; response: JoinMeetingResponse }
  | { phase: "admitted"; response: JoinMeetingResponse }
  | { phase: "error"; message: string };

export function useCallSession(meetingId: string) {
  const [state, setState] = useState<SessionState>({ phase: "joining" });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const attemptJoin = useCallback(
    async (password?: string) => {
      try {
        const response = await meetingService.join(meetingId, password);
        if (response.status === "waiting") {
          setState({ phase: "waiting", response });
        } else {
          setState({ phase: "admitted", response });
        }
      } catch (error) {
        const message = extractErrorMessage(error);
        if (message.toLowerCase().includes("password")) {
          setState({ phase: "needs-password", error: password ? message : undefined });
        } else {
          setState({ phase: "error", message });
        }
      }
    },
    [meetingId]
  );

  useEffect(() => {
    // attemptJoin is async and only calls setState after its first `await`
    // (i.e. once the network response resolves), so this never synchronously
    // cascades a render the way the lint rule assumes - matches React's own
    // "fetching data in an effect" pattern: https://react.dev/learn/synchronizing-with-effects#fetching-data
    // eslint-disable-next-line react-hooks/set-state-in-effect
    attemptJoin();
  }, [attemptJoin]);

  // While waiting for the host to admit us, poll for a token until we're let in.
  useEffect(() => {
    if (state.phase !== "waiting") {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }

    pollRef.current = setInterval(async () => {
      try {
        const response = await meetingService.getToken(meetingId);
        if (response.status === "admitted") {
          setState({ phase: "admitted", response });
        }
      } catch {
        // host hasn't admitted yet, or meeting ended - keep waiting / let user leave manually
      }
    }, 4000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [state.phase, meetingId]);

  const submitPassword = useCallback((password: string) => attemptJoin(password), [attemptJoin]);

  return { state, submitPassword };
}
