import { Topbar } from "@/components/layout/topbar";
import { ActiveCallCard } from "@/components/dashboard/active-call-card";
import { UpcomingMeetings } from "@/components/dashboard/upcoming-meetings";
import { RecordingsList } from "@/components/dashboard/recordings-list";
import { AIAssistantCard } from "@/components/dashboard/ai-assistant-card";
import { CalendarWidget } from "@/components/dashboard/calendar-widget";
import { TeamWorkspace } from "@/components/dashboard/team-workspace";
import { AnalyticsCard } from "@/components/dashboard/analytics-card";
import { ChatLauncher } from "@/components/dashboard/chat-launcher";

export default function DashboardPage() {
  return (
    <>
      <Topbar />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <ActiveCallCard />
          <UpcomingMeetings />
          <RecordingsList />
        </div>

        <div className="flex flex-col gap-6">
          <AIAssistantCard />
          <CalendarWidget />
          <TeamWorkspace />
          <AnalyticsCard />
        </div>
      </div>

      <ChatLauncher />
    </>
  );
}
