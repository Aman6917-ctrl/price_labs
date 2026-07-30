import { Menu, Moon, Search, Sun, X } from "lucide-react";
import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  CommandPalette,
  useCommandPaletteHotkey,
} from "@/components/search/CommandPalette";
import { useTheme } from "@/context/theme";

export function Header({
  onMenuClick,
}: {
  onMenuClick?: () => void;
}) {
  const { theme, toggle } = useTheme();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const openPalette = useCallback(() => setPaletteOpen(true), []);
  useCommandPaletteHotkey(openPalette);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-card/95 px-3 backdrop-blur-sm md:px-5">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onMenuClick}
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </Button>

        <div className="min-w-0 md:w-40">
          <p className="truncate text-[13px] font-medium text-foreground">
            Default Workspace
          </p>
        </div>

        <button
          type="button"
          onClick={openPalette}
          className="relative mx-auto hidden h-8 w-full max-w-md items-center gap-2 rounded-md border border-border bg-background px-2.5 text-left text-[13px] text-muted-foreground transition-colors duration-product hover:border-foreground/20 hover:bg-accent md:flex"
          aria-label="Open search (Ctrl K)"
        >
          <Search className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span className="flex-1 truncate">Search pages, docs, gaps…</span>
          <kbd className="kbd">⌘K</kbd>
        </button>

        <div className="ml-auto flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={openPalette}
            aria-label="Search"
          >
            <Search className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={toggle}
            aria-label={
              theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
            }
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
          <div
            className="ml-1 flex h-7 w-7 items-center justify-center rounded-full border border-border bg-muted text-[10px] font-semibold tracking-wide text-foreground"
            aria-label="User avatar"
            title="Support Engineer"
          >
            SE
          </div>
        </div>
      </header>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </>
  );
}

export function MobileDrawerClose({ onClick }: { onClick: () => void }) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={onClick}
      aria-label="Close navigation"
    >
      <X className="h-4 w-4" />
    </Button>
  );
}
