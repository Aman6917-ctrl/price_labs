import { NavLink } from "react-router-dom";
import {
  BarChart3,
  BookOpen,
  FileWarning,
  LayoutDashboard,
  MessageSquareText,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { MobileDrawerClose } from "./Header";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/ask", label: "Ask", icon: MessageSquareText },
  { to: "/gaps", label: "Knowledge Gaps", icon: FileWarning },
  { to: "/documents", label: "Documents", icon: BookOpen },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar({
  mobileOpen,
  onClose,
}: {
  mobileOpen?: boolean;
  onClose?: () => void;
}) {
  return (
    <>
      <div
        className={cn(
          "fixed inset-0 z-40 bg-foreground/20 transition-opacity duration-200 md:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onClose}
        aria-hidden
      />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[232px] flex-col border-r border-border bg-sidebar transition-transform duration-200 md:static md:z-0 md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-14 items-center justify-between gap-2 border-b border-border px-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span
                className="flex h-6 w-6 items-center justify-center rounded-[5px] bg-foreground text-[10px] font-bold tracking-tight text-background"
                aria-hidden
              >
                PL
              </span>
              <div className="min-w-0">
                <p className="truncate text-[13px] font-semibold tracking-tight text-foreground">
                  Support Intel
                </p>
                <p className="truncate text-[11px] text-muted-foreground">
                  PriceLabs internal
                </p>
              </div>
            </div>
          </div>
          <div className="md:hidden">
            {onClose ? <MobileDrawerClose onClick={onClose} /> : null}
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 p-2" aria-label="Primary">
          <p className="section-label px-2.5 pb-1.5 pt-2">Workspace</p>
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "group relative flex h-8 items-center gap-2.5 rounded-md px-2.5 text-[13px] transition-colors duration-product",
                  isActive
                    ? "bg-sidebar-active font-medium text-foreground"
                    : "text-sidebar-foreground hover:bg-accent hover:text-foreground",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive ? (
                    <span
                      className="absolute left-0 top-1.5 h-5 w-[2px] rounded-r bg-foreground"
                      aria-hidden
                    />
                  ) : null}
                  <item.icon
                    className={cn(
                      "h-[15px] w-[15px] shrink-0",
                      isActive ? "text-foreground" : "text-muted-foreground",
                    )}
                    aria-hidden
                  />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border px-4 py-3">
          <p className="text-[11px] leading-4 text-muted-foreground">
            Support Engineering
          </p>
          <p className="mt-0.5 font-mono text-[10px] text-muted-foreground/80">
            v1.0 · MVP
          </p>
        </div>
      </aside>
    </>
  );
}
