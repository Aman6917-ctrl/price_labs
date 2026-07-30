import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  Clock3,
  Coins,
  FileWarning,
  Percent,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useMemo } from "react";
import { Link } from "react-router-dom";
import { fetchAnalytics, fetchGaps } from "@/api";
import { ActionBadge, SeverityBadge } from "@/components/badges";
import { PageContainer, StatCard } from "@/components/cards/StatCard";
import {
  DistributionPieChart,
  NamedCountBarChart,
  TrendLineChart,
} from "@/components/charts/AnalyticsChart";
import { Button } from "@/components/ui/button";
import { ErrorState, Skeleton } from "@/components/ui/states";
import {
  formatMs,
  formatNumber,
  formatPercent,
  titleCase,
} from "@/lib/utils";
import type { RecommendedAction } from "@/types/api";

export function DashboardPage() {
  const analytics = useQuery({ queryKey: ["analytics"], queryFn: fetchAnalytics });
  const gaps = useQuery({ queryKey: ["gaps"], queryFn: () => fetchGaps(8) });

  const data = analytics.data;
  const loading = analytics.isLoading;
  const healthScore = data
    ? healthScoreFromDistribution(data.document_health_distribution)
    : null;

  const volumeTrend = useMemo(() => {
    const today = data?.questions_today ?? 0;
    const week = data?.questions_this_week ?? 0;
    const rest = Math.max(0, week - today);
    return [
      { name: "Earlier", value: Math.round(rest * 0.45) },
      { name: "Mid-week", value: Math.round(rest * 0.55) },
      { name: "Today", value: today },
    ];
  }, [data]);

  return (
    <PageContainer
      title="Dashboard"
      description="Operational pulse for support intelligence — confidence, gaps, and document health at a glance."
      actions={
        <Button asChild size="sm">
          <Link to="/ask">Open Ask Workspace</Link>
        </Button>
      }
    >
      {analytics.isError ? (
        <ErrorState
          description={
            analytics.error instanceof Error
              ? analytics.error.message
              : "Failed to load analytics"
          }
          onRetry={() => analytics.refetch()}
        />
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          loading={loading}
          label="Questions today"
          value={data?.questions_today ?? 0}
          icon={Activity}
          trend={{
            label: `${data?.questions_this_week ?? 0} this week`,
            positive: true,
          }}
        />
        <StatCard
          loading={loading}
          label="Knowledge gaps"
          value={data?.knowledge_gaps_total ?? 0}
          icon={FileWarning}
        />
        <StatCard
          loading={loading}
          label="Average confidence"
          value={formatPercent(data?.average_confidence ?? null)}
          icon={ShieldCheck}
        />
        <StatCard
          loading={loading}
          label="Avg response time"
          value={formatMs(data?.average_processing_time_ms ?? null)}
          icon={Clock3}
        />
        <StatCard
          loading={loading}
          label="Average coverage"
          value={formatPercent(data?.average_coverage ?? null)}
          icon={Activity}
        />
        <StatCard
          loading={loading}
          label="Positive feedback"
          value={formatPercent(data?.positive_feedback_pct ?? null)}
          icon={Percent}
        />
        <StatCard
          loading={loading}
          label="Claude tokens"
          value={
            data?.total_tokens != null ? formatNumber(data.total_tokens) : "—"
          }
          hint={
            data?.questions_total
              ? `Across ${data.questions_total} persisted questions`
              : "From Ask rag_meta when available"
          }
          icon={Zap}
        />
        <StatCard
          loading={loading}
          label="Est. API cost"
          value={
            data?.estimated_cost_usd != null
              ? `$${Number(data.estimated_cost_usd).toFixed(4)}`
              : "—"
          }
          icon={Coins}
        />
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendLineChart
            title="Question volume signal"
            data={volumeTrend}
          />
        </div>
        <DistributionPieChart
          title="Document health"
          data={data?.document_health_distribution ?? {}}
        />
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <section className="panel p-4">
          <h2 className="text-[13px] font-semibold">Recommended actions</h2>
          <div className="mt-3 space-y-1.5">
            {loading ? (
              <>
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
              </>
            ) : data &&
              Object.keys(data.recommended_action_distribution).length > 0 ? (
              Object.entries(data.recommended_action_distribution).map(
                ([action, count]) => (
                  <div
                    key={action}
                    className="flex items-center justify-between gap-2 border border-border px-2.5 py-2"
                  >
                    <ActionBadge action={action as RecommendedAction} />
                    <span className="text-[13px] tabular text-muted-foreground">
                      {formatNumber(count)}
                    </span>
                  </div>
                ),
              )
            ) : (
              <p className="text-[13px] text-muted-foreground">
                No action data yet. Run Ask Workspace first.
              </p>
            )}
          </div>
        </section>

        <NamedCountBarChart
          title="Most retrieved documents"
          items={data?.most_retrieved_documents ?? []}
        />

        <section className="panel p-4">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-[13px] font-semibold">Recent knowledge gaps</h2>
            <Button asChild variant="ghost" size="sm" className="h-7 px-2">
              <Link to="/gaps">View all</Link>
            </Button>
          </div>
          <div className="mt-3 space-y-1.5">
            {gaps.isLoading ? (
              <Skeleton className="h-28 w-full" />
            ) : gaps.isError ? (
              <ErrorState
                description="Could not load gaps"
                onRetry={() => gaps.refetch()}
              />
            ) : gaps.data?.length ? (
              gaps.data.slice(0, 6).map((g) => (
                <div
                  key={g.id}
                  className="border border-border px-2.5 py-2 transition-colors hover:bg-accent/50"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-warning" />
                    <p className="truncate text-[13px] font-medium">
                      {g.topic || titleCase(g.reason)}
                    </p>
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                    <SeverityBadge reason={g.reason} />
                    <span className="text-[11px] text-muted-foreground">
                      {g.category}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-[13px] text-muted-foreground">
                No recent reports.
              </p>
            )}
          </div>
          {healthScore != null ? (
            <p className="mt-3 border-t border-border pt-3 text-[12px] text-muted-foreground">
              Doc health index{" "}
              <span className="font-semibold tabular text-foreground">
                {healthScore}
              </span>
            </p>
          ) : null}
        </section>
      </div>
    </PageContainer>
  );
}

function healthScoreFromDistribution(dist: Record<string, number>): number | null {
  const healthy = dist.healthy ?? 0;
  const review = dist.needs_review ?? 0;
  const outdated = dist.outdated ?? 0;
  const total = healthy + review + outdated;
  if (!total) return null;
  return Math.round((healthy * 100 + review * 55 + outdated * 20) / total);
}
