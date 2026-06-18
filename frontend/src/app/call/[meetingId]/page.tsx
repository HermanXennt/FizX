"use client";

import { useParams } from "next/navigation";
import { AuthGuard } from "@/components/auth/auth-guard";
import { CallRoom } from "@/components/call/call-room";
import { PasswordPrompt } from "@/components/call/password-prompt";
import { WaitingRoom } from "@/components/call/waiting-room";
import { useCallSession } from "@/hooks/use-call-session";
import { resolveLiveKitUrl } from "@/lib/livekit-url";

function CallPageContent() {
  const params = useParams<{ meetingId: string }>();
  const { state, submitPassword } = useCallSession(params.meetingId);

  if (state.phase === "joining") {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#0b0b0c]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/15 border-t-white/70" />
      </div>
    );
  }

  if (state.phase === "needs-password") {
    return <PasswordPrompt error={state.error} onSubmit={submitPassword} />;
  }

  if (state.phase === "waiting") {
    return <WaitingRoom meeting={state.response.meeting} />;
  }

  if (state.phase === "error") {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center gap-3 bg-[#0b0b0c] text-white">
        <p className="text-[16px] font-medium">Couldn&apos;t join this meeting</p>
        <p className="text-[13.5px] text-white/50">{state.message}</p>
      </div>
    );
  }

  const { token, meeting } = state.response;
  if (!token) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#0b0b0c] text-white/60">
        Missing access token.
      </div>
    );
  }

  return <CallRoom serverUrl={resolveLiveKitUrl()} token={token} meeting={meeting} />;
}

export default function CallPage() {
  return (
    <AuthGuard>
      <CallPageContent />
    </AuthGuard>
  );
}
