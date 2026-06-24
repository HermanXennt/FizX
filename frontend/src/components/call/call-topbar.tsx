"use client";

import { useParticipants } from "@livekit/components-react";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Minimize2 } from "lucide-react";
import Link from "next/link";
import { AvatarStack } from "@/components/dashboard/avatar-stack";

function formatElapsed(startedAt: number) {
  const seconds = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export function CallTopbar({
  title,
  startedAt,
  isRecording,
}: {
  title: string;
  startedAt: number;
  isRecording?: boolean;
}) {
  const participants = useParticipants();
  const [elapsed, setElapsed] = useState(() => formatElapsed(startedAt));

  useEffect(() => {
    const id = setInterval(() => setElapsed(formatElapsed(startedAt)), 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex items-center justify-between gap-2"
    >
      <div className="flex min-w-0 items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.06] px-3 py-2 text-white backdrop-blur-md sm:gap-3 sm:px-4">
        <span className="relative flex h-1.5 w-1.5 shrink-0">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500 opacity-75" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-red-500" />
        </span>
        <p className="min-w-0 truncate text-[13px] font-medium sm:text-[13.5px]">{title}</p>
        <span className="h-3.5 w-px shrink-0 bg-white/15" />
        <p className="shrink-0 text-[13px] tabular-nums text-white/55">{elapsed}</p>
        {isRecording && (
          <>
            <span className="h-3.5 w-px shrink-0 bg-white/15" />
            <span className="flex shrink-0 items-center gap-1.5 text-[12px] font-medium text-[#ff6b5e]">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#ff6b5e]" />
              REC
            </span>
          </>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <div className="hidden rounded-full border border-white/[0.08] bg-white/[0.06] px-3 py-2 backdrop-blur-md sm:block">
          <AvatarStack
            people={participants.map((p) => ({
              id: p.identity,
              initials: (p.name || "?").slice(0, 2).toUpperCase(),
            }))}
            size={26}
            max={4}
          />
        </div>
        <Link
          href="/"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.06] text-white/80 backdrop-blur-md transition-colors hover:bg-white/[0.12] hover:text-white sm:h-10 sm:w-10"
        >
          <Minimize2 className="h-[16px] w-[16px]" strokeWidth={1.9} />
        </Link>
      </div>
    </motion.div>
  );
}
