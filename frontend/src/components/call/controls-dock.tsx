"use client";

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
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { PanelTab } from "@/components/call/side-panel";

function DockButton({
  active,
  toggledOff,
  onClick,
  children,
  label,
}: {
  active?: boolean;
  toggledOff?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      className={cn(
        "relative flex h-12 w-12 items-center justify-center rounded-full transition-all duration-200",
        toggledOff
          ? "bg-white text-[#111113] hover:bg-white/90"
          : active
            ? "bg-[#111113] text-white"
            : "bg-white/[0.08] text-white/85 hover:bg-white/[0.14]"
      )}
    >
      {children}
    </button>
  );
}

export function ControlsDock({
  micOn,
  cameraOn,
  screenSharing,
  activePanel,
  onToggleMic,
  onToggleCamera,
  onToggleScreenShare,
  onTogglePanel,
  onLeave,
}: {
  micOn: boolean;
  cameraOn: boolean;
  screenSharing: boolean;
  activePanel: PanelTab | null;
  onToggleMic: () => void;
  onToggleCamera: () => void;
  onToggleScreenShare: () => void;
  onTogglePanel: (tab: PanelTab) => void;
  onLeave: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut", delay: 0.1 }}
      className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-[#1c1c1e]/95 p-2 shadow-float backdrop-blur-md"
    >
      <DockButton label="Toggle microphone" toggledOff={!micOn} onClick={onToggleMic}>
        {micOn ? (
          <Mic className="h-[18px] w-[18px]" strokeWidth={1.9} />
        ) : (
          <MicOff className="h-[18px] w-[18px]" strokeWidth={1.9} />
        )}
      </DockButton>

      <DockButton label="Toggle camera" toggledOff={!cameraOn} onClick={onToggleCamera}>
        {cameraOn ? (
          <Video className="h-[18px] w-[18px]" strokeWidth={1.9} />
        ) : (
          <VideoOff className="h-[18px] w-[18px]" strokeWidth={1.9} />
        )}
      </DockButton>

      <DockButton label="Share screen" active={screenSharing} onClick={onToggleScreenShare}>
        <MonitorUp className="h-[18px] w-[18px]" strokeWidth={1.9} />
      </DockButton>

      <div className="mx-1 h-7 w-px bg-white/[0.08]" />

      <DockButton
        label="Participants"
        active={activePanel === "participants"}
        onClick={() => onTogglePanel("participants")}
      >
        <Users className="h-[18px] w-[18px]" strokeWidth={1.9} />
      </DockButton>

      <DockButton
        label="Chat"
        active={activePanel === "chat"}
        onClick={() => onTogglePanel("chat")}
      >
        <MessageSquare className="h-[18px] w-[18px]" strokeWidth={1.9} />
      </DockButton>

      <DockButton
        label="AI notes"
        active={activePanel === "notes"}
        onClick={() => onTogglePanel("notes")}
      >
        <Sparkles className="h-[18px] w-[18px]" strokeWidth={1.9} />
      </DockButton>

      <DockButton
        label="More"
        active={activePanel === "transcript"}
        onClick={() => onTogglePanel("transcript")}
      >
        <MoreHorizontal className="h-[18px] w-[18px]" strokeWidth={1.9} />
      </DockButton>

      <div className="mx-1 h-7 w-px bg-white/[0.08]" />

      <button
        onClick={onLeave}
        aria-label="Leave call"
        className="flex h-12 items-center gap-2 rounded-full bg-[#d4493c] px-4 text-[13.5px] font-medium text-white transition-colors duration-200 hover:bg-[#c23f33]"
      >
        <PhoneOff className="h-[17px] w-[17px]" strokeWidth={2} />
        Leave
      </button>
    </motion.div>
  );
}
