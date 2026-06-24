"use client";

import { AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export function NoticeBanner({
  message,
  tone = "warning",
  onDismiss,
}: {
  message: string;
  tone?: "warning" | "info";
  onDismiss: () => void;
}) {
  return (
    <div
      className={cn(
        "absolute inset-x-3 top-3 z-50 flex items-start gap-2.5 rounded-2xl border px-4 py-3 shadow-float sm:inset-x-auto sm:left-1/2 sm:top-4 sm:w-[420px] sm:-translate-x-1/2",
        tone === "warning" ? "border-amber-400/20 bg-[#26211a] text-amber-100" : "border-white/10 bg-[#1c1c1e] text-white/85"
      )}
    >
      {tone === "warning" ? (
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} />
      ) : (
        <Info className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} />
      )}
      <p className="flex-1 text-[13px] leading-snug">{message}</p>
      <button
        onClick={onDismiss}
        className={cn(
          "shrink-0 rounded-full p-0.5",
          tone === "warning" ? "text-amber-100/60 hover:text-amber-100" : "text-white/50 hover:text-white"
        )}
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
