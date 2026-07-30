import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Bot,
  Database,
  Moon,
  Server,
  Sparkles,
  Sun,
} from "lucide-react";
import { PageContainer } from "@/components/cards/StatCard";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/context/theme";
import { cn } from "@/lib/utils";

async function pingHealth(): Promise<{
  status: string;
  mongodb?: boolean;
}> {
  const res = await fetch("/health");
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json() as Promise<{ status: string; mongodb?: boolean }>;
}

export function SettingsPage() {
  const { theme, toggle, setTheme } = useTheme();
  const health = useQuery({
    queryKey: ["health"],
    queryFn: pingHealth,
    refetchInterval: 30_000,
  });

  return (
    <PageContainer
      title="Settings"
      description="Workspace preferences, provider configuration, and runtime health."
    >
      <div className="grid gap-3 lg:grid-cols-2">
        <section className="panel p-4 md:p-5">
          <h2 className="text-[13px] font-semibold">Appearance</h2>
          <p className="mt-1 text-[12px] text-muted-foreground">
            Theme preference is saved in this browser.
          </p>
          <div className="mt-4 inline-flex rounded-md border border-border p-0.5">
            <Button
              type="button"
              variant={theme === "light" ? "secondary" : "ghost"}
              size="sm"
              className={cn("h-7", theme === "light" && "bg-muted shadow-xs")}
              onClick={() => setTheme("light")}
            >
              <Sun className="h-3.5 w-3.5" /> Light
            </Button>
            <Button
              type="button"
              variant={theme === "dark" ? "secondary" : "ghost"}
              size="sm"
              className={cn("h-7", theme === "dark" && "bg-muted shadow-xs")}
              onClick={() => setTheme("dark")}
            >
              <Moon className="h-3.5 w-3.5" /> Dark
            </Button>
            <Button type="button" variant="ghost" size="sm" className="h-7" onClick={toggle}>
              Toggle
            </Button>
          </div>
        </section>

        <section className="panel p-4 md:p-5">
          <h2 className="text-[13px] font-semibold">Runtime status</h2>
          <dl className="mt-3 space-y-2 text-[13px]">
            <StatusRow
              icon={Server}
              label="Backend API"
              value={
                health.isLoading
                  ? "Checking…"
                  : health.isError
                    ? "Offline"
                    : health.data?.status === "ok"
                      ? "Online"
                      : "Degraded"
              }
              ok={!health.isError && health.data?.status === "ok"}
            />
            <StatusRow
              icon={Database}
              label="MongoDB"
              value={
                health.isLoading
                  ? "Checking…"
                  : health.data?.mongodb
                    ? "Connected"
                    : "Unavailable"
              }
              ok={Boolean(health.data?.mongodb)}
            />
            <StatusRow icon={Activity} label="Vector database" value="Chroma" ok />
          </dl>
        </section>

        <section className="panel p-4 md:p-5 lg:col-span-2">
          <h2 className="text-[13px] font-semibold">Provider information</h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <InfoTile icon={Bot} label="LLM Provider" value="Anthropic" />
            <InfoTile icon={Sparkles} label="Current LLM" value="Claude Sonnet 5" />
            <InfoTile
              icon={Activity}
              label="Embedding Model"
              value="MiniLM (all-MiniLM-L6-v2)"
            />
            <InfoTile icon={Database} label="Vector Database" value="Chroma" />
          </div>
        </section>

        <section className="panel p-4 md:p-5 lg:col-span-2">
          <h2 className="text-[13px] font-semibold">Future integrations</h2>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {[
              "Zendesk / Intercom / Freshdesk ticket sync",
              "GitHub Docs + Confluence automatic ingestion",
              "Slack notifications for critical knowledge gaps",
              "SSO / RBAC for multi-workspace accounts",
            ].map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 border border-border px-3 py-2.5 text-[13px] text-muted-foreground"
              >
                <span
                  className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/50"
                  aria-hidden
                />
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </PageContainer>
  );
}

function StatusRow({
  icon: Icon,
  label,
  value,
  ok,
}: {
  icon: typeof Server;
  label: string;
  value: string;
  ok?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border border-border px-3 py-2.5">
      <div className="flex items-center gap-2">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
        <span>{label}</span>
      </div>
      <span
        className={cn(
          "inline-flex items-center gap-1.5 text-[12px] font-medium",
          ok ? "text-success" : "text-danger",
        )}
      >
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            ok ? "bg-success" : "bg-danger",
          )}
        />
        {value}
      </span>
    </div>
  );
}

function InfoTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Bot;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-border bg-muted/30 p-3">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        <span className="text-[11px] font-medium uppercase tracking-[0.04em]">
          {label}
        </span>
      </div>
      <p className="mt-2 text-[13px] font-semibold text-foreground">{value}</p>
    </div>
  );
}
