"use client";

import { ActiveCallCard } from "@/components/dashboard/active-call-card";
import { AIAssistantCard } from "@/components/dashboard/ai-assistant-card";
import { AnalyticsCard } from "@/components/dashboard/analytics-card";
import { CalendarWidget } from "@/components/dashboard/calendar-widget";
import { RecordingsList } from "@/components/dashboard/recordings-list";
import { StudentRosterCard } from "@/components/dashboard/student-roster-card";
import { TeacherQuickActions } from "@/components/dashboard/teacher-quick-actions";
import { TeamWorkspace } from "@/components/dashboard/team-workspace";
import { UpcomingMeetings } from "@/components/dashboard/upcoming-meetings";
import { useWorkspaces } from "@/hooks/use-workspaces";

export function TeacherDashboard() {
  const { data: workspaces } = useWorkspaces();
  const workspace = workspaces?.[0];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="flex flex-col gap-6 lg:col-span-2">
        {workspace && <TeacherQuickActions workspace={workspace} />}
        <ActiveCallCard />
        <StudentRosterCard workspaceId={workspace?.id} />
        <UpcomingMeetings title="Upcoming classes" />
        <RecordingsList />
      </div>

      <div className="flex flex-col gap-6">
        <AIAssistantCard isTeacher />
        <AnalyticsCard />
        <CalendarWidget />
        <TeamWorkspace />
      </div>
    </div>
  );
}
