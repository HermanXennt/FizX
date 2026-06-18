"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutGrid,
  CalendarDays,
  Users,
  Disc,
  BarChart3,
  Settings,
  Sparkle,
  LogOut,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useLogout } from "@/hooks/use-auth";
import { useAuthStore } from "@/store/auth-store";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutGrid },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
  { href: "/team", label: "Team", icon: Users },
  { href: "/recordings", label: "Recordings", icon: Disc },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

const presenceDotColor: Record<string, string> = {
  online: "#34c759",
  in_call: "#1d1d1f",
  away: "#f5a623",
  do_not_disturb: "#ff3b30",
  offline: "#c7c7cc",
};

export function Sidebar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  return (
    <aside className="fixed left-6 top-6 bottom-6 z-40 hidden w-20 flex-col items-center justify-between rounded-[28px] border border-black/5 bg-white/95 py-6 shadow-soft-lg lg:flex">
      <div className="flex flex-col items-center gap-7">
        <Link
          href="/"
          className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-soft"
        >
          <Sparkle className="h-5 w-5" strokeWidth={2.25} fill="currentColor" />
        </Link>

        <nav className="flex flex-col items-center gap-2">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Tooltip key={item.href}>
                <TooltipTrigger
                  render={
                    <Link href={item.href} className="relative flex items-center justify-center" />
                  }
                >
                  {active && (
                    <motion.span
                      layoutId="sidebar-active-pill"
                      className="absolute inset-0 rounded-2xl bg-primary shadow-soft"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  )}
                  <span
                    className={cn(
                      "relative flex h-11 w-11 items-center justify-center rounded-2xl transition-colors duration-200",
                      active
                        ? "text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    )}
                  >
                    <item.icon className="h-[19px] w-[19px]" strokeWidth={1.9} />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={12}>
                  {item.label}
                </TooltipContent>
              </Tooltip>
            );
          })}
        </nav>
      </div>

      <div className="flex flex-col items-center gap-4">
        <Tooltip>
          <TooltipTrigger
            render={
              <Link
                href="/settings"
                className={cn(
                  "flex h-11 w-11 items-center justify-center rounded-2xl transition-colors duration-200",
                  pathname === "/settings"
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              />
            }
          >
            <Settings className="h-[19px] w-[19px]" strokeWidth={1.9} />
          </TooltipTrigger>
          <TooltipContent side="right" sideOffset={12}>
            Settings
          </TooltipContent>
        </Tooltip>

        <div className="h-px w-8 bg-border" />

        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <button className="relative flex h-10 w-10 items-center justify-center rounded-full bg-[#1d1d1f] text-[13px] font-semibold text-white">
                {user?.initials ?? "?"}
                <span
                  className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white"
                  style={{ backgroundColor: presenceDotColor[user?.presence_status ?? "offline"] }}
                />
              </button>
            }
          />
          <DropdownMenuContent side="right" align="end" className="w-44 rounded-2xl p-1.5">
            <div className="px-2 py-1.5">
              <p className="truncate text-[13px] font-medium">{user?.full_name}</p>
              <p className="truncate text-[11.5px] text-muted-foreground">{user?.email}</p>
            </div>
            <DropdownMenuItem onClick={() => logout.mutate()} className="rounded-xl py-1.5 text-[13px]">
              <LogOut className="h-3.5 w-3.5" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
}
