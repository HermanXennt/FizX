"use client";

import { useState } from "react";
import { CalendarPlus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useScheduleMeeting } from "@/hooks/use-meetings";

function defaultDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function ScheduleMeetingDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(defaultDate());
  const [startTime, setStartTime] = useState("10:00");
  const [endTime, setEndTime] = useState("11:00");
  const [error, setError] = useState<string | null>(null);

  const schedule = useScheduleMeeting();

  function reset() {
    setTitle("");
    setDate(defaultDate());
    setStartTime("10:00");
    setEndTime("11:00");
    setError(null);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const scheduledStart = new Date(`${date}T${startTime}`);
    const scheduledEnd = new Date(`${date}T${endTime}`);
    if (scheduledEnd <= scheduledStart) {
      setError("End time must be after start time.");
      return;
    }
    setError(null);
    schedule.mutate(
      {
        title: title.trim() || "Class call",
        workspace: workspaceId,
        scheduled_start: scheduledStart.toISOString(),
        scheduled_end: scheduledEnd.toISOString(),
      },
      {
        onSuccess: () => {
          setOpen(false);
          reset();
        },
      }
    );
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogTrigger className="flex items-center gap-1.5 rounded-full bg-secondary px-3.5 py-1.5 text-[12.5px] font-medium text-foreground/80 hover:bg-secondary/80">
        <CalendarPlus className="h-3.5 w-3.5" strokeWidth={2} />
        Schedule a call
      </DialogTrigger>

      <DialogContent className="max-w-md gap-0 overflow-hidden rounded-[28px] border border-black/5 bg-white p-0 shadow-soft-lg sm:max-w-md">
        <DialogHeader className="px-6 pt-6 pb-4">
          <DialogTitle className="text-[17px] font-semibold tracking-tight text-foreground">
            Schedule a call
          </DialogTitle>
          <DialogDescription className="text-[13px] text-muted-foreground">
            This goes on the calendar for everyone in the group.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3 px-6 pb-6">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Class call"
            className="h-10 rounded-2xl border-black/10"
          />
          <Input
            type="date"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="h-10 rounded-2xl border-black/10"
          />
          <div className="flex gap-3">
            <Input
              type="time"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="h-10 rounded-2xl border-black/10"
            />
            <Input
              type="time"
              required
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="h-10 rounded-2xl border-black/10"
            />
          </div>
          {error && <p className="text-[12.5px] text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={schedule.isPending}
            className="h-10 rounded-full bg-primary text-[13.5px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
          >
            {schedule.isPending ? "Scheduling…" : "Schedule"}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
