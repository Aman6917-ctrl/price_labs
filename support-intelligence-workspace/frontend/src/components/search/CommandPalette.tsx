import * as Dialog from "@radix-ui/react-dialog";
import {
  BarChart3,
  BookOpen,
  FileWarning,
  LayoutDashboard,
  MessageSquareText,
  Search,
  Settings,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";

const RECENT_KEY = "siw-recent-searches";

const SHORTCUTS = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Ask Workspace", path: "/ask", icon: MessageSquareText },
  { label: "Knowledge Gaps", path: "/gaps", icon: FileWarning },
  { label: "Documents", path: "/documents", icon: BookOpen },
  { label: "Analytics", path: "/analytics", icon: BarChart3 },
  { label: "Settings", path: "/settings", icon: Settings },
];

function loadRecent(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function saveRecent(term: string) {
  const next = [term, ...loadRecent().filter((t) => t !== term)].slice(0, 6);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
}

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [recent, setRecent] = useState<string[]>(() => loadRecent());

  useEffect(() => {
    if (open) {
      setRecent(loadRecent());
      setQuery("");
    }
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return SHORTCUTS;
    return SHORTCUTS.filter((s) => s.label.toLowerCase().includes(q));
  }, [query]);

  function go(path: string, label: string) {
    if (query.trim()) saveRecent(query.trim());
    else saveRecent(label);
    onOpenChange(false);
    navigate(path);
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-foreground/25 data-[state=open]:animate-in" />
        <Dialog.Content
          className="fixed left-1/2 top-[16%] z-50 w-[min(520px,calc(100vw-2rem))] -translate-x-1/2 overflow-hidden rounded-lg border border-border bg-card shadow-md focus:outline-none"
          aria-label="Command palette"
        >
          <Dialog.Title className="sr-only">Search workspace</Dialog.Title>
          <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
            <Search className="h-4 w-4 text-muted-foreground" aria-hidden />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Jump to a page…"
              className="h-7 w-full bg-transparent text-[13px] outline-none placeholder:text-muted-foreground"
              aria-label="Search query"
            />
            <kbd className="kbd hidden sm:inline">ESC</kbd>
          </div>

          {!query && recent.length ? (
            <div className="border-b border-border px-2 py-2">
              <p className="section-label px-2 pb-1">Recent</p>
              <ul>
                {recent.map((term) => (
                  <li key={term}>
                    <button
                      type="button"
                      className="flex w-full items-center rounded-md px-2 py-1.5 text-left text-[13px] hover:bg-accent"
                      onClick={() => setQuery(term)}
                    >
                      {term}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <ul className="max-h-72 overflow-auto p-1.5">
            {results.map((item) => (
              <li key={item.path}>
                <button
                  type="button"
                  onClick={() => go(item.path, item.label)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-[13px]",
                    "hover:bg-accent focus-visible:bg-accent",
                  )}
                >
                  <item.icon className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="flex-1">{item.label}</span>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    ↵
                  </span>
                </button>
              </li>
            ))}
            {!results.length ? (
              <li className="px-3 py-8 text-center text-[13px] text-muted-foreground">
                No matches
              </li>
            ) : null}
          </ul>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function useCommandPaletteHotkey(onOpen: () => void) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpen();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onOpen]);
}
