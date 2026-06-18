"use client";

import { isTrackReference, VideoTrack, type TrackReferenceOrPlaceholder } from "@livekit/components-react";
import { motion } from "framer-motion";
import { Mic, MicOff, Pin } from "lucide-react";
import { stableColor } from "@/lib/avatar";
import { cn } from "@/lib/utils";

function initialsFor(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function VideoTile({
  trackRef,
  isHost = false,
  className,
  compact = false,
}: {
  trackRef: TrackReferenceOrPlaceholder;
  isHost?: boolean;
  className?: string;
  compact?: boolean;
}) {
  const participant = trackRef.participant;
  const displayName = participant.name || "Guest";
  const initials = initialsFor(displayName);
  const color = stableColor(participant.identity);
  const hasVideo = isTrackReference(trackRef) && !trackRef.publication.isMuted;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn(
        "group relative flex items-center justify-center overflow-hidden rounded-3xl border",
        participant.isSpeaking
          ? "border-white/40 shadow-[0_0_0_3px_rgba(255,255,255,0.08)]"
          : "border-white/[0.06]",
        className
      )}
      style={{ background: `linear-gradient(155deg, ${color} 0%, #0c0c0d 130%)` }}
    >
      <div className="pointer-events-none absolute inset-0 bg-black/10" />

      {hasVideo ? (
        <VideoTrack trackRef={trackRef} className="h-full w-full object-cover" />
      ) : (
        <div
          className={cn(
            "flex items-center justify-center rounded-full font-semibold text-white/90",
            compact ? "h-10 w-10 text-[13px]" : "h-20 w-20 text-[26px]"
          )}
          style={{ backgroundColor: "rgba(255,255,255,0.12)" }}
        >
          {initials}
        </div>
      )}

      {participant.isSpeaking && (
        <motion.div
          className="pointer-events-none absolute inset-0 rounded-3xl"
          animate={{ opacity: [0.5, 0.15, 0.5] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          style={{ boxShadow: "inset 0 0 0 2px rgba(255,255,255,0.55)" }}
        />
      )}

      <div className="absolute left-3 top-3 flex items-center gap-1.5">
        {isHost && (
          <span className="rounded-full bg-black/40 px-2 py-0.5 text-[10.5px] font-medium text-white/80 backdrop-blur-sm">
            Host
          </span>
        )}
      </div>

      <button className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-black/30 text-white/0 opacity-0 backdrop-blur-sm transition-opacity duration-200 group-hover:text-white/80 group-hover:opacity-100">
        <Pin className="h-3.5 w-3.5" strokeWidth={2} />
      </button>

      <div className="absolute bottom-3 left-3 flex items-center gap-1.5 rounded-full bg-black/35 px-2.5 py-1 backdrop-blur-sm">
        {participant.isMicrophoneEnabled ? (
          <Mic className="h-3 w-3 text-white/70" strokeWidth={2} />
        ) : (
          <MicOff className="h-3 w-3 text-white/70" strokeWidth={2} />
        )}
        <span className={cn("font-medium text-white/85", compact ? "text-[11px]" : "text-[12.5px]")}>
          {displayName}
        </span>
      </div>
    </motion.div>
  );
}
