"use client";

import { useRef, useState } from "react";
import { Sparkles, ArrowUp } from "lucide-react";
import { useAskAi } from "@/hooks/use-ai";
import { useMeetings } from "@/hooks/use-meetings";
import { extractErrorMessage } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { AiPreset } from "@/services/ai-service";

const presets: { label: string; preset: AiPreset; needsMeeting: boolean; teacherOnly?: boolean }[] = [
  { label: "Summarize this meeting", preset: "summarize", needsMeeting: true },
  { label: "List action items", preset: "action_items", needsMeeting: true },
  { label: "Who hasn't spoken yet?", preset: "who_hasnt_spoken", needsMeeting: true, teacherOnly: true },
  { label: "Draft a follow-up email", preset: "follow_up_email", needsMeeting: true },
];

interface ChatMessage {
  role: "user" | "assistant" | "error";
  content: string;
}

export function AIAssistantCard({ isTeacher = true }: { isTeacher?: boolean }) {
  const [value, setValue] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const visiblePresets = presets.filter((p) => isTeacher || !p.teacherOnly);

  const { data: liveMeetings } = useMeetings({ status: "live" });
  const { data: endedMeetings } = useMeetings({ status: "ended" });
  const meetingId = liveMeetings?.[0]?.id ?? endedMeetings?.[0]?.id;

  const askAi = useAskAi();

  function send(label: string, payload: { message?: string; preset?: AiPreset }) {
    setHistory((h) => [...h, { role: "user", content: label }]);
    setValue("");
    askAi.mutate(
      { ...payload, meeting_id: meetingId },
      {
        onSuccess: (data) => {
          setHistory((h) => [...h, { role: "assistant", content: data.reply }]);
          requestAnimationFrame(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }));
        },
        onError: (error) => {
          setHistory((h) => [...h, { role: "error", content: extractErrorMessage(error) }]);
        },
      }
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim() || askAi.isPending) return;
    send(value.trim(), { message: value.trim() });
  }

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
      <div className="mb-4 flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Sparkles className="h-[15px] w-[15px]" strokeWidth={2} />
        </div>
        <h3 className="text-[16px] font-semibold tracking-tight text-foreground">AI Assistant</h3>
      </div>

      <p className="text-[13.5px] leading-relaxed text-muted-foreground">
        Ask about your meetings, get summaries, or draft follow-ups instantly.
      </p>

      {history.length > 0 && (
        <div ref={scrollRef} className="mt-4 flex max-h-64 flex-col gap-2.5 overflow-y-auto pr-1">
          {history.map((m, i) => (
            <div
              key={i}
              className={cn(
                "max-w-[90%] rounded-2xl px-3.5 py-2 text-[13px] leading-relaxed",
                m.role === "user" && "self-end bg-primary text-primary-foreground",
                m.role === "assistant" && "self-start bg-secondary/70 text-foreground",
                m.role === "error" && "self-start bg-red-50 text-red-600"
              )}
            >
              {m.content}
            </div>
          ))}
          {askAi.isPending && (
            <div className="self-start rounded-2xl bg-secondary/70 px-3.5 py-2 text-[13px] text-muted-foreground">
              Thinking…
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {visiblePresets.map((p) => {
          const disabled = (p.needsMeeting && !meetingId) || askAi.isPending;
          return (
            <button
              key={p.preset}
              disabled={disabled}
              title={disabled && p.needsMeeting && !meetingId ? "No recent meeting" : undefined}
              onClick={() => send(p.label, { preset: p.preset })}
              className="rounded-full border border-black/[0.06] bg-secondary/60 px-3 py-1.5 text-[12.5px] font-medium text-foreground/80 transition-colors duration-200 hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-40"
            >
              {p.label}
            </button>
          );
        })}
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-5 flex items-center gap-2 rounded-full border border-black/[0.06] bg-secondary/40 p-1.5 pl-4"
      >
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask anything…"
          disabled={askAi.isPending}
          className="h-8 flex-1 bg-transparent text-[13.5px] outline-none placeholder:text-muted-foreground/70"
        />
        <button
          type="submit"
          disabled={!value.trim() || askAi.isPending}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          <ArrowUp className="h-4 w-4" strokeWidth={2.2} />
        </button>
      </form>
    </div>
  );
}
