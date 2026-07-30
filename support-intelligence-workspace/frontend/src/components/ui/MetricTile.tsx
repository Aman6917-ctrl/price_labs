import type { LucideIcon } from "lucide-react";
import { memo } from "react";
import { formatMs } from "@/lib/utils";

export const MetricTile = memo(function MetricTile({
  label,
  valueMs,
  icon: Icon,
}: {
  label: string;
  valueMs: number;
  icon: LucideIcon;
}) {
  return (
    <div className="panel group p-3 transition-colors duration-product hover:border-foreground/15">
      <div className="flex items-center gap-2 text-muted-foreground">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-muted text-foreground">
          <Icon className="h-3.5 w-3.5" aria-hidden />
        </span>
        <span className="text-[11px] font-medium uppercase tracking-[0.04em]">
          {label}
        </span>
      </div>
      <p className="mt-2.5 text-xl font-semibold tracking-tight tabular text-foreground">
        {formatMs(valueMs)}
      </p>
    </div>
  );
});
