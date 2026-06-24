"use client";

import { ActiveCallCard } from "@/components/dashboard/active-call-card";
import { AIAssistantCard } from "@/components/dashboard/ai-assistant-card";
import { CalendarWidget } from "@/components/dashboard/calendar-widget";
import { RecordingsList } from "@/components/dashboard/recordings-list";
import { StudentProgressCard } from "@/components/dashboard/student-progress-card";
import { TeamWorkspace } from "@/components/dashboard/team-workspace";
import { UpcomingMeetings } from "@/components/dashboard/upcoming-meetings";

export function StudentDashboard() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="flex flex-col gap-6 lg:col-span-2">
        <ActiveCallCard />
        <StudentProgressCard />
        <UpcomingMeetings title="My classes" />
        <RecordingsList title="My recordings" />
      </div>

      <div className="flex flex-col gap-6">
        <AIAssistantCard isTeacher={false} />
        <CalendarWidget />
        <TeamWorkspace />
      </div>
    </div>
  );
}
