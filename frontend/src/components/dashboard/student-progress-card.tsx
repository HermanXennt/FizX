"use client";

import { useMyStats } from "@/hooks/use-analytics";

const dayLabels = ["S", "M", "T", "W", "T", "F", "S"];

function lastSevenDays(activity: { date: string; count: number }[] = []): number[] {
  const byDate = new Map(activity.map((a) => [a.date, a.count]));
  const days: number[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    days.push(byDate.get(key) ?? 0);
  }
  return days;
}

export function StudentProgressCard() {
  const { data: stats } = useMyStats();
  const weekly = lastSevenDays(stats?.activity_by_day);
  const max = Math.max(1, ...weekly);
  const totalHours = stats ? Math.round((stats.total_minutes_in_meetings / 60) * 10) / 10 : 0;

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
      <h3 className="mb-5 text-[16px] font-semibold tracking-tight text-foreground">My Progress</h3>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-[20px] font-semibold tracking-tight text-foreground">{stats?.meetings_attended ?? 0}</p>
          <p className="text-[11.5px] text-muted-foreground">Classes attended</p>
        </div>
        <div>
          <p className="text-[20px] font-semibold tracking-tight text-foreground">{totalHours}h</p>
          <p className="text-[11.5px] text-muted-foreground">Time in class</p>
        </div>
      </div>

      <div className="mt-6 flex items-end justify-between gap-2.5">
        {weekly.map((v, i) => (
          <div key={i} className="flex flex-1 flex-col items-center gap-2">
            <div className="flex h-20 w-full items-end overflow-hidden rounded-md bg-secondary/50">
              <div
                className="w-full rounded-md bg-primary transition-all duration-500"
                style={{ height: `${(v / max) * 100}%` }}
              />
            </div>
            <span className="text-[10.5px] font-medium text-muted-foreground">{dayLabels[i]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
