"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  MonitorUp,
  Users,
  MessageSquare,
  Sparkles,
  MoreHorizontal,
  PhoneOff,
  Circle,
  Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { PanelTab } from "@/components/call/side-panel";

function DockButton({
  active,
  toggledOff,
  disabled,
  locked,
  onClick,
  children,
  label,
  className,
}: {
  active?: boolean;
  toggledOff?: boolean;
  disabled?: boolean;
  locked?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  label: string;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={cn(
        "relative flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40 sm:h-12 sm:w-12",
        toggledOff
          ? "bg-white text-[#111113] hover:bg-white/90"
          : active
            ? "bg-[#111113] text-white"
            : "bg-white/[0.08] text-white/85 hover:bg-white/[0.14]",
        className
      )}
    >
      {children}
      {locked && (
        <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#d4493c] text-white">
          <Lock className="h-2.5 w-2.5" strokeWidth={2.5} />
        </span>
      )}
    </button>
  );
}

function MoreMenuRow({
  active,
  disabled,
  onClick,
  icon,
  label,
}: {
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-[13.5px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40",
        active ? "bg-white text-[#111113]" : "text-white/85 hover:bg-white/[0.08]"
      )}
    >
      {icon}
      {label}
    </button>
  );
}

export function ControlsDock({
  micOn,
  cameraOn,
  micLocked,
  cameraLocked,
  screenSharing,
  activePanel,
  onToggleMic,
  onToggleCamera,
  onToggleScreenShare,
  onTogglePanel,
  onLeave,
  onEndMeeting,
  isHost,
  isRecording,
  recordingPending,
  onToggleRecording,
}: {
  micOn: boolean;
  cameraOn: boolean;
  micLocked?: boolean;
  cameraLocked?: boolean;
  screenSharing: boolean;
  activePanel: PanelTab | null;
  onToggleMic: () => void;
  onToggleCamera: () => void;
  onToggleScreenShare: () => void;
  onTogglePanel: (tab: PanelTab) => void;
  onLeave: () => void;
  onEndMeeting?: () => void;
  isHost?: boolean;
  isRecording?: boolean;
  recordingPending?: boolean;
  onToggleRecording?: () => void;
}) {
  const [moreOpen, setMoreOpen] = useState(false);
  const [leaveMenuOpen, setLeaveMenuOpen] = useState(false);

  // LiveKit's egress pipeline takes a few seconds to actually start after
  // the API call returns - stopping before that lands fails with "Start
  // signal not received" instead of producing a (very short) recording.
  const [justStarted, setJustStarted] = useState(false);
  const wasRecording = useRef(false);
  useEffect(() => {
    if (isRecording && !wasRecording.current) {
      setJustStarted(true);
      const timer = setTimeout(() => setJustStarted(false), 5000);
      wasRecording.current = true;
      return () => clearTimeout(timer);
    }
    if (!isRecording) {
      wasRecording.current = false;
    }
  }, [isRecording]);
  const recordingLocked = Boolean(recordingPending) || (Boolean(isRecording) && justStarted);

  function selectFromMore(action: () => void) {
    action();
    setMoreOpen(false);
  }

  return (
    <div className="relative flex justify-center">
      {moreOpen && (
        <>
          <button
            aria-label="Close menu"
            onClick={() => setMoreOpen(false)}
            className="fixed inset-0 z-40 sm:hidden"
          />
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="absolute bottom-full z-50 mb-3 flex w-56 flex-col gap-0.5 rounded-2xl border border-white/[0.08] bg-[#1c1c1e] p-1.5 shadow-float sm:hidden"
          >
            <MoreMenuRow
              active={screenSharing}
              onClick={() => selectFromMore(onToggleScreenShare)}
              icon={<MonitorUp className="h-4 w-4" strokeWidth={1.9} />}
              label={screenSharing ? "Stop sharing" : "Share screen"}
            />
            {isHost && onToggleRecording && (
              <MoreMenuRow
                active={isRecording}
                disabled={recordingLocked}
                onClick={() => selectFromMore(onToggleRecording)}
                icon={<Circle className="h-4 w-4" strokeWidth={1.9} fill={isRecording ? "#d4493c" : "none"} />}
                label={isRecording ? (justStarted ? "Starting…" : "Stop recording") : "Start recording"}
              />
            )}
            <MoreMenuRow
              active={activePanel === "participants"}
              onClick={() => selectFromMore(() => onTogglePanel("participants"))}
              icon={<Users className="h-4 w-4" strokeWidth={1.9} />}
              label="Participants"
            />
            <MoreMenuRow
              active={activePanel === "chat"}
              onClick={() => selectFromMore(() => onTogglePanel("chat"))}
              icon={<MessageSquare className="h-4 w-4" strokeWidth={1.9} />}
              label="Chat"
            />
            <MoreMenuRow
              active={activePanel === "notes"}
              onClick={() => selectFromMore(() => onTogglePanel("notes"))}
              icon={<Sparkles className="h-4 w-4" strokeWidth={1.9} />}
              label="AI Notes"
            />
            <MoreMenuRow
              active={activePanel === "transcript"}
              onClick={() => selectFromMore(() => onTogglePanel("transcript"))}
              icon={<MoreHorizontal className="h-4 w-4" strokeWidth={1.9} />}
              label="Transcript"
            />
          </motion.div>
        </>
      )}

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut", delay: 0.1 }}
        className="flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-[#1c1c1e]/95 p-1.5 shadow-float backdrop-blur-md sm:gap-2 sm:p-2"
      >
        <DockButton
          label={micLocked ? "Microphone disabled by host" : "Toggle microphone"}
          toggledOff={!micOn}
          disabled={micLocked}
          locked={micLocked}
          onClick={onToggleMic}
        >
          {micOn ? (
            <Mic className="h-[18px] w-[18px]" strokeWidth={1.9} />
          ) : (
            <MicOff className="h-[18px] w-[18px]" strokeWidth={1.9} />
          )}
        </DockButton>

        <DockButton
          label={cameraLocked ? "Camera disabled by host" : "Toggle camera"}
          toggledOff={!cameraOn}
          disabled={cameraLocked}
          locked={cameraLocked}
          onClick={onToggleCamera}
        >
          {cameraOn ? (
            <Video className="h-[18px] w-[18px]" strokeWidth={1.9} />
          ) : (
            <VideoOff className="h-[18px] w-[18px]" strokeWidth={1.9} />
          )}
        </DockButton>

        {/* Collapsed into the "more" menu below sm; shown inline at sm and up. */}
        <div className="hidden items-center gap-2 sm:flex">
          <DockButton label="Share screen" active={screenSharing} onClick={onToggleScreenShare}>
            <MonitorUp className="h-[18px] w-[18px]" strokeWidth={1.9} />
          </DockButton>

          {isHost && onToggleRecording && (
            <DockButton
              label={isRecording ? (justStarted ? "Starting…" : "Stop recording") : "Start recording"}
              active={isRecording}
              disabled={recordingLocked}
              onClick={onToggleRecording}
              className={isRecording ? "bg-[#d4493c]/90 text-white" : undefined}
            >
              <Circle className="h-[18px] w-[18px]" strokeWidth={1.9} fill={isRecording ? "currentColor" : "none"} />
            </DockButton>
          )}

          <div className="mx-1 h-7 w-px bg-white/[0.08]" />

          <DockButton
            label="Participants"
            active={activePanel === "participants"}
            onClick={() => onTogglePanel("participants")}
          >
            <Users className="h-[18px] w-[18px]" strokeWidth={1.9} />
          </DockButton>

          <DockButton label="Chat" active={activePanel === "chat"} onClick={() => onTogglePanel("chat")}>
            <MessageSquare className="h-[18px] w-[18px]" strokeWidth={1.9} />
          </DockButton>

          <DockButton label="AI notes" active={activePanel === "notes"} onClick={() => onTogglePanel("notes")}>
            <Sparkles className="h-[18px] w-[18px]" strokeWidth={1.9} />
          </DockButton>

          <DockButton
            label="Transcript"
            active={activePanel === "transcript"}
            onClick={() => onTogglePanel("transcript")}
          >
            <MoreHorizontal className="h-[18px] w-[18px]" strokeWidth={1.9} />
          </DockButton>

          <div className="mx-1 h-7 w-px bg-white/[0.08]" />
        </div>

        <DockButton
          label="More"
          active={moreOpen}
          onClick={() => setMoreOpen((o) => !o)}
          className="sm:hidden"
        >
          <MoreHorizontal className="h-[18px] w-[18px]" strokeWidth={1.9} />
        </DockButton>

        <div className="relative">
          {isHost && onEndMeeting && leaveMenuOpen && (
            <>
              <button
                aria-label="Close menu"
                onClick={() => setLeaveMenuOpen(false)}
                className="fixed inset-0 z-40"
              />
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                className="absolute bottom-full right-0 z-50 mb-3 flex w-60 flex-col gap-0.5 rounded-2xl border border-white/[0.08] bg-[#1c1c1e] p-1.5 shadow-float"
              >
                <MoreMenuRow
                  onClick={() => {
                    setLeaveMenuOpen(false);
                    onEndMeeting();
                  }}
                  icon={<PhoneOff className="h-4 w-4" strokeWidth={1.9} />}
                  label="End meeting for everyone"
                />
                <MoreMenuRow
                  onClick={() => {
                    setLeaveMenuOpen(false);
                    onLeave();
                  }}
                  icon={<PhoneOff className="h-4 w-4" strokeWidth={1.9} />}
                  label="Leave (others stay in the call)"
                />
              </motion.div>
            </>
          )}

          <button
            onClick={() => (isHost && onEndMeeting ? setLeaveMenuOpen((o) => !o) : onLeave())}
            aria-label={isHost && onEndMeeting ? "Leave or end call" : "Leave call"}
            className="flex h-11 items-center gap-2 rounded-full bg-[#d4493c] px-3 text-[13px] font-medium text-white transition-colors duration-200 hover:bg-[#c23f33] sm:h-12 sm:px-4 sm:text-[13.5px]"
          >
            <PhoneOff className="h-[17px] w-[17px]" strokeWidth={2} />
            <span className="hidden sm:inline">Leave</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}
