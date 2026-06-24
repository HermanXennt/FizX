"use client";

import { motion } from "framer-motion";
import { PhoneOff, Plus, Video } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AvatarStack } from "@/components/dashboard/avatar-stack";
import { useCreateInstantMeeting, useEndMeeting, useMeetings } from "@/hooks/use-meetings";
import { useAuthStore } from "@/store/auth-store";

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const minutes = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return "Started just now";
  if (minutes === 1) return "Started 1 min ago";
  return `Started ${minutes} min ago`;
}

export function ActiveCallCard() {
  const user = useAuthStore((s) => s.user);
  const { data: liveMeetings } = useMeetings({ status: "live" });
  const createInstant = useCreateInstantMeeting();
  const endMeeting = useEndMeeting();
  const liveMeeting = liveMeetings?.[0];

  if (!liveMeeting) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="relative overflow-hidden rounded-[28px] bg-[#111113] p-6 sm:p-8 text-white shadow-soft-lg"
      >
        <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-[20px] font-semibold tracking-tight">No active calls right now</h3>
            <p className="mt-1 text-[14px] text-white/60">
              {user?.account_type === "teacher"
                ? "Start an instant meeting to get going."
                : "Your teacher hasn't started a call yet."}
            </p>
          </div>
          {user?.account_type === "teacher" && (
            <Button
              onClick={() => createInstant.mutate({})}
              disabled={createInstant.isPending}
              className="h-12 rounded-full bg-white px-6 text-[14px] font-medium text-[#111113] shadow-soft hover:bg-white/90"
            >
              <Plus className="h-4 w-4" strokeWidth={2.1} />
              {createInstant.isPending ? "Starting…" : "New Meeting"}
            </Button>
          )}
        </div>
      </motion.div>
    );
  }

  const isHost = user?.id === liveMeeting.host.id;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="relative overflow-hidden rounded-[28px] bg-[#111113] p-6 sm:p-8 text-white shadow-soft-lg"
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{ backgroundImage: "radial-gradient(circle at 85% 20%, white 0%, transparent 45%)" }}
      />
      <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-3">
          <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-[12px] font-medium tracking-wide">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500 opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-red-500" />
            </span>
            LIVE NOW
          </span>
          <div>
            <h3 className="text-[20px] font-semibold tracking-tight">{liveMeeting.title}</h3>
            <p className="mt-1 text-[14px] text-white/60">{timeAgo(liveMeeting.actual_start)}</p>
          </div>
          <AvatarStack
            people={[{ id: liveMeeting.host.id, initials: liveMeeting.host.initials }]}
            size={32}
            max={5}
          />
        </div>

        <div className="flex items-center gap-3">
          {isHost && (
            <Button
              variant="outline"
              size="icon"
              onClick={() => endMeeting.mutate(liveMeeting.id)}
              disabled={endMeeting.isPending}
              className="h-12 w-12 rounded-full border-white/15 bg-white/5 text-white hover:bg-white/10"
            >
              <PhoneOff className="h-[18px] w-[18px]" strokeWidth={1.9} />
            </Button>
          )}
          <Button
            render={<Link href={`/call/${liveMeeting.id}`} />}
            nativeButton={false}
            className="h-12 rounded-full bg-white px-6 text-[14px] font-medium text-[#111113] shadow-soft hover:bg-white/90"
          >
            <Video className="h-4 w-4" strokeWidth={2.1} />
            Join Call
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
