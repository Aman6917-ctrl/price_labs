import { memo } from "react";
import { titleCase } from "@/lib/utils";
import type { ConfidenceLevel } from "@/types/api";
import { ProgressBar } from "./ProgressBar";

function toneFromScore(score: number): "success" | "warning" | "danger" {
  if (score >= 75) return "success";
  if (score >= 45) return "warning";
  return "danger";
}

export const ScoreMeter = memo(function ScoreMeter({
  label,
  score,
  level,
  hint,
}: {
  label: string;
  score: number;
  level?: ConfidenceLevel | string;
  hint?: string;
}) {
  const tone = toneFromScore(score);
  return (
    <div className="panel p-3.5 transition-colors duration-product hover:border-foreground/15">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[12px] font-medium text-muted-foreground">{label}</p>
        {level ? (
          <span className="text-[11px] font-medium text-muted-foreground">
            {titleCase(String(level))}
          </span>
        ) : null}
      </div>
      <p className="mt-1.5 text-[28px] font-semibold tracking-tight tabular text-foreground">
        {Math.round(score)}
        <span className="ml-0.5 text-[13px] font-medium text-muted-foreground">
          %
        </span>
      </p>
      <ProgressBar
        className="mt-2.5"
        value={score}
        tone={tone}
        aria-label={`${label} ${Math.round(score)} percent`}
      />
      {hint ? (
        <p className="mt-2 text-[11px] leading-4 text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
});
