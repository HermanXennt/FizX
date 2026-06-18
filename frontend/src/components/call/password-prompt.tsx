"use client";

import { useState } from "react";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function PasswordPrompt({
  error,
  onSubmit,
}: {
  error?: string;
  onSubmit: (password: string) => void;
}) {
  const [password, setPassword] = useState("");

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-[#0b0b0c] px-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(password);
        }}
        className="flex w-full max-w-sm flex-col items-center gap-4 rounded-[28px] border border-white/[0.08] bg-[#18181a] p-8 text-white"
      >
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10">
          <Lock className="h-5 w-5" strokeWidth={2} />
        </div>
        <h1 className="text-[18px] font-semibold">This meeting is protected</h1>
        <p className="text-center text-[13.5px] text-white/50">Enter the meeting password to continue.</p>

        <Input
          type="password"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Meeting password"
          className="h-11 w-full rounded-2xl border-white/10 bg-white/[0.05] text-white placeholder:text-white/35"
        />

        {error && <p className="text-[12.5px] text-red-400">{error}</p>}

        <Button type="submit" className="h-11 w-full rounded-full bg-white text-[#111113] hover:bg-white/90">
          Join meeting
        </Button>
      </form>
    </div>
  );
}
