"use client";

import { useState } from "react";
import { Search, Bell, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCreateInstantMeeting } from "@/hooks/use-meetings";
import { useNotifications } from "@/hooks/use-notifications";
import { useAuthStore } from "@/store/auth-store";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function Topbar({
  title,
  subtitle,
}: {
  title?: string;
  subtitle?: string;
}) {
  const user = useAuthStore((s) => s.user);
  const createInstant = useCreateInstantMeeting();
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications();
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <header className="flex items-center justify-between gap-6 pb-10">
      <div>
        <h1 className="text-[28px] font-semibold tracking-tight text-foreground">
          {title ?? `${getGreeting()}, ${user?.first_name || "there"}`}
        </h1>
        <p className="mt-1.5 text-[15px] text-muted-foreground">
          {subtitle ?? "Here's what's happening across your workspace today."}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative hidden md:block">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search meetings, people…"
            className="h-11 w-64 rounded-full border-black/5 bg-white pl-10 text-[14px] shadow-soft-sm placeholder:text-muted-foreground/70 focus-visible:ring-black/10"
          />
        </div>

        <DropdownMenu open={notifOpen} onOpenChange={setNotifOpen}>
          <DropdownMenuTrigger
            render={
              <button
                type="button"
                className="relative flex h-11 w-11 items-center justify-center rounded-full border border-black/5 bg-white shadow-soft-sm hover:bg-accent"
              >
                <Bell className="h-[18px] w-[18px] text-foreground/80" strokeWidth={1.9} />
                {unreadCount > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#d4493c] px-1 text-[10px] font-semibold text-white">
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </span>
                )}
              </button>
            }
          />
          <DropdownMenuContent align="end" className="w-80 rounded-2xl p-2">
            <div className="flex items-center justify-between px-2 py-1.5">
              <span className="text-[13px] font-semibold">Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead()}
                  className="text-[12px] text-muted-foreground hover:text-foreground"
                >
                  Mark all read
                </button>
              )}
            </div>
            {notifications.length === 0 && (
              <p className="px-2 py-4 text-center text-[12.5px] text-muted-foreground">No notifications yet.</p>
            )}
            {notifications.slice(0, 8).map((n) => (
              <DropdownMenuItem
                key={n.id}
                onClick={() => !n.is_read && markRead(n.id)}
                className="flex flex-col items-start gap-0.5 rounded-xl py-2"
              >
                <span className={`text-[13px] ${n.is_read ? "font-normal text-foreground/70" : "font-medium"}`}>
                  {n.title}
                </span>
                {n.body && <span className="text-[11.5px] text-muted-foreground">{n.body}</span>}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          onClick={() => createInstant.mutate({})}
          disabled={createInstant.isPending}
          className="h-11 rounded-full bg-primary px-5 text-[14px] font-medium text-primary-foreground shadow-soft hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" strokeWidth={2.2} />
          {createInstant.isPending ? "Starting…" : "New Meeting"}
        </Button>
      </div>
    </header>
  );
}
