import { memo } from "react";
import { cn } from "@/lib/utils";

export const ProgressBar = memo(function ProgressBar({
  value,
  tone = "primary",
  className,
  "aria-label": ariaLabel,
}: {
  value: number;
  tone?: "primary" | "success" | "warning" | "danger" | "info";
  className?: string;
  "aria-label"?: string;
}) {
  const pct = Math.max(0, Math.min(100, value));
  const tones: Record<string, string> = {
    primary: "bg-foreground",
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-danger",
    info: "bg-info",
  };

  return (
    <div
      className={cn("h-1.5 w-full overflow-hidden rounded-[2px] bg-muted", className)}
      role="progressbar"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={ariaLabel}
    >
      <div
        className={cn(
          "h-full rounded-[2px] transition-[width] duration-500 ease-product",
          tones[tone],
        )}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
});
