"use client";

import { useState } from "react";
import { Sparkles, ArrowUp } from "lucide-react";

const aiSuggestions = [
  "Summarize this meeting",
  "List action items",
  "Who hasn't spoken yet?",
  "Draft a follow-up email",
];

export function AIAssistantCard() {
  const [value, setValue] = useState("");

  return (
    <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
      <div className="mb-4 flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Sparkles className="h-[15px] w-[15px]" strokeWidth={2} />
        </div>
        <h3 className="text-[16px] font-semibold tracking-tight text-foreground">
          AI Assistant
        </h3>
      </div>

      <p className="text-[13.5px] leading-relaxed text-muted-foreground">
        Ask about your meetings, get summaries, or draft follow-ups instantly.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {aiSuggestions.map((s) => (
          <button
            key={s}
            onClick={() => setValue(s)}
            className="rounded-full border border-black/[0.06] bg-secondary/60 px-3 py-1.5 text-[12.5px] font-medium text-foreground/80 transition-colors duration-200 hover:bg-secondary"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="mt-5 flex items-center gap-2 rounded-full border border-black/[0.06] bg-secondary/40 p-1.5 pl-4">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask anything…"
          className="h-8 flex-1 bg-transparent text-[13.5px] outline-none placeholder:text-muted-foreground/70"
        />
        <button className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90">
          <ArrowUp className="h-4 w-4" strokeWidth={2.2} />
        </button>
      </div>
    </div>
  );
}
