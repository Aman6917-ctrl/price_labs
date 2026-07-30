import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, FileText, X } from "lucide-react";
import { fetchDocumentStats, fetchDocuments } from "@/api";
import { HealthBadge } from "@/components/badges";
import { DocumentRowStats } from "@/components/cards/DocumentCard";
import { PageContainer } from "@/components/cards/StatCard";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { formatDate, formatNumber, formatPercent } from "@/lib/utils";
import type { DocumentHealth, DocumentRecord } from "@/types/api";

type SortKey = "health" | "retrievals" | "gaps" | "title";

export function DocumentsPage() {
  const docs = useQuery({
    queryKey: ["documents"],
    queryFn: () => fetchDocuments(200),
  });
  const [search, setSearch] = useState("");
  const [health, setHealth] = useState<DocumentHealth | "all">("all");
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState<SortKey>("retrievals");
  const [selected, setSelected] = useState<DocumentRecord | null>(null);

  const categories = useMemo(() => {
    const set = new Set((docs.data ?? []).map((d) => d.category));
    return ["all", ...Array.from(set).sort()];
  }, [docs.data]);

  const filtered = useMemo(() => {
    let rows = [...(docs.data ?? [])];
    if (health !== "all") rows = rows.filter((d) => d.health === health);
    if (category !== "all") rows = rows.filter((d) => d.category === category);
    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (d) =>
          d.title.toLowerCase().includes(q) ||
          d.document_id.toLowerCase().includes(q) ||
          d.category.toLowerCase().includes(q),
      );
    }
    rows.sort((a, b) => {
      if (sort === "title") return a.title.localeCompare(b.title);
      if (sort === "retrievals") return b.retrieval_count - a.retrieval_count;
      if (sort === "gaps") return b.knowledge_gap_count - a.knowledge_gap_count;
      return a.health.localeCompare(b.health);
    });
    return rows;
  }, [docs.data, health, category, search, sort]);

  return (
    <PageContainer
      title="Documents"
      description="Internal knowledge-base registry — browse health, retrievals, and gap signals."
      actions={
        <span className="text-[12px] tabular text-muted-foreground">
          {filtered.length} documents
        </span>
      }
    >
      <div className="filter-bar">
        <Input
          className="max-w-xs"
          placeholder="Search documents…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search documents"
        />
        <Select
          className="w-auto min-w-[130px]"
          value={health}
          onChange={(e) => setHealth(e.target.value as DocumentHealth | "all")}
          aria-label="Filter by health"
        >
          <option value="all">All health</option>
          <option value="healthy">Healthy</option>
          <option value="needs_review">Needs Review</option>
          <option value="outdated">Outdated</option>
        </Select>
        <Select
          className="w-auto min-w-[140px]"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          aria-label="Filter by category"
        >
          {categories.map((c) => (
            <option key={c} value={c}>
              {c === "all" ? "All categories" : c}
            </option>
          ))}
        </Select>
        <Select
          className="w-auto min-w-[150px]"
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          aria-label="Sort documents"
        >
          <option value="retrievals">Sort: Retrievals</option>
          <option value="gaps">Sort: Knowledge Gaps</option>
          <option value="health">Sort: Health</option>
          <option value="title">Sort: Title</option>
        </Select>
      </div>

      {docs.isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-36 w-full" />
          ))}
        </div>
      ) : docs.isError ? (
        <ErrorState
          description={
            docs.error instanceof Error ? docs.error.message : "Failed to load"
          }
          onRetry={() => docs.refetch()}
        />
      ) : !filtered.length ? (
        <EmptyState
          icon={<BookOpen className="h-4 w-4" />}
          title="No documents in registry"
          description="Ingest the knowledge base, then Ask to populate retrieval stats."
        />
      ) : (
        <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((d) => (
            <button
              key={d.document_id}
              type="button"
              onClick={() => setSelected(d)}
              className="panel p-3.5 text-left transition-colors duration-product hover:border-foreground/15 focus-visible:border-foreground/25"
            >
              <div className="flex items-start gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-muted text-muted-foreground">
                  <FileText className="h-3.5 w-3.5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold">{d.title}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    <span className="chip">{d.category}</span>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      v{d.version}
                    </span>
                    <HealthBadge health={d.health} />
                  </div>
                  <p className="mt-2 line-clamp-2 text-[12px] leading-4 text-muted-foreground">
                    {d.source || d.document_id}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-3 border-t border-border pt-2.5 text-[11px] text-muted-foreground">
                    <span>
                      Retrievals{" "}
                      <strong className="tabular text-foreground">
                        {formatNumber(d.retrieval_count)}
                      </strong>
                    </span>
                    <span>
                      Updated{" "}
                      <strong className="text-foreground">
                        {formatDate(
                          typeof d.last_updated === "string"
                            ? d.last_updated
                            : d.updated_at,
                        )}
                      </strong>
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {selected ? (
        <DocumentDrawer doc={selected} onClose={() => setSelected(null)} />
      ) : null}
    </PageContainer>
  );
}

function DocumentDrawer({
  doc,
  onClose,
}: {
  doc: DocumentRecord;
  onClose: () => void;
}) {
  const stats = useQuery({
    queryKey: ["document-stats", doc.document_id],
    queryFn: () => fetchDocumentStats(doc.document_id),
  });

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end bg-foreground/20"
      role="dialog"
      aria-modal="true"
      aria-label="Document details"
      onClick={onClose}
    >
      <div
        className="flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-2 border-b border-border px-4 py-3">
          <div className="min-w-0">
            <h2 className="text-[15px] font-semibold tracking-tight">
              {doc.title}
            </h2>
            <p className="mt-0.5 truncate font-mono text-[11px] text-muted-foreground">
              {doc.document_id}
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="space-y-5 overflow-auto p-4">
          <div className="flex flex-wrap gap-1.5">
            <HealthBadge health={doc.health} />
            <span className="chip">{doc.category}</span>
            <span className="chip">v{doc.version}</span>
          </div>

          <section>
            <h3 className="section-label">Preview</h3>
            <p className="mt-2 border border-border bg-muted/40 p-3 text-[13px] leading-5 text-muted-foreground">
              {doc.source || "No preview available for this registry entry."}
            </p>
          </section>

          <section>
            <h3 className="section-label">Statistics</h3>
            <div className="mt-2">
              {stats.isLoading ? (
                <Skeleton className="h-16 w-full" />
              ) : (
                <DocumentRowStats doc={doc} />
              )}
            </div>
            <dl className="mt-3 space-y-2 border border-border p-3 text-[13px]">
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Avg coverage</dt>
                <dd className="tabular">
                  {formatPercent(
                    stats.data?.average_coverage ?? doc.average_coverage ?? null,
                  )}
                </dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Avg quality</dt>
                <dd className="tabular">
                  {formatPercent(
                    stats.data?.average_quality ?? doc.average_quality ?? null,
                  )}
                </dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Last retrieved</dt>
                <dd>
                  {formatDate(
                    stats.data?.last_retrieved ?? doc.last_retrieved ?? null,
                  )}
                </dd>
              </div>
            </dl>
          </section>
        </div>
      </div>
    </div>
  );
}
