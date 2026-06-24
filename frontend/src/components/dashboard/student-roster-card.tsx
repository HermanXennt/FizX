"use client";

import { AlertCircle, Users } from "lucide-react";
import { useWorkspaceStudentRoster } from "@/hooks/use-analytics";
import { stableColor } from "@/lib/avatar";
import { cn } from "@/lib/utils";

function formatLastAttended(iso: string | null): string {
  if (!iso) return "Never attended";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60 * 24));
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

export function StudentRosterCard({ workspaceId }: { workspaceId: string | undefined }) {
  const { data: roster, isLoading } = useWorkspaceStudentRoster(workspaceId);
  const needsAttention = roster?.filter((r) => r.meetings_attended === 0) ?? [];

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-[16px] font-semibold tracking-tight text-foreground">Students</h3>
        {needsAttention.length > 0 && (
          <span className="flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[11.5px] font-medium text-amber-700">
            <AlertCircle className="h-3 w-3" strokeWidth={2} />
            {needsAttention.length} need attention
          </span>
        )}
      </div>

      <div className="flex flex-col">
        {!isLoading && roster?.length === 0 && (
          <p className="py-6 text-center text-[13.5px] text-muted-foreground">No students in this class yet.</p>
        )}

        {roster?.map((student) => {
          const flagged = student.meetings_attended === 0;
          return (
            <div
              key={student.user_id}
              className="flex items-center gap-3 border-b border-black/[0.04] py-3 last:border-0 last:pb-0"
            >
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold text-white"
                style={{ backgroundColor: stableColor(student.user_id) }}
              >
                <Users className="h-3.5 w-3.5" strokeWidth={2} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13.5px] font-medium text-foreground">{student.name}</p>
                <p className="text-[12px] text-muted-foreground">{formatLastAttended(student.last_attended)}</p>
              </div>
              <span
                className={cn(
                  "shrink-0 rounded-full px-2.5 py-1 text-[11.5px] font-medium",
                  flagged ? "bg-amber-50 text-amber-700" : "bg-secondary text-foreground/80"
                )}
              >
                {student.meetings_attended}/{student.total_meetings} classes
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
