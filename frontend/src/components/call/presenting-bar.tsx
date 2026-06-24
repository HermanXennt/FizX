"use client";

import { MonitorUp } from "lucide-react";

export function PresentingBar({ onStop }: { onStop: () => void }) {
  return (
    <div className="flex items-center justify-center">
      <div className="flex items-center gap-3 rounded-full border border-white/[0.08] bg-[#1c1c1e]/95 px-4 py-2 text-[13px] text-white/85 shadow-float backdrop-blur-md">
        <span className="flex items-center gap-1.5 text-emerald-400">
          <MonitorUp className="h-3.5 w-3.5" strokeWidth={2} />
          You&apos;re presenting your screen
        </span>
        <button
          onClick={onStop}
          className="rounded-full bg-white/[0.1] px-3 py-1 text-[12px] font-medium text-white hover:bg-white/[0.16]"
        >
          Stop presenting
        </button>
      </div>
    </div>
  );
}
