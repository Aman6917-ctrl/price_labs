import {
  AlertTriangle,
  CheckCircle2,
  Flag,
  ShieldAlert,
} from "lucide-react";
import { memo } from "react";
import { cn, titleCase } from "@/lib/utils";
import type { RecommendedAction } from "@/types/api";

const CONFIG: Record<
  RecommendedAction,
  {
    icon: typeof CheckCircle2;
    title: string;
    className: string;
  }
> = {
  send_response: {
    icon: CheckCircle2,
    title: "Send response",
    className: "border-success/25 bg-success/[0.06] text-success",
  },
  verify_documentation: {
    icon: AlertTriangle,
    title: "Verify documentation",
    className: "border-warning/25 bg-warning/[0.06] text-warning",
  },
  flag_knowledge_gap: {
    icon: Flag,
    title: "Flag knowledge gap",
    className: "border-warning/25 bg-warning/[0.06] text-warning",
  },
  escalate_to_human: {
    icon: ShieldAlert,
    title: "Escalate to human",
    className: "border-danger/25 bg-danger/[0.06] text-danger",
  },
};

export const ActionAlert = memo(function ActionAlert({
  action,
  reason,
}: {
  action: RecommendedAction;
  reason?: string | null;
}) {
  const cfg = CONFIG[action] ?? {
    icon: AlertTriangle,
    title: titleCase(action),
    className: "border-border bg-muted text-foreground",
  };
  const Icon = cfg.icon;

  return (
    <div
      role="status"
      className={cn(
        "flex items-start gap-3 rounded-md border px-3.5 py-3",
        cfg.className,
      )}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div className="min-w-0">
        <p className="text-[13px] font-semibold tracking-tight">{cfg.title}</p>
        {reason ? (
          <p className="mt-0.5 text-[13px] leading-5 opacity-90">{reason}</p>
        ) : (
          <p className="mt-0.5 text-[13px] leading-5 opacity-80">
            Recommended next step for the support engineer.
          </p>
        )}
      </div>
    </div>
  );
});
