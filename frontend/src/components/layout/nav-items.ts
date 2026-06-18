import { LayoutGrid, CalendarDays, Users, Disc, BarChart3, type LucideIcon } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const navItems: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutGrid },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
  { href: "/team", label: "Team", icon: Users },
  { href: "/recordings", label: "Recordings", icon: Disc },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];
