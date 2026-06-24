"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  useDataChannel,
  useIsSpeaking,
  useLocalParticipant,
  useLocalParticipantPermissions,
} from "@livekit/components-react";
import { TrackSource } from "@livekit/protocol";
import { MediaDeviceFailure } from "livekit-client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ControlsDock } from "@/components/call/controls-dock";
import { EnableAudioOverlay } from "@/components/call/enable-audio-overlay";
import { MediaErrorBanner } from "@/components/call/media-error-banner";
import { NoticeBanner } from "@/components/call/notice-banner";
import { ParticipantGrid } from "@/components/call/participant-grid";
import { PresentingBar } from "@/components/call/presenting-bar";
import { CallTopbar } from "@/components/call/call-topbar";
import { SidePanel, type PanelTab } from "@/components/call/side-panel";
import { useIceServers, useMarkSpoken } from "@/hooks/use-meetings";
import { useMeetingRecordings, useStartRecording, useStopRecording } from "@/hooks/use-recordings";
import { meetingService } from "@/services/meeting-service";
import { useAuthStore } from "@/store/auth-store";
import type { Meeting } from "@/types/meeting";

function isSourceLocked(sources: TrackSource[] | undefined, source: TrackSource): boolean {
  if (!sources || sources.length === 0) return false; // empty allow-list = unrestricted
  return !sources.includes(source);
}

function CallShell({
  meeting,
  onLeave,
  onEndMeeting,
  mediaError,
  onDismissMediaError,
}: {
  meeting: Meeting;
  onLeave: () => void;
  onEndMeeting: () => void;
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

  // One-shot: the first time this device's mic actually triggers an
  // active-speaker event, tell the backend so the AI assistant can answer
  // "who hasn't spoken yet" with real data instead of guessing.
  const isSpeaking = useIsSpeaking(localParticipant);
  const markSpoken = useMarkSpoken(meeting.id);
  const hasReportedSpoken = useRef(false);
  useEffect(() => {
    if (isSpeaking && !hasReportedSpoken.current) {
      hasReportedSpoken.current = true;
      markSpoken.mutate();
    }
  }, [isSpeaking, markSpoken]);

  const { data: recordings } = useMeetingRecordings(meeting.id);
  const activeRecording = recordings?.find((r) => r.status === "processing");
  const startRecording = useStartRecording(meeting.id);
  const stopRecording = useStopRecording(meeting.id);
  const recordingPending = startRecording.isPending || stopRecording.isPending;

  function handleToggleRecording() {
    if (activeRecording) {
      stopRecording.mutate(activeRecording.id);
    } else {
      startRecording.mutate();
    }
  }

  // The host can revoke a participant's permission to publish camera/mic
  // (apps/meetings/services.py set_participant_media) - enforced server-side
  // by LiveKit, not a client convention, so this reflects the real state.
  const permissions = useLocalParticipantPermissions();
  const micLocked = isSourceLocked(permissions?.canPublishSources, TrackSource.MICROPHONE);
  const cameraLocked = isSourceLocked(permissions?.canPublishSources, TrackSource.CAMERA);

  const [hostNotice, setHostNotice] = useState<string | null>(null);
  useDataChannel("meeting-events", (msg) => {
    try {
      const event = JSON.parse(new TextDecoder().decode(msg.payload));
      if (event.event === "muted_by_host") {
        setHostNotice("You were muted by the host.");
      } else if (event.event === "media_permissions_changed") {
        const disabled = [
          !event.mic_enabled && "microphone",
          !event.camera_enabled && "camera",
        ].filter(Boolean);
        setHostNotice(
          disabled.length > 0
            ? `Your ${disabled.join(" and ")} ${disabled.length > 1 ? "have" : "has"} been disabled by the host.`
            : "The host restored your microphone and camera access."
        );
      }
    } catch {
      // ignore malformed payloads
    }
  });

  const [screenShareError, setScreenShareError] = useState<string | null>(null);
  async function handleToggleScreenShare() {
    if (isScreenShareEnabled) {
      await localParticipant.setScreenShareEnabled(false);
      return;
    }
    try {
      await localParticipant.setScreenShareEnabled(true, {
        audio: true,
        systemAudio: "include",
        surfaceSwitching: "include",
        selfBrowserSurface: "exclude",
        contentHint: "detail",
      });
    } catch (err) {
      const name = err instanceof Error ? err.name : "";
      if (name === "NotAllowedError" || name === "AbortError") return; // user cancelled the picker
      setScreenShareError("Couldn't start screen sharing. Check your browser/OS permissions and try again.");
    }
  }

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
      {!mediaError && screenShareError && (
        <NoticeBanner message={screenShareError} onDismiss={() => setScreenShareError(null)} />
      )}
      {!mediaError && !screenShareError && hostNotice && (
        <NoticeBanner message={hostNotice} onDismiss={() => setHostNotice(null)} />
      )}

      <CallTopbar title={meeting.title} startedAt={startedAt} isRecording={Boolean(activeRecording)} />

      {isScreenShareEnabled && <PresentingBar onStop={handleToggleScreenShare} />}

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
          micLocked={micLocked}
          cameraLocked={cameraLocked}
          screenSharing={isScreenShareEnabled}
          activePanel={activePanel}
          onToggleMic={() => !micLocked && localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled)}
          onToggleCamera={() => !cameraLocked && localParticipant.setCameraEnabled(!isCameraEnabled)}
          onToggleScreenShare={handleToggleScreenShare}
          onTogglePanel={(tab) => setActivePanel((current) => (current === tab ? null : tab))}
          onLeave={onLeave}
          onEndMeeting={onEndMeeting}
          isHost={isHost}
          isRecording={Boolean(activeRecording)}
          recordingPending={recordingPending}
          onToggleRecording={handleToggleRecording}
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
  const hasSyncedPermissions = useRef(false);

  function handleConnected() {
    // Re-applies any mic/camera lock the host already set for this
    // participant - covers the reconnect/refresh case in case the JWT-level
    // grant (best-effort, see livekit/service.py) didn't already cover it.
    if (!hasSyncedPermissions.current) {
      hasSyncedPermissions.current = true;
      meetingService.syncPermissions(meeting.id).catch(() => {});
    }
  }

  async function handleLeave() {
    try {
      await meetingService.leave(meeting.id);
    } catch {
      // already left or meeting ended server-side - not fatal, still navigate away
    }
    router.push("/");
  }

  async function handleEndMeeting() {
    try {
      await meetingService.end(meeting.id);
    } catch {
      // already ended server-side - not fatal, still navigate away
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
      onConnected={handleConnected}
      onDisconnected={() => router.push("/")}
      onMediaDeviceFailure={(failure) => failure && setMediaError(failure)}
    >
      <RoomAudioRenderer />
      <EnableAudioOverlay />
      <CallShell
        meeting={meeting}
        onLeave={handleLeave}
        onEndMeeting={handleEndMeeting}
        mediaError={mediaError}
        onDismissMediaError={() => setMediaError(null)}
      />
    </LiveKitRoom>
  );
}
