"use client";

import { LiveKitRoom, RoomAudioRenderer, useLocalParticipant } from "@livekit/components-react";
import { MediaDeviceFailure } from "livekit-client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ControlsDock } from "@/components/call/controls-dock";
import { EnableAudioOverlay } from "@/components/call/enable-audio-overlay";
import { MediaErrorBanner } from "@/components/call/media-error-banner";
import { ParticipantGrid } from "@/components/call/participant-grid";
import { CallTopbar } from "@/components/call/call-topbar";
import { SidePanel, type PanelTab } from "@/components/call/side-panel";
import { useIceServers } from "@/hooks/use-meetings";
import { meetingService } from "@/services/meeting-service";
import { useAuthStore } from "@/store/auth-store";
import type { Meeting } from "@/types/meeting";

function CallShell({
  meeting,
  onLeave,
  mediaError,
  onDismissMediaError,
}: {
  meeting: Meeting;
  onLeave: () => void;
  mediaError: MediaDeviceFailure | null;
  onDismissMediaError: () => void;
}) {
  const { localParticipant, isMicrophoneEnabled, isCameraEnabled, isScreenShareEnabled } = useLocalParticipant();
  const [activePanel, setActivePanel] = useState<PanelTab | null>(null);
  const currentUserId = useAuthStore((s) => s.user?.id);
  const isHost = currentUserId === meeting.host.id;
  const [startedAt] = useState(() =>
    meeting.actual_start ? new Date(meeting.actual_start).getTime() : Date.now()
  );

  return (
    <div className="relative flex h-screen w-screen flex-col gap-2 overflow-hidden bg-[#0b0b0c] p-2 sm:gap-4 sm:p-5">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.5]"
        style={{
          backgroundImage:
            "radial-gradient(circle at 15% 0%, rgba(255,255,255,0.05) 0%, transparent 45%), radial-gradient(circle at 85% 100%, rgba(255,255,255,0.04) 0%, transparent 45%)",
        }}
      />

      {mediaError && <MediaErrorBanner failure={mediaError} onDismiss={onDismissMediaError} />}

      <CallTopbar title={meeting.title} startedAt={startedAt} />

      <div className="relative flex min-h-0 flex-1 gap-2 sm:gap-4">
        <div className="min-w-0 flex-1">
          <ParticipantGrid panelOpen={activePanel !== null} hostIdentity={meeting.host.id} />
        </div>

        <SidePanel
          tab={activePanel}
          onChangeTab={setActivePanel}
          onClose={() => setActivePanel(null)}
          meetingId={meeting.id}
          isHost={isHost}
        />
      </div>

      <div className="flex justify-center">
        <ControlsDock
          micOn={isMicrophoneEnabled}
          cameraOn={isCameraEnabled}
          screenSharing={isScreenShareEnabled}
          activePanel={activePanel}
          onToggleMic={() => localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled)}
          onToggleCamera={() => localParticipant.setCameraEnabled(!isCameraEnabled)}
          onToggleScreenShare={() => localParticipant.setScreenShareEnabled(!isScreenShareEnabled)}
          onTogglePanel={(tab) => setActivePanel((current) => (current === tab ? null : tab))}
          onLeave={onLeave}
        />
      </div>
    </div>
  );
}

export function CallRoom({
  serverUrl,
  token,
  meeting,
}: {
  serverUrl: string;
  token: string;
  meeting: Meeting;
}) {
  const router = useRouter();
  const { data: iceServers, isLoading: iceServersLoading } = useIceServers();
  const [mediaError, setMediaError] = useState<MediaDeviceFailure | null>(null);

  async function handleLeave() {
    try {
      await meetingService.leave(meeting.id);
    } catch {
      // already left or meeting ended server-side - not fatal, still navigate away
    }
    router.push("/");
  }

  if (iceServersLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#0b0b0c]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/15 border-t-white/70" />
      </div>
    );
  }

  return (
    <LiveKitRoom
      serverUrl={serverUrl}
      token={token}
      video
      audio
      connect
      // Falls back to relaying through coturn (TURN) when a direct UDP path
      // between peers is unreliable - restrictive NAT, carrier-grade NAT on
      // mobile networks, etc. Without this, LiveKit only offers its own host
      // candidates, and a flaky direct path shows up as periodic disconnects.
      connectOptions={iceServers ? { rtcConfig: { iceServers } } : undefined}
      onDisconnected={() => router.push("/")}
      onMediaDeviceFailure={(failure) => failure && setMediaError(failure)}
    >
      <RoomAudioRenderer />
      <EnableAudioOverlay />
      <CallShell
        meeting={meeting}
        onLeave={handleLeave}
        mediaError={mediaError}
        onDismissMediaError={() => setMediaError(null)}
      />
    </LiveKitRoom>
  );
}
