"use client";

import { Topbar } from "@/components/layout/topbar";
import { useMeetings } from "@/hooks/use-meetings";
import { AvatarStack } from "@/components/dashboard/avatar-stack";
import type { Meeting } from "@/types/meeting";

function groupByDate(meetings: Meeting[]): Record<string, Meeting[]> {
  const groups: Record<string, Meeting[]> = {};
  for (const meeting of meetings) {
    if (!meeting.scheduled_start) continue;
    const key = new Date(meeting.scheduled_start).toDateString();
    groups[key] ??= [];
    groups[key].push(meeting);
  }
  return groups;
}

export default function CalendarPage() {
  const { data: meetings, isLoading } = useMeetings({ status: "scheduled" });
  const groups = groupByDate(
    [...(meetings ?? [])].sort(
      (a, b) => new Date(a.scheduled_start!).getTime() - new Date(b.scheduled_start!).getTime()
    )
  );
  const dateKeys = Object.keys(groups);

  return (
    <>
      <Topbar title="Calendar" subtitle="All your upcoming scheduled meetings." />

      <div className="flex flex-col gap-6">
        {!isLoading && dateKeys.length === 0 && (
          <div className="rounded-[28px] border border-black/5 bg-white p-6 sm:p-10 text-center shadow-soft">
            <p className="text-[14px] text-muted-foreground">No upcoming meetings scheduled.</p>
          </div>
        )}

        {dateKeys.map((dateKey) => (
          <div key={dateKey} className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
            <h3 className="mb-4 text-[15px] font-semibold tracking-tight text-foreground">
              {new Date(dateKey).toLocaleDateString(undefined, {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}
            </h3>
            <div className="flex flex-col">
              {groups[dateKey].map((meeting) => (
                <div
                  key={meeting.id}
                  className="flex items-center gap-4 border-b border-black/[0.04] py-3.5 last:border-0 last:pb-0"
                >
                  <div className="w-20 shrink-0 text-[13.5px] font-medium text-foreground">
                    {new Date(meeting.scheduled_start!).toLocaleTimeString([], {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[14px] font-medium text-foreground">{meeting.title}</p>
                    {meeting.recurrence_rule && (
                      <span className="text-[11.5px] text-muted-foreground">Recurring</span>
                    )}
                  </div>
                  <AvatarStack
                    people={[{ id: meeting.host.id, initials: meeting.host.initials }]}
                    size={24}
                    max={3}
                  />
                  <a
                    href={`/call/${meeting.id}`}
                    className="rounded-full bg-secondary px-3 py-1.5 text-[12.5px] font-medium text-foreground hover:bg-secondary/80"
                  >
                    Join
                  </a>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
