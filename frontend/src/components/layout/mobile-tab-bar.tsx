"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { navItems } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";

export function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex items-stretch justify-around border-t border-black/5 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md lg:hidden">
      {navItems.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className="relative flex flex-1 flex-col items-center gap-1 py-2.5 text-muted-foreground"
          >
            {active && (
              <motion.span
                layoutId="mobile-tab-active-pill"
                className="absolute inset-x-3 top-1 h-8 rounded-xl bg-secondary"
                transition={{ type: "spring", stiffness: 420, damping: 34 }}
              />
            )}
            <item.icon
              className={cn("relative z-10 h-5 w-5", active && "text-foreground")}
              strokeWidth={active ? 2.1 : 1.8}
            />
            <span className={cn("relative z-10 text-[10.5px] font-medium", active && "text-foreground")}>
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
