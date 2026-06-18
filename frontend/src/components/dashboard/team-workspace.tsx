"use client";

import { UserPlus } from "lucide-react";
import { useCreateWorkspace, useWorkspaceMembers, useWorkspaces } from "@/hooks/use-workspaces";
import { stableColor } from "@/lib/avatar";
import type { PresenceStatus } from "@/types/user";

const statusColor: Record<PresenceStatus, string> = {
  online: "#34c759",
  in_call: "#1d1d1f",
  away: "#f5a623",
  do_not_disturb: "#ff3b30",
  offline: "#c7c7cc",
};

const statusLabel: Record<PresenceStatus, string> = {
  online: "Online",
  in_call: "In a call",
  away: "Away",
  do_not_disturb: "Do not disturb",
  offline: "Offline",
};

export function TeamWorkspace() {
  const { data: workspaces } = useWorkspaces();
  const workspace = workspaces?.[0];
  const { data: members } = useWorkspaceMembers(workspace?.id);
  const createWorkspace = useCreateWorkspace();

  if (!workspace) {
    return (
      <div className="rounded-[28px] border border-black/5 bg-white p-7 shadow-soft">
        <h3 className="mb-2 text-[16px] font-semibold tracking-tight text-foreground">Team Workspace</h3>
        <p className="mb-4 text-[13px] text-muted-foreground">
          Create a workspace to invite teammates and share meetings.
        </p>
        <button
          onClick={() => createWorkspace.mutate({ name: "My Workspace" })}
          disabled={createWorkspace.isPending}
          className="rounded-full bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90"
        >
          {createWorkspace.isPending ? "Creating…" : "Create workspace"}
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-7 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-[16px] font-semibold tracking-tight text-foreground">{workspace.name}</h3>
        <button className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground">
          <UserPlus className="h-[15px] w-[15px]" strokeWidth={1.9} />
        </button>
      </div>

      <div className="flex flex-col gap-4">
        {members?.map((m) => (
          <div key={m.id} className="flex items-center gap-3">
            <div className="relative">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-full text-[12px] font-semibold text-white"
                style={{ backgroundColor: stableColor(m.user.id) }}
              >
                {m.user.initials}
              </div>
              <span
                className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white"
                style={{ backgroundColor: statusColor[m.user.presence_status] }}
              />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13.5px] font-medium text-foreground">{m.user.full_name}</p>
              <p className="truncate text-[12px] capitalize text-muted-foreground">{m.role}</p>
            </div>
            <span className="shrink-0 text-[11.5px] font-medium text-muted-foreground">
              {statusLabel[m.user.presence_status]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
