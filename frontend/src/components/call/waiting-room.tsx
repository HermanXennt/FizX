"use client";

import { useRouter } from "next/navigation";
import { Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Meeting } from "@/types/meeting";

export function WaitingRoom({ meeting }: { meeting: Meeting }) {
  const router = useRouter();

  return (
    <div className="flex h-screen w-screen flex-col items-center justify-center gap-5 bg-[#0b0b0c] px-6 text-white">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/[0.06]">
        <Clock className="h-6 w-6 text-white/70" strokeWidth={1.8} />
      </div>
      <div className="text-center">
        <h1 className="text-[19px] font-semibold">Waiting for the host to let you in</h1>
        <p className="mt-1.5 text-[14px] text-white/50">{meeting.title}</p>
      </div>
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white/40" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-white/60" />
      </span>
      <Button
        variant="outline"
        onClick={() => router.push("/")}
        className="mt-2 h-10 rounded-full border-white/15 bg-transparent text-white hover:bg-white/[0.08]"
      >
        Leave
      </Button>
    </div>
  );
}
