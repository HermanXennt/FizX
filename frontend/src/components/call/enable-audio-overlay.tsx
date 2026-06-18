"use client";

import { useStartAudio } from "@livekit/components-react";
import { Volume2 } from "lucide-react";

/**
 * Browsers (especially mobile Safari) block audio playback until a real
 * user gesture happens *after* the audio element exists - clicking "New
 * Meeting" doesn't count, because the remote participant's audio track
 * (and the <audio> element LiveKit creates for it) doesn't exist yet at
 * that point. Without this, calls connect and show video but stay silent.
 */
export function EnableAudioOverlay() {
  const { mergedProps, canPlayAudio } = useStartAudio({ props: {} });

  if (canPlayAudio) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <button
        onClick={mergedProps.onClick}
        className="flex items-center gap-2.5 rounded-full bg-white px-6 py-3.5 text-[14px] font-medium text-[#111113] shadow-float transition-transform hover:scale-105 active:scale-95"
      >
        <Volume2 className="h-[18px] w-[18px]" strokeWidth={2} />
        Tap to enable audio
      </button>
    </div>
  );
}
