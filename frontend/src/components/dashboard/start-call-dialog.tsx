"use client";

import { useState } from "react";
import { Check, Search, Video } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useCreateInstantMeeting } from "@/hooks/use-meetings";
import { useWorkspaceMembers } from "@/hooks/use-workspaces";
import { useAuthStore } from "@/store/auth-store";
import { stableColor } from "@/lib/avatar";
import { cn } from "@/lib/utils";

export function StartCallDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const currentUserId = useAuthStore((s) => s.user?.id);
  const { data: members, isLoading } = useWorkspaceMembers(workspaceId, search);
  const createInstant = useCreateInstantMeeting();

  const candidates = (members ?? []).filter((m) => m.user.id !== currentUserId);

  function toggle(id: string) {
    setSelectedIds((current) => (current.includes(id) ? current.filter((x) => x !== id) : [...current, id]));
  }

  function handleStart() {
    createInstant.mutate(
      { workspace: workspaceId, participant_ids: selectedIds },
      {
        onSuccess: () => {
          setOpen(false);
          setSelectedIds([]);
          setSearch("");
        },
      }
    );
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) {
          setSelectedIds([]);
          setSearch("");
        }
      }}
    >
      <DialogTrigger className="flex items-center gap-1.5 rounded-full bg-primary px-3.5 py-1.5 text-[12.5px] font-medium text-primary-foreground hover:bg-primary/90">
        <Video className="h-3.5 w-3.5" strokeWidth={2} />
        Start a call
      </DialogTrigger>

      <DialogContent className="max-w-md gap-0 overflow-hidden rounded-[28px] border border-black/5 bg-white p-0 shadow-soft-lg sm:max-w-md">
        <DialogHeader className="px-6 pt-6 pb-4">
          <DialogTitle className="text-[17px] font-semibold tracking-tight text-foreground">
            Start a call
          </DialogTitle>
          <DialogDescription className="text-[13px] text-muted-foreground">
            Search teammates by name or phone number and call them instantly.
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 pb-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name or phone…"
              className="h-10 w-full rounded-full bg-secondary/60 pl-9 pr-3.5 text-[13.5px] outline-none placeholder:text-muted-foreground/70"
            />
          </div>
        </div>

        <div className="max-h-[280px] overflow-y-auto px-3 pb-3">
          {isLoading && <p className="px-3 py-6 text-center text-[13px] text-muted-foreground">Searching…</p>}
          {!isLoading && candidates.length === 0 && (
            <p className="px-3 py-6 text-center text-[13px] text-muted-foreground">No teammates found.</p>
          )}
          {candidates.map((member) => {
            const isSelected = selectedIds.includes(member.user.id);
            return (
              <button
                key={member.id}
                type="button"
                onClick={() => toggle(member.user.id)}
                className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left hover:bg-accent"
              >
                <div
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold text-white"
                  style={{ backgroundColor: stableColor(member.user.id) }}
                >
                  {member.user.initials}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13.5px] font-medium text-foreground">{member.user.full_name}</p>
                  <p className="truncate text-[12px] text-muted-foreground">{member.phone_number}</p>
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
            {selectedIds.length === 0
              ? "Just you for now"
              : `${selectedIds.length} ${selectedIds.length === 1 ? "person" : "people"} selected`}
          </p>
          <button
            onClick={handleStart}
            disabled={createInstant.isPending}
            className="flex items-center gap-1.5 rounded-full bg-primary px-5 py-2.5 text-[13.5px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
          >
            <Video className="h-3.5 w-3.5" strokeWidth={2} />
            {createInstant.isPending ? "Starting…" : "Start call"}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
