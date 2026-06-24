"use client";

import { useRef, useState } from "react";
import { MessageSquare, Paperclip, Send, X } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { MessageAttachment } from "@/components/chat/message-attachment";
import { useChat } from "@/hooks/use-chat";
import { useWorkspaces } from "@/hooks/use-workspaces";
import { useAuthStore } from "@/store/auth-store";
import { stableColor } from "@/lib/avatar";
import { cn } from "@/lib/utils";

function ChatBody({ workspaceId }: { workspaceId: string }) {
  const { messages, sendMessage, sendAttachment } = useChat({ kind: "workspace", id: workspaceId });
  const myId = useAuthStore((s) => s.user?.id);
  const [draft, setDraft] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleSend() {
    if (!draft.trim()) return;
    sendMessage(draft.trim());
    setDraft("");
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setUploading(true);
    try {
      await sendAttachment(file);
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <div className="flex-1 overflow-y-auto px-6 py-5">
        <div className="flex flex-col gap-5">
          {messages.length === 0 && (
            <p className="py-8 text-center text-[13.5px] text-muted-foreground">
              No messages yet. Start the conversation.
            </p>
          )}
          {messages.map((m) => {
            const self = m.sender.id === myId;
            return (
              <div key={m.id} className={cn("flex gap-3", self && "flex-row-reverse")}>
                <div
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold text-white"
                  style={{ backgroundColor: stableColor(m.sender.id) }}
                >
                  {m.sender.initials}
                </div>
                <div className={cn("flex max-w-[78%] flex-col gap-1", self && "items-end")}>
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-medium text-foreground/70">{m.sender.full_name}</span>
                    <span className="text-[11px] text-muted-foreground">
                      {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                  {m.content && (
                    <div
                      className={cn(
                        "rounded-2xl px-3.5 py-2.5 text-[13.5px] leading-relaxed",
                        self ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground"
                      )}
                    >
                      {m.content}
                    </div>
                  )}
                  {!m.is_deleted && <MessageAttachment message={m} tone="light" />}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="border-t border-black/[0.05] p-4">
        <div className="flex items-center gap-2 rounded-full border border-black/[0.06] bg-secondary/40 p-1.5 pl-4">
          <input ref={fileInputRef} type="file" onChange={handleFileSelect} className="hidden" />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            title="Attach a file"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-40"
          >
            <Paperclip className="h-3.5 w-3.5" strokeWidth={2} />
          </button>
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={uploading ? "Uploading…" : "Message the team…"}
            disabled={uploading}
            className="h-8 flex-1 bg-transparent text-[13.5px] outline-none placeholder:text-muted-foreground/70"
          />
          <button
            onClick={handleSend}
            disabled={uploading}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground disabled:opacity-40"
          >
            <Send className="h-3.5 w-3.5" strokeWidth={2} />
          </button>
        </div>
      </div>
    </>
  );
}

export function ChatLauncher() {
  const [open, setOpen] = useState(false);
  const { data: workspaces } = useWorkspaces();
  const workspace = workspaces?.[0];

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        // bottom-24 clears the fixed MobileTabBar below lg; at lg+ there's
        // no tab bar, so it drops back down to the usual corner position.
        className="fixed bottom-24 right-5 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-float transition-transform duration-200 hover:scale-105 active:scale-95 sm:right-8 lg:bottom-8"
      >
        <MessageSquare className="h-5 w-5" strokeWidth={1.9} />
      </button>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent
          side="right"
          className="flex w-full flex-col gap-0 border-l border-black/5 bg-white p-0 sm:max-w-sm [&>button]:hidden"
        >
          <SheetHeader className="flex-row items-center justify-between border-b border-black/[0.05] px-6 py-5 space-y-0">
            <SheetTitle className="text-[16px] font-semibold tracking-tight">Team Chat</SheetTitle>
            <button
              onClick={() => setOpen(false)}
              className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </SheetHeader>

          {workspace ? (
            <ChatBody workspaceId={workspace.id} />
          ) : (
            <div className="flex flex-1 items-center justify-center px-6">
              <p className="text-center text-[13.5px] text-muted-foreground">
                Create a workspace to start team chat.
              </p>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
