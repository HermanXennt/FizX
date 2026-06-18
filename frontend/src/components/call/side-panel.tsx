"use client";

import { useParticipants } from "@livekit/components-react";
import { AnimatePresence, motion } from "framer-motion";
import { X, Send, Sparkles, ListChecks, Search, Mic, MicOff, Check, UserX } from "lucide-react";
import { useState } from "react";
import { useChat } from "@/hooks/use-chat";
import { useAdmitParticipant, useDenyParticipant, useMeetingParticipants } from "@/hooks/use-meetings";
import { useAuthStore } from "@/store/auth-store";
import { stableColor } from "@/lib/avatar";
import { cn } from "@/lib/utils";

export type PanelTab = "participants" | "chat" | "notes" | "transcript";

const tabs: { id: PanelTab; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "participants", label: "People" },
  { id: "notes", label: "AI Notes" },
  { id: "transcript", label: "Transcript" },
];

export function SidePanel({
  tab,
  onChangeTab,
  onClose,
  meetingId,
  isHost,
}: {
  tab: PanelTab | null;
  onChangeTab: (tab: PanelTab) => void;
  onClose: () => void;
  meetingId: string;
  isHost: boolean;
}) {
  return (
    <AnimatePresence>
      {tab && (
        <motion.div
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 24 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          // Below sm, this overlays just the video-grid area (its parent is
          // the relatively-positioned middle row, not the viewport) so the
          // call timer up top and mic/camera/leave controls below stay
          // reachable - at sm+ it reverts to a normal fixed-width sidebar.
          className="absolute inset-0 z-30 flex flex-col rounded-3xl border border-white/[0.06] bg-[#18181a] text-white sm:relative sm:inset-auto sm:w-[360px] sm:shrink-0"
        >
          <div className="flex items-center justify-between gap-2 p-4 pb-3">
            <div className="flex items-center gap-1 rounded-full bg-white/[0.06] p-1">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => onChangeTab(t.id)}
                  className={cn(
                    "rounded-full px-3 py-1.5 text-[12.5px] font-medium transition-colors duration-200",
                    tab === t.id ? "bg-white text-[#111113]" : "text-white/55 hover:text-white/80"
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <button
              onClick={onClose}
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-white/50 hover:bg-white/[0.08] hover:text-white"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 pb-4">
            {tab === "chat" && <ChatTab meetingId={meetingId} />}
            {tab === "participants" && <ParticipantsTab meetingId={meetingId} isHost={isHost} />}
            {tab === "notes" && <NotesTab />}
            {tab === "transcript" && <TranscriptTab />}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ChatTab({ meetingId }: { meetingId: string }) {
  const { messages, sendMessage } = useChat({ kind: "meeting", id: meetingId });
  const myId = useAuthStore((s) => s.user?.id);
  const [draft, setDraft] = useState("");

  function handleSend() {
    if (!draft.trim()) return;
    sendMessage(draft.trim());
    setDraft("");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4">
        {messages.map((m) => {
          const self = m.sender.id === myId;
          return (
            <div key={m.id} className={cn("flex gap-2.5", self && "flex-row-reverse")}>
              <div
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10.5px] font-semibold text-white"
                style={{ backgroundColor: stableColor(m.sender.id) }}
              >
                {m.sender.initials}
              </div>
              <div className={cn("flex max-w-[80%] flex-col gap-1", self && "items-end")}>
                <div className="flex items-center gap-2">
                  <span className="text-[11.5px] font-medium text-white/60">{m.sender.full_name}</span>
                  <span className="text-[10.5px] text-white/35">
                    {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                <div
                  className={cn(
                    "rounded-2xl px-3 py-2 text-[13px] leading-relaxed",
                    self ? "bg-white text-[#111113]" : "bg-white/[0.07] text-white/85"
                  )}
                >
                  {m.is_deleted ? <span className="italic text-white/40">message deleted</span> : m.content}
                </div>
              </div>
            </div>
          );
        })}
        {messages.length === 0 && (
          <p className="py-8 text-center text-[13px] text-white/35">No messages yet. Say hello!</p>
        )}
      </div>

      <div className="sticky bottom-0 mt-4 flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.05] p-1.5 pl-3.5">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Send a message…"
          className="h-8 flex-1 bg-transparent text-[13px] text-white outline-none placeholder:text-white/35"
        />
        <button
          onClick={handleSend}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-[#111113]"
        >
          <Send className="h-3.5 w-3.5" strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}

function ParticipantsTab({ meetingId, isHost }: { meetingId: string; isHost: boolean }) {
  const liveParticipants = useParticipants();
  const { data: dbParticipants } = useMeetingParticipants(meetingId, { pollMs: isHost ? 5000 : undefined });
  const admit = useAdmitParticipant(meetingId);
  const deny = useDenyParticipant(meetingId);

  const waiting = isHost ? (dbParticipants ?? []).filter((p) => p.status === "waiting") : [];

  return (
    <div className="flex flex-col gap-1">
      <div className="relative mb-3">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/35" />
        <input
          placeholder="Search people…"
          className="h-9 w-full rounded-full bg-white/[0.06] pl-9 text-[13px] text-white outline-none placeholder:text-white/35"
        />
      </div>

      {waiting.length > 0 && (
        <div className="mb-4">
          <p className="mb-1 px-1 text-[11.5px] font-medium text-amber-400/80">
            WAITING ROOM · {waiting.length}
          </p>
          {waiting.map((p) => (
            <div key={p.id} className="flex items-center gap-3 rounded-2xl px-2 py-2.5">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-semibold text-white"
                style={{ backgroundColor: stableColor(p.user.id) }}
              >
                {p.user.initials}
              </div>
              <p className="min-w-0 flex-1 truncate text-[13px] font-medium text-white/85">{p.user.full_name}</p>
              <button
                onClick={() => admit.mutate(p.id)}
                className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25"
              >
                <Check className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => deny.mutate(p.id)}
                className="flex h-7 w-7 items-center justify-center rounded-full bg-red-500/15 text-red-400 hover:bg-red-500/25"
              >
                <UserX className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      <p className="mb-1 px-1 text-[11.5px] font-medium text-white/40">IN CALL · {liveParticipants.length}</p>
      {liveParticipants.map((p) => (
        <div key={p.identity} className="flex items-center gap-3 rounded-2xl px-2 py-2.5 hover:bg-white/[0.05]">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-semibold text-white"
            style={{ backgroundColor: stableColor(p.identity) }}
          >
            {(p.name || "?").slice(0, 2).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-medium text-white/85">{p.name || "Guest"}</p>
          </div>
          <div className="flex items-center gap-2 text-white/40">
            {p.isMicrophoneEnabled ? (
              <Mic className="h-3.5 w-3.5" strokeWidth={1.9} />
            ) : (
              <MicOff className="h-3.5 w-3.5" strokeWidth={1.9} />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function NotesTab() {
  const [resolved, setResolved] = useState<Record<number, boolean>>({});
  const actionItems = [
    "Share usability study recordings with the team",
    "Revise form validation copy for step 3",
    "Tighten spacing on onboarding step 2",
    "Schedule follow-up review before Friday",
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-white/50" strokeWidth={2} />
          <p className="text-[11.5px] font-medium text-white/40">LIVE SUMMARY</p>
        </div>
        <p className="text-[13.5px] leading-relaxed text-white/75">
          AI meeting summaries aren&apos;t connected yet. This panel is ready for a
          summarization service to populate it once one is wired up.
        </p>
      </div>

      <div>
        <div className="mb-2 flex items-center gap-2">
          <ListChecks className="h-3.5 w-3.5 text-white/50" strokeWidth={2} />
          <p className="text-[11.5px] font-medium text-white/40">ACTION ITEMS</p>
        </div>
        <div className="flex flex-col gap-1">
          {actionItems.map((item, i) => (
            <button
              key={i}
              onClick={() => setResolved((r) => ({ ...r, [i]: !r[i] }))}
              className="flex items-start gap-2.5 rounded-2xl px-2 py-2 text-left hover:bg-white/[0.05]"
            >
              <span
                className={cn(
                  "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-colors",
                  resolved[i] ? "border-white bg-white" : "border-white/30"
                )}
              >
                {resolved[i] && <span className="h-1.5 w-1.5 rounded-full bg-[#111113]" />}
              </span>
              <span
                className={cn(
                  "text-[13px] leading-snug text-white/80",
                  resolved[i] && "text-white/40 line-through"
                )}
              >
                {item}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function TranscriptTab() {
  return (
    <div className="flex h-full items-center justify-center px-6 text-center">
      <p className="text-[13px] leading-relaxed text-white/35">
        Live transcription isn&apos;t connected yet. This panel is ready for a
        speech-to-text service to stream lines into once one is wired up.
      </p>
    </div>
  );
}
