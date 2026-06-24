"use client";

import { useState } from "react";
import Image from "next/image";
import { Check, MessageCircle, RefreshCw, Users } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  useConnectWhatsApp,
  useDisconnectWhatsApp,
  useImportWhatsAppGroup,
  useUnlinkWhatsAppGroup,
  useWhatsAppGroups,
  useWhatsAppQr,
  useWhatsAppStatus,
} from "@/hooks/use-whatsapp-groups";
import { cn } from "@/lib/utils";
import type { Workspace } from "@/types/workspace";

export function ConnectWhatsAppDialog({ workspace }: { workspace: Workspace }) {
  const [open, setOpen] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [result, setResult] = useState<{ added: number; invited: number; skipped: number } | null>(null);

  const connect = useConnectWhatsApp();
  const disconnect = useDisconnectWhatsApp();
  const { data: statusData } = useWhatsAppStatus({ pollMs: open ? 2500 : undefined, enabled: open });
  const status = statusData?.status ?? "disconnected";
  const isConnected = status === "open";
  const isLinked = Boolean(workspace.whatsapp_group_id) && !result;

  const { data: qrData } = useWhatsAppQr(open && status === "qr");
  const { data: groupsData, isLoading: groupsLoading } = useWhatsAppGroups(open && isConnected && !isLinked);
  const importGroup = useImportWhatsAppGroup(workspace.id);
  const unlinkGroup = useUnlinkWhatsAppGroup(workspace.id);

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (next && status === "disconnected") {
      connect.mutate();
    }
    if (!next) {
      setSelectedGroupId(null);
      setResult(null);
    }
  }

  function handleImport(groupId: string, groupName: string) {
    importGroup.mutate(
      { groupId, groupName },
      { onSuccess: (data) => setResult(data) }
    );
  }

  function handleResync() {
    if (!workspace.whatsapp_group_id) return;
    handleImport(workspace.whatsapp_group_id, workspace.whatsapp_group_name);
  }

  const selectedGroup = groupsData?.groups.find((g) => g.id === selectedGroupId);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger className="flex items-center gap-1.5 rounded-full bg-secondary px-3.5 py-1.5 text-[12.5px] font-medium text-foreground/80 hover:bg-secondary/80">
        <MessageCircle className="h-3.5 w-3.5" strokeWidth={2} />
        {workspace.whatsapp_group_id ? "WhatsApp sync" : "Connect WhatsApp"}
      </DialogTrigger>

      <DialogContent className="max-w-md gap-0 overflow-hidden rounded-[28px] border border-black/5 bg-white p-0 shadow-soft-lg sm:max-w-md">
        <DialogHeader className="px-6 pt-6 pb-4">
          <DialogTitle className="text-[17px] font-semibold tracking-tight text-foreground">
            {result ? "Import complete" : isLinked ? "Syncing with WhatsApp" : isConnected ? "Pick a group" : "Connect WhatsApp"}
          </DialogTitle>
          <DialogDescription className="text-[13px] text-muted-foreground">
            {result
              ? "Here's what happened with the numbers from that group."
              : isLinked
                ? "This group's WhatsApp roster is checked automatically every few minutes."
                : isConnected
                  ? "Pick one of your WhatsApp groups to add everyone in it as students."
                  : "Link your own WhatsApp to pull a class roster straight from a group you're already in. Only group names and phone numbers are read - nothing is ever posted to your chats."}
          </DialogDescription>
        </DialogHeader>

        {!isConnected && !result && (
          <div className="flex flex-col items-center gap-4 px-6 pb-8">
            {qrData?.qr ? (
              <Image src={qrData.qr} alt="WhatsApp QR code" width={220} height={220} className="rounded-2xl" unoptimized />
            ) : (
              <div className="flex h-[220px] w-[220px] items-center justify-center rounded-2xl bg-secondary/60 text-[13px] text-muted-foreground">
                {status === "connecting" ? "Starting…" : "Waiting for QR code…"}
              </div>
            )}
            <p className="text-center text-[12.5px] text-muted-foreground">
              Open WhatsApp → Linked devices → Link a device, then scan this code.
            </p>
          </div>
        )}

        {isConnected && isLinked && (
          <div className="flex flex-col gap-3 px-6 pb-6">
            <div className="flex items-center gap-3 rounded-2xl bg-secondary/60 px-4 py-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white text-foreground/70">
                <Users className="h-4 w-4" strokeWidth={2} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13.5px] font-medium text-foreground">{workspace.whatsapp_group_name}</p>
                <p className="text-[12px] text-muted-foreground">Linked group</p>
              </div>
            </div>
            <button
              onClick={handleResync}
              disabled={importGroup.isPending}
              className="flex items-center justify-center gap-1.5 rounded-full bg-primary px-4 py-2.5 text-[13.5px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", importGroup.isPending && "animate-spin")} strokeWidth={2} />
              {importGroup.isPending ? "Syncing…" : "Sync now"}
            </button>
            <button
              onClick={() => unlinkGroup.mutate()}
              disabled={unlinkGroup.isPending}
              className="rounded-full px-4 py-2 text-[12.5px] font-medium text-muted-foreground hover:text-foreground disabled:opacity-60"
            >
              {unlinkGroup.isPending ? "Unlinking…" : "Unlink this group"}
            </button>
          </div>
        )}

        {isConnected && !isLinked && !result && (
          <>
            <div className="max-h-[280px] overflow-y-auto px-3 pb-3">
              {groupsLoading && (
                <p className="px-3 py-6 text-center text-[13px] text-muted-foreground">Loading your groups…</p>
              )}
              {!groupsLoading && groupsData?.groups.length === 0 && (
                <p className="px-3 py-6 text-center text-[13px] text-muted-foreground">No WhatsApp groups found.</p>
              )}
              {groupsData?.groups.map((group) => {
                const isSelected = group.id === selectedGroupId;
                return (
                  <button
                    key={group.id}
                    type="button"
                    onClick={() => setSelectedGroupId(group.id)}
                    className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left hover:bg-accent"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground/70">
                      <Users className="h-4 w-4" strokeWidth={2} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13.5px] font-medium text-foreground">{group.name}</p>
                      <p className="truncate text-[12px] text-muted-foreground">{group.participantCount} members</p>
                    </div>
                    <span
                      className={cn(
                        "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors",
                        isSelected ? "border-primary bg-primary text-primary-foreground" : "border-black/15"
                      )}
                    >
                      {isSelected && <Check className="h-3 w-3" strokeWidth={2.5} />}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex items-center justify-between gap-3 border-t border-black/[0.05] px-6 py-4">
              <p className="text-[12.5px] text-muted-foreground">
                {selectedGroup ? `${selectedGroup.participantCount} members` : "Pick a group"}
              </p>
              <button
                onClick={() => selectedGroup && handleImport(selectedGroup.id, selectedGroup.name)}
                disabled={!selectedGroupId || importGroup.isPending}
                className="flex items-center gap-1.5 rounded-full bg-primary px-5 py-2.5 text-[13.5px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
              >
                {importGroup.isPending ? "Importing…" : "Import as students"}
              </button>
            </div>
          </>
        )}

        {result && (
          <div className="flex flex-col gap-3 px-6 pb-6">
            <div className="flex items-center justify-between rounded-2xl bg-secondary/60 px-4 py-3">
              <span className="text-[13px] text-foreground/80">Added existing FizX users</span>
              <span className="text-[14px] font-semibold text-foreground">{result.added}</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-secondary/60 px-4 py-3">
              <span className="text-[13px] text-foreground/80">Invited via WhatsApp (new to FizX)</span>
              <span className="text-[14px] font-semibold text-foreground">{result.invited}</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-secondary/60 px-4 py-3">
              <span className="text-[13px] text-foreground/80">Skipped (already in group / hidden number)</span>
              <span className="text-[14px] font-semibold text-foreground">{result.skipped}</span>
            </div>
            <button
              onClick={() => setResult(null)}
              className="mt-2 h-10 rounded-full bg-primary text-[13.5px] font-medium text-primary-foreground hover:bg-primary/90"
            >
              Done
            </button>
          </div>
        )}

        {isConnected && (
          <div className="border-t border-black/[0.05] px-6 py-3 text-center">
            <button
              onClick={() => disconnect.mutate()}
              disabled={disconnect.isPending}
              className="text-[12px] text-muted-foreground hover:text-foreground disabled:opacity-60"
            >
              {disconnect.isPending ? "Disconnecting…" : "Disconnect WhatsApp"}
            </button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
