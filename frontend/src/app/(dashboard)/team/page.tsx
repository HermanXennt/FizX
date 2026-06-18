"use client";

import { useState } from "react";
import { UserPlus } from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StartCallDialog } from "@/components/dashboard/start-call-dialog";
import {
  useCreateWorkspace,
  useInviteToWorkspace,
  useWorkspaceInvitations,
  useWorkspaceMembers,
  useWorkspaces,
} from "@/hooks/use-workspaces";
import { stableColor } from "@/lib/avatar";

export default function TeamPage() {
  const { data: workspaces } = useWorkspaces();
  const workspace = workspaces?.[0];
  const { data: members } = useWorkspaceMembers(workspace?.id);
  const { data: invitations } = useWorkspaceInvitations(workspace?.id);
  const createWorkspace = useCreateWorkspace();
  const invite = useInviteToWorkspace(workspace?.id ?? "");
  const [phoneNumber, setPhoneNumber] = useState("");

  if (!workspace) {
    return (
      <>
        <Topbar title="Team" subtitle="Manage members, roles, and invitations." />
        <div className="rounded-[28px] border border-black/5 bg-white p-6 sm:p-10 text-center shadow-soft">
          <p className="mb-4 text-[14px] text-muted-foreground">
            You don&apos;t have a workspace yet. Create one to invite teammates.
          </p>
          <Button
            onClick={() => createWorkspace.mutate({ name: "My Workspace" })}
            disabled={createWorkspace.isPending}
            className="h-11 rounded-full bg-primary px-6 text-primary-foreground"
          >
            {createWorkspace.isPending ? "Creating…" : "Create workspace"}
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      <Topbar title={workspace.name} subtitle={`${workspace.member_count} members · ${workspace.plan} plan`} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft lg:col-span-2">
          <div className="mb-5 flex items-center justify-between gap-3">
            <h3 className="text-[16px] font-semibold tracking-tight text-foreground">Members</h3>
            <StartCallDialog workspaceId={workspace.id} />
          </div>
          <div className="flex flex-col">
            {members?.map((m) => (
              <div
                key={m.id}
                className="flex items-center gap-3 border-b border-black/[0.04] py-3.5 last:border-0 last:pb-0"
              >
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-full text-[12px] font-semibold text-white"
                  style={{ backgroundColor: stableColor(m.user.id) }}
                >
                  {m.user.initials}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13.5px] font-medium text-foreground">{m.user.full_name}</p>
                </div>
                <span className="shrink-0 rounded-full bg-secondary px-2.5 py-1 text-[11.5px] font-medium capitalize text-foreground/80">
                  {m.role}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
            <h3 className="mb-4 text-[16px] font-semibold tracking-tight text-foreground">Invite teammate</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                invite.mutate({ phone_number: phoneNumber, role: "member" });
                setPhoneNumber("");
              }}
              className="flex flex-col gap-3"
            >
              <Input
                type="tel"
                required
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="15551234567"
                className="h-10 rounded-2xl border-black/10"
              />
              <Button
                type="submit"
                disabled={invite.isPending}
                className="h-10 rounded-full bg-primary text-primary-foreground"
              >
                <UserPlus className="h-3.5 w-3.5" />
                {invite.isPending ? "Sending…" : "Send invite"}
              </Button>
            </form>
          </div>

          {invitations && invitations.length > 0 && (
            <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
              <h3 className="mb-4 text-[14px] font-semibold tracking-tight text-foreground">Pending invitations</h3>
              <div className="flex flex-col gap-3">
                {invitations.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between gap-2">
                    <span className="truncate text-[13px] text-foreground/80">{inv.phone_number}</span>
                    <span className="shrink-0 text-[11.5px] capitalize text-muted-foreground">{inv.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
