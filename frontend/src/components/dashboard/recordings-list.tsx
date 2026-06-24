"use client";

import { Play, Download, Clock3 } from "lucide-react";
import { useMyRecordings } from "@/hooks/use-recordings";
import type { MeetingRecording } from "@/types/recording";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatSize(bytes: number | null): string {
  if (!bytes) return "—";
  return `${(bytes / (1024 * 1024)).toFixed(0)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function RecordingsList({ title = "Recent Recordings" }: { title?: string }) {
  const { data: recordings, isLoading } = useMyRecordings();

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-[17px] font-semibold tracking-tight text-foreground">{title}</h3>
        <span className="text-[13px] text-muted-foreground">{recordings?.length ?? 0} total</span>
      </div>

      <div className="flex flex-col">
        {!isLoading && recordings?.length === 0 && (
          <p className="py-6 text-center text-[13.5px] text-muted-foreground">No recordings yet.</p>
        )}

        {recordings?.map((rec: MeetingRecording) => (
          <div
            key={rec.id}
            className="group flex items-center gap-4 border-b border-black/[0.04] py-3.5 last:border-0 last:pb-0"
          >
            {rec.status === "ready" ? (
              <a
                href={rec.file_url}
                target="_blank"
                rel="noreferrer"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground transition-colors duration-200 group-hover:bg-primary group-hover:text-primary-foreground"
              >
                <Play className="h-3.5 w-3.5 fill-current" strokeWidth={0} />
              </a>
            ) : (
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-muted-foreground">
                <Clock3 className="h-3.5 w-3.5" strokeWidth={2} />
              </div>
            )}

            <div className="min-w-0 flex-1">
              <p className="truncate text-[14.5px] font-medium text-foreground">Recording</p>
              <p className="mt-0.5 text-[12.5px] text-muted-foreground">
                {formatDate(rec.created_at)} · {formatDuration(rec.duration_seconds)} · {formatSize(rec.size_bytes)} ·{" "}
                {rec.status}
              </p>
            </div>

            {rec.status === "ready" && (
              <a
                href={rec.file_url}
                download
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground"
              >
                <Download className="h-[15px] w-[15px]" strokeWidth={1.9} />
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
