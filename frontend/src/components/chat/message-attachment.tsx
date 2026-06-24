"use client";

import { FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/chat";

function formatSize(bytes: number | null): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function MessageAttachment({ message, tone = "light" }: { message: ChatMessage; tone?: "light" | "dark" }) {
  if (!message.attachment_url) return null;

  if (message.attachment_content_type.startsWith("image/")) {
    return (
      <a href={message.attachment_url} target="_blank" rel="noopener noreferrer" className="block overflow-hidden rounded-xl">
        {/* eslint-disable-next-line @next/next/no-img-element -- arbitrary user-uploaded URLs, not a static/optimizable asset */}
        <img
          src={message.attachment_url}
          alt={message.attachment_name || "Image attachment"}
          className="max-h-64 w-auto max-w-full rounded-xl object-cover"
        />
      </a>
    );
  }

  return (
    <a
      href={message.attachment_url}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "flex items-center gap-2.5 rounded-xl border px-3 py-2.5 transition-colors",
        tone === "dark"
          ? "border-white/[0.08] bg-white/[0.05] hover:bg-white/[0.08]"
          : "border-black/[0.06] bg-black/[0.02] hover:bg-black/[0.04]"
      )}
    >
      <FileText className={cn("h-5 w-5 shrink-0", tone === "dark" ? "text-white/50" : "text-muted-foreground")} strokeWidth={1.8} />
      <div className="min-w-0 flex-1">
        <p className={cn("truncate text-[12.5px] font-medium", tone === "dark" ? "text-white/85" : "text-foreground")}>
          {message.attachment_name || "Attachment"}
        </p>
        {message.attachment_size != null && (
          <p className={cn("text-[11px]", tone === "dark" ? "text-white/40" : "text-muted-foreground")}>
            {formatSize(message.attachment_size)}
          </p>
        )}
      </div>
    </a>
  );
}
