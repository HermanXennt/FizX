"use client";

import { StartCallDialog } from "@/components/dashboard/start-call-dialog";
import { ScheduleMeetingDialog } from "@/components/dashboard/schedule-meeting-dialog";
import { ConnectWhatsAppDialog } from "@/components/dashboard/connect-whatsapp-dialog";
import type { Workspace } from "@/types/workspace";

export function TeacherQuickActions({ workspace }: { workspace: Workspace }) {
  return (
    <div className="flex flex-wrap items-center gap-2.5 rounded-[28px] border border-black/5 bg-white p-4 shadow-soft">
      <StartCallDialog workspaceId={workspace.id} />
      <ScheduleMeetingDialog workspaceId={workspace.id} />
      <ConnectWhatsAppDialog workspace={workspace} />
    </div>
  );
}
