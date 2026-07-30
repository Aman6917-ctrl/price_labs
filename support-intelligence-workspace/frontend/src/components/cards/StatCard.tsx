import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/states";
import { cn, formatNumber } from "@/lib/utils";

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  loading,
  trend,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: LucideIcon;
  loading?: boolean;
  trend?: { label: string; positive?: boolean };
}) {
  if (loading) {
    return (
      <div className="panel p-4">
        <Skeleton className="mb-3 h-3 w-20" />
        <Skeleton className="h-7 w-14" />
        <Skeleton className="mt-2 h-3 w-24" />
      </div>
    );
  }

  return (
    <div className="panel group p-4 transition-colors duration-product hover:border-foreground/15">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[12px] font-medium text-muted-foreground">{label}</p>
        {Icon ? (
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-muted text-muted-foreground transition-colors group-hover:text-foreground">
            <Icon className="h-3.5 w-3.5" aria-hidden />
          </span>
        ) : null}
      </div>
      <p className="mt-2 text-[26px] font-semibold tracking-tight tabular text-foreground">
        {typeof value === "number" ? formatNumber(value) : value}
      </p>
      {hint ? (
        <p className="mt-1.5 text-[12px] leading-4 text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {trend ? (
        <p
          className={cn(
            "mt-1.5 text-[12px]",
            trend.positive ? "text-muted-foreground" : "text-muted-foreground",
          )}
        >
          {trend.label}
        </p>
      ) : null}
    </div>
  );
}

export function PageContainer({
  title,
  description,
  actions,
  children,
  className,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: [0.2, 0.8, 0.2, 1] }}
      className={cn("mx-auto w-full max-w-[1280px] space-y-5", className)}
    >
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-border pb-4">
        <div className="min-w-0">
          <h1 className="page-title">{title}</h1>
          {description ? <p className="page-desc">{description}</p> : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {children}
    </motion.div>
  );
}
