import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileWarning } from "lucide-react";
import { fetchGaps } from "@/api";
import { SeverityBadge } from "@/components/badges";
import { PageContainer } from "@/components/cards/StatCard";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { formatDate, titleCase } from "@/lib/utils";
import type { KnowledgeGapReason } from "@/types/api";

const REASONS: Array<KnowledgeGapReason | "all"> = [
  "all",
  "missing_documentation",
  "outdated_documentation",
  "incorrect_documentation",
  "confusing_documentation",
];

const PAGE_SIZE = 8;

export function GapsPage() {
  const gaps = useQuery({ queryKey: ["gaps", 100], queryFn: () => fetchGaps(100) });
  const [search, setSearch] = useState("");
  const [reason, setReason] = useState<(typeof REASONS)[number]>("all");
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(0);

  const categories = useMemo(() => {
    const set = new Set((gaps.data ?? []).map((g) => g.category));
    return ["all", ...Array.from(set).sort()];
  }, [gaps.data]);

  const filtered = useMemo(() => {
    return (gaps.data ?? []).filter((g) => {
      if (reason !== "all" && g.reason !== reason) return false;
      if (category !== "all" && g.category !== category) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        const hay =
          `${g.topic ?? ""} ${g.description ?? ""} ${g.category} ${g.reason}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [gaps.data, reason, category, search]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageSafe = Math.min(page, pageCount - 1);
  const pageRows = filtered.slice(pageSafe * PAGE_SIZE, pageSafe * PAGE_SIZE + PAGE_SIZE);

  return (
    <PageContainer
      title="Knowledge Gaps"
      description="Engineering view of documentation issues flagged during Ask sessions."
      actions={
        <span className="text-[12px] tabular text-muted-foreground">
          {filtered.length} records
        </span>
      }
    >
      <div className="filter-bar">
        <Input
          className="max-w-xs"
          placeholder="Search gaps…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          aria-label="Search knowledge gaps"
        />
        <Select
          className="w-auto min-w-[160px]"
          value={reason}
          onChange={(e) => {
            setReason(e.target.value as (typeof REASONS)[number]);
            setPage(0);
          }}
          aria-label="Filter by reason"
        >
          {REASONS.map((r) => (
            <option key={r} value={r}>
              {r === "all" ? "All reasons" : titleCase(r)}
            </option>
          ))}
        </Select>
        <Select
          className="w-auto min-w-[140px]"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setPage(0);
          }}
          aria-label="Filter by category"
        >
          {categories.map((c) => (
            <option key={c} value={c}>
              {c === "all" ? "All categories" : c}
            </option>
          ))}
        </Select>
      </div>

      {gaps.isLoading ? (
        <Skeleton className="h-72 w-full" />
      ) : gaps.isError ? (
        <ErrorState
          description={
            gaps.error instanceof Error ? gaps.error.message : "Failed to load"
          }
          onRetry={() => gaps.refetch()}
        />
      ) : !filtered.length ? (
        <EmptyState
          icon={<FileWarning className="h-4 w-4" />}
          title="No knowledge gaps"
          description="Flag gaps from Ask Workspace when documentation is weak or missing."
        />
      ) : (
        <>
          <div className="panel overflow-x-auto">
            <table className="data-table min-w-[860px]">
              <thead>
                <tr>
                  <th>Topic / Question</th>
                  <th>Severity</th>
                  <th>Category</th>
                  <th>Created</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((g) => (
                  <tr key={g.id}>
                    <td>
                      <p className="font-medium text-foreground">
                        {g.topic || g.description || "Untitled gap"}
                      </p>
                      {g.description && g.topic ? (
                        <p className="mt-0.5 line-clamp-1 text-[12px] text-muted-foreground">
                          {g.description}
                        </p>
                      ) : null}
                    </td>
                    <td>
                      <SeverityBadge reason={g.reason} />
                    </td>
                    <td>
                      <span className="chip">{g.category}</span>
                    </td>
                    <td className="tabular text-muted-foreground">
                      {formatDate(g.created_at)}
                    </td>
                    <td>
                      <span className="inline-flex items-center gap-1.5 text-[12px] font-medium text-warning">
                        <span className="h-1.5 w-1.5 rounded-full bg-warning" />
                        Open
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-[12px] text-muted-foreground">
              Showing {pageSafe * PAGE_SIZE + 1}–
              {Math.min(filtered.length, (pageSafe + 1) * PAGE_SIZE)} of{" "}
              {filtered.length}
            </p>
            <div className="flex gap-1.5">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={pageSafe <= 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={pageSafe >= pageCount - 1}
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </PageContainer>
  );
}
