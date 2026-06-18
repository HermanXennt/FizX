"use client";

import { Topbar } from "@/components/layout/topbar";
import { useWorkspaceOverview } from "@/hooks/use-analytics";
import { useWorkspaces } from "@/hooks/use-workspaces";

export default function AnalyticsPage() {
  const { data: workspaces } = useWorkspaces();
  const workspace = workspaces?.[0];
  const { data: overview, isLoading } = useWorkspaceOverview(workspace?.id);

  if (!workspace) {
    return (
      <>
        <Topbar title="Analytics" subtitle="Meeting statistics for your workspace." />
        <div className="rounded-[28px] border border-black/5 bg-white p-6 sm:p-10 text-center shadow-soft">
          <p className="text-[14px] text-muted-foreground">Create a workspace to see analytics.</p>
        </div>
      </>
    );
  }

  const maxDay = Math.max(1, ...(overview?.meetings_by_day.map((d) => d.count) ?? [0]));

  return (
    <>
      <Topbar title="Analytics" subtitle={`Meeting statistics for ${workspace.name}.`} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
          <p className="text-[28px] font-semibold tracking-tight text-foreground">
            {overview?.total_meetings ?? 0}
          </p>
          <p className="text-[13px] text-muted-foreground">Total meetings</p>
        </div>
        <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
          <p className="text-[28px] font-semibold tracking-tight text-foreground">
            {overview?.total_meeting_minutes ?? 0}m
          </p>
          <p className="text-[13px] text-muted-foreground">Total meeting minutes</p>
        </div>
        <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
          <p className="text-[28px] font-semibold tracking-tight text-foreground">
            {overview?.avg_meeting_duration_minutes ?? 0}m
          </p>
          <p className="text-[13px] text-muted-foreground">Avg. duration</p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft lg:col-span-2">
          <h3 className="mb-5 text-[16px] font-semibold tracking-tight text-foreground">Meetings (last 30 days)</h3>
          {!isLoading && overview?.meetings_by_day.length === 0 ? (
            <p className="text-[13.5px] text-muted-foreground">No meeting activity yet.</p>
          ) : (
            <div className="flex h-40 items-end gap-1.5">
              {overview?.meetings_by_day.map((d) => (
                <div
                  key={d.date}
                  title={`${d.date}: ${d.count}`}
                  className="flex-1 rounded-md bg-primary transition-all duration-500"
                  style={{ height: `${(d.count / maxDay) * 100}%`, minHeight: 4 }}
                />
              ))}
            </div>
          )}
        </div>

        <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
          <h3 className="mb-4 text-[16px] font-semibold tracking-tight text-foreground">Top hosts</h3>
          <div className="flex flex-col gap-3">
            {overview?.top_hosts.map((h) => (
              <div key={h.user_id} className="flex items-center justify-between">
                <span className="truncate text-[13.5px] text-foreground/85">{h.name}</span>
                <span className="text-[12.5px] font-medium text-muted-foreground">{h.meeting_count}</span>
              </div>
            ))}
            {overview?.top_hosts.length === 0 && (
              <p className="text-[13px] text-muted-foreground">No data yet.</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
