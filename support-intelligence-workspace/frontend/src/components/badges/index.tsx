import { cn, titleCase } from "@/lib/utils";
import type {
  AnswerQuality,
  ConfidenceLevel,
  DocumentHealth,
  RecommendedAction,
} from "@/types/api";

const badgeBase =
  "inline-flex items-center gap-1 rounded-[5px] border px-1.5 py-0.5 text-[11px] font-medium tabular leading-4";

export function MetricBadge({
  label,
  value,
  tone = "neutral",
}: {
  label?: string;
  value: string;
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
}) {
  const tones = {
    neutral: "border-border bg-muted/80 text-foreground",
    success: "border-success/20 bg-success/[0.08] text-success",
    warning: "border-warning/20 bg-warning/[0.08] text-warning",
    danger: "border-danger/20 bg-danger/[0.08] text-danger",
    info: "border-info/20 bg-info/[0.08] text-info",
  };
  return (
    <span className={cn(badgeBase, tones[tone])}>
      {label ? <span className="opacity-60">{label}</span> : null}
      {value}
    </span>
  );
}

export function ConfidenceBadge({
  level,
  score,
}: {
  level: ConfidenceLevel;
  score?: number;
}) {
  const tone =
    level === "high" ? "success" : level === "medium" ? "warning" : "danger";
  const text =
    score !== undefined
      ? `${titleCase(level)} · ${Math.round(score)}`
      : titleCase(level);
  return <MetricBadge tone={tone} value={text} />;
}

export function CoverageBadge({ score }: { score: number }) {
  const tone = score >= 85 ? "success" : score >= 50 ? "warning" : "danger";
  return <MetricBadge tone={tone} value={`${Math.round(score)}%`} />;
}

export function QualityBadge({ label }: { label: AnswerQuality }) {
  const tone =
    label === "excellent"
      ? "success"
      : label === "good"
        ? "info"
        : label === "needs_review"
          ? "warning"
          : "danger";
  return <MetricBadge tone={tone} value={titleCase(label)} />;
}

export function HealthBadge({
  health,
}: {
  health: DocumentHealth | "unknown" | string;
}) {
  const normalized = (health || "unknown") as DocumentHealth | "unknown";
  const tone =
    normalized === "healthy"
      ? "success"
      : normalized === "needs_review"
        ? "warning"
        : normalized === "outdated"
          ? "danger"
          : "neutral";
  const label =
    normalized === "healthy"
      ? "Healthy"
      : normalized === "needs_review"
        ? "Needs review"
        : normalized === "outdated"
          ? "Outdated"
          : "Unknown";
  return <MetricBadge tone={tone} value={label} />;
}

export function ActionBadge({ action }: { action: RecommendedAction }) {
  const tone =
    action === "send_response"
      ? "success"
      : action === "escalate_to_human"
        ? "danger"
        : "warning";
  return <MetricBadge tone={tone} value={titleCase(action)} />;
}

export function SeverityBadge({ reason }: { reason: string }) {
  const tone =
    reason.includes("missing") || reason.includes("incorrect")
      ? "danger"
      : reason.includes("outdated")
        ? "warning"
        : "info";
  return <MetricBadge tone={tone} value={titleCase(reason)} />;
}
