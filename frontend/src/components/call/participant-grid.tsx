"use client";

import { useTracks, VideoTrack } from "@livekit/components-react";
import { Track } from "livekit-client";
import { motion } from "framer-motion";
import { MonitorUp } from "lucide-react";
import { useState } from "react";
import { VideoTile } from "@/components/call/video-tile";
import { cn } from "@/lib/utils";

const gridCols: Record<number, string> = {
  1: "grid-cols-1",
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 sm:grid-cols-2",
  5: "grid-cols-2 sm:grid-cols-3",
  6: "grid-cols-2 sm:grid-cols-3",
};

function ThumbnailRail({
  tracks,
  hostIdentity,
  pinnedIdentity,
  onSelect,
  compactWidth,
}: {
  tracks: ReturnType<typeof useTracks>;
  hostIdentity?: string;
  pinnedIdentity: string | null;
  onSelect: (identity: string) => void;
  compactWidth: boolean;
}) {
  return (
    <div
      className={cn(
        "flex shrink-0 gap-3 overflow-x-auto overflow-y-hidden scrollbar-none",
        "flex-row sm:flex-col sm:overflow-x-hidden sm:overflow-y-auto",
        compactWidth ? "sm:w-[140px]" : "sm:w-[180px]"
      )}
    >
      {tracks.map((trackRef) => (
        <VideoTile
          key={trackRef.participant.identity}
          trackRef={trackRef}
          isHost={trackRef.participant.identity === hostIdentity}
          pinned={trackRef.participant.identity === pinnedIdentity}
          onClick={() => onSelect(trackRef.participant.identity)}
          compact
          className="aspect-video h-24 shrink-0 sm:h-auto sm:w-full"
        />
      ))}
    </div>
  );
}

export function ParticipantGrid({
  panelOpen,
  hostIdentity,
}: {
  panelOpen: boolean;
  hostIdentity?: string;
}) {
  const cameraTracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: true }], {
    onlySubscribed: false,
  });
  const screenShareTracks = useTracks([Track.Source.ScreenShare], { onlySubscribed: false });
  // If the pinned participant leaves, lookups below simply stop matching and
  // the view falls back to the grid on its own - no need to clear this.
  const [pinnedIdentity, setPinnedIdentity] = useState<string | null>(null);

  function togglePin(identity: string) {
    setPinnedIdentity((current) => (current === identity ? null : identity));
  }

  if (screenShareTracks.length > 0) {
    const presenterTrack = screenShareTracks[0];

    return (
      <div className="flex h-full w-full flex-col gap-4 sm:flex-row">
        <motion.div
          layout
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="relative min-h-0 flex-1 overflow-hidden rounded-3xl border border-white/[0.06] bg-[#161618]"
        >
          <VideoTrack trackRef={presenterTrack} playsInline className="h-full w-full object-contain" />
          <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-black/40 px-3 py-1.5 text-[12px] font-medium text-white/80 backdrop-blur-sm">
            <MonitorUp className="h-3.5 w-3.5" />
            {presenterTrack.participant.name || "Someone"} is presenting
          </div>
        </motion.div>

        <ThumbnailRail
          tracks={cameraTracks}
          hostIdentity={hostIdentity}
          pinnedIdentity={null}
          onSelect={() => {}}
          compactWidth={panelOpen}
        />
      </div>
    );
  }

  const pinnedTrack = cameraTracks.find((t) => t.participant.identity === pinnedIdentity);

  if (pinnedTrack) {
    const others = cameraTracks.filter((t) => t.participant.identity !== pinnedIdentity);

    return (
      <div className="flex h-full w-full flex-col gap-4 sm:flex-row">
        <div className="min-h-0 flex-1">
          <VideoTile
            trackRef={pinnedTrack}
            isHost={pinnedTrack.participant.identity === hostIdentity}
            pinned
            onClick={() => togglePin(pinnedTrack.participant.identity)}
            className="h-full w-full"
          />
        </div>

        {others.length > 0 && (
          <ThumbnailRail
            tracks={others}
            hostIdentity={hostIdentity}
            pinnedIdentity={pinnedIdentity}
            onSelect={togglePin}
            compactWidth={panelOpen}
          />
        )}
      </div>
    );
  }

  const count = Math.min(cameraTracks.length, 6) || 1;

  return (
    <div className={cn("grid h-full w-full auto-rows-fr gap-4", gridCols[count] ?? "grid-cols-3")}>
      {cameraTracks.map((trackRef) => (
        <VideoTile
          key={trackRef.participant.identity}
          trackRef={trackRef}
          isHost={trackRef.participant.identity === hostIdentity}
          onClick={cameraTracks.length > 1 ? () => togglePin(trackRef.participant.identity) : undefined}
          className="h-full w-full"
        />
      ))}
    </div>
  );
}
