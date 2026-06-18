"use client";

import { CalendarDays } from "lucide-react";
import { useMeetings } from "@/hooks/use-meetings";
import { stableColor } from "@/lib/avatar";

const days = ["S", "M", "T", "W", "T", "F", "S"];

function getWeek() {
  const today = new Date();
  const start = new Date(today);
  start.setDate(today.getDate() - today.getDay());
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

export function CalendarWidget() {
  const week = getWeek();
  const today = new Date();
  const { data: meetings } = useMeetings({ status: "scheduled" });

  const todaysEvents = (meetings ?? [])
    .filter((m) => m.scheduled_start && new Date(m.scheduled_start).toDateString() === today.toDateString())
    .sort((a, b) => new Date(a.scheduled_start!).getTime() - new Date(b.scheduled_start!).getTime())
    .map((m) => ({
      time: new Date(m.scheduled_start!).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      title: m.title,
      color: stableColor(m.id),
    }));

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-7 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-[16px] font-semibold tracking-tight text-foreground">
          Calendar
        </h3>
        <CalendarDays className="h-4 w-4 text-muted-foreground" strokeWidth={1.8} />
      </div>

      <div className="mb-5 grid grid-cols-7 gap-1.5">
        {week.map((d, i) => {
          const isToday = d.toDateString() === today.toDateString();
          return (
            <div key={i} className="flex flex-col items-center gap-1.5">
              <span className="text-[11px] font-medium text-muted-foreground">
                {days[i]}
              </span>
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-[12.5px] font-medium transition-colors ${
                  isToday
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground/70 hover:bg-secondary"
                }`}
              >
                {d.getDate()}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col gap-3">
        {todaysEvents.length === 0 && (
          <p className="text-[12.5px] text-muted-foreground">No events scheduled today.</p>
        )}
        {todaysEvents.map((e, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: e.color }} />
            <span className="w-16 shrink-0 text-[12.5px] text-muted-foreground">{e.time}</span>
            <span className="truncate text-[13px] font-medium text-foreground/85">{e.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
