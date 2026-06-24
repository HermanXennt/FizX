"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowUpRight, ChevronRight } from "lucide-react";
import { AvatarStack } from "@/components/dashboard/avatar-stack";
import { useMeetings } from "@/hooks/use-meetings";
import type { Meeting } from "@/types/meeting";

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function formatDuration(meeting: Meeting): string {
  if (!meeting.scheduled_start || !meeting.scheduled_end) return "";
  const minutes = Math.round(
    (new Date(meeting.scheduled_end).getTime() - new Date(meeting.scheduled_start).getTime()) / 60000
  );
  return `${minutes} min`;
}

export function UpcomingMeetings({ title = "Upcoming Meetings" }: { title?: string }) {
  const { data: meetings, isLoading } = useMeetings({ status: "scheduled" });

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-[17px] font-semibold tracking-tight text-foreground">{title}</h3>
        <Link
          href="/calendar"
          className="flex items-center gap-1 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          View all
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="flex flex-col">
        {!isLoading && meetings?.length === 0 && (
          <p className="py-6 text-center text-[13.5px] text-muted-foreground">
            No upcoming meetings scheduled.
          </p>
        )}

        {meetings?.map((meeting, i) => (
          <motion.div
            key={meeting.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.05, ease: "easeOut" }}
            className="flex items-center gap-4 border-b border-black/[0.04] py-4 last:border-0 last:pb-0"
          >
            <div className="w-16 shrink-0">
              <p className="text-[14px] font-medium text-foreground">{formatTime(meeting.scheduled_start)}</p>
              <p className="text-[12px] text-muted-foreground">{formatDuration(meeting)}</p>
            </div>

            <div className="h-9 w-px bg-black/[0.05]" />

            <div className="min-w-0 flex-1">
              <p className="truncate text-[14.5px] font-medium text-foreground">{meeting.title}</p>
              {meeting.requires_password && (
                <span className="mt-1 inline-block text-[11px] font-medium text-muted-foreground">
                  Password protected
                </span>
              )}
            </div>

            <AvatarStack
              people={[{ id: meeting.host.id, initials: meeting.host.initials }]}
              size={26}
              max={3}
            />

            <Link
              href={`/call/${meeting.id}`}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground"
            >
              <ArrowUpRight className="h-4 w-4" strokeWidth={2} />
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
