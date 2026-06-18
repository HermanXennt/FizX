"use client";

import { useTracks, VideoTrack } from "@livekit/components-react";
import { Track } from "livekit-client";
import { motion } from "framer-motion";
import { MonitorUp } from "lucide-react";
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

  if (screenShareTracks.length > 0) {
    const presenterTrack = screenShareTracks[0];

    return (
      <div className="flex h-full w-full gap-4">
        <motion.div
          layout
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="relative flex flex-1 items-center justify-center overflow-hidden rounded-3xl border border-white/[0.06] bg-[#161618]"
        >
          <VideoTrack trackRef={presenterTrack} className="h-full w-full object-contain" />
          <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-black/40 px-3 py-1.5 text-[12px] font-medium text-white/80 backdrop-blur-sm">
            <MonitorUp className="h-3.5 w-3.5" />
            {presenterTrack.participant.name || "Someone"} is presenting
          </div>
        </motion.div>

        <div
          className={cn(
            "flex shrink-0 flex-col gap-3 overflow-y-auto scrollbar-none",
            panelOpen ? "w-[140px]" : "w-[180px]"
          )}
        >
          {cameraTracks.map((trackRef) => (
            <VideoTile
              key={trackRef.participant.identity}
              trackRef={trackRef}
              isHost={trackRef.participant.identity === hostIdentity}
              compact
              className="aspect-video w-full shrink-0"
            />
          ))}
        </div>
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
          className="aspect-video w-full"
        />
      ))}
    </div>
  );
}
