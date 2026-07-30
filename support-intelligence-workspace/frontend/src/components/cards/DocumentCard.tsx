import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown, Copy, FileText } from "lucide-react";
import { memo, useState } from "react";
import { toast } from "sonner";
import { HealthBadge } from "@/components/badges";
import { Button } from "@/components/ui/button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { formatDate, formatNumber, formatPercent } from "@/lib/utils";
import type { DocumentHealth, DocumentRecord, RetrievedDocument } from "@/types/api";

export const DocumentCard = memo(function DocumentCard({
  doc,
  health,
}: {
  doc: RetrievedDocument;
  health?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const similarityPct = Math.round(doc.similarity * 100);
  const tone =
    similarityPct >= 75 ? "success" : similarityPct >= 45 ? "warning" : "danger";

  return (
    <article className="panel p-3.5 transition-colors duration-product hover:border-foreground/15">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-muted text-muted-foreground">
          <FileText className="h-3.5 w-3.5" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="truncate text-[13px] font-semibold text-foreground">
                {doc.title}
              </h3>
              <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                <span className="chip">{doc.category}</span>
                <span className="font-mono text-[11px] text-muted-foreground">
                  v{doc.version}
                </span>
                <HealthBadge
                  health={(health as DocumentHealth) || "unknown"}
                />
              </div>
            </div>
            <span className="text-[13px] font-semibold tabular text-foreground">
              {similarityPct}%
            </span>
          </div>

          <div className="mt-3">
            <div className="mb-1 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Similarity</span>
              <span className="tabular">{similarityPct}%</span>
            </div>
            <ProgressBar
              value={similarityPct}
              tone={tone}
              aria-label="Similarity"
            />
          </div>

          <p className="mt-2 text-[11px] text-muted-foreground">
            Updated {formatDate(doc.last_updated)}
          </p>

          {doc.excerpt ? (
            <>
              <AnimatePresence initial={false}>
                {expanded ? (
                  <motion.p
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-2 overflow-hidden text-[12px] leading-5 text-muted-foreground"
                  >
                    {doc.excerpt}
                  </motion.p>
                ) : (
                  <p className="mt-2 line-clamp-2 text-[12px] leading-5 text-muted-foreground">
                    {doc.excerpt}
                  </p>
                )}
              </AnimatePresence>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="mt-1 h-7 px-2"
                onClick={() => setExpanded((v) => !v)}
                aria-expanded={expanded}
              >
                {expanded ? "Show less" : "Read more"}
                <ChevronDown
                  className={`h-3.5 w-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
                />
              </Button>
            </>
          ) : null}
        </div>
      </div>
    </article>
  );
});

export const CitationCard = memo(function CitationCard({
  title,
  category,
  similarity,
  excerpt,
}: {
  title: string;
  category: string;
  similarity: number;
  excerpt?: string | null;
}) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const similarityPct = Math.round(similarity * 100);

  return (
    <article className="panel p-3.5 transition-colors duration-product hover:border-foreground/15">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-foreground">{title}</p>
          <p className="mt-0.5 text-[12px] text-muted-foreground">{category}</p>
        </div>
        <span className="shrink-0 rounded-md border border-border bg-muted px-1.5 py-0.5 text-[11px] font-semibold tabular text-foreground">
          {similarityPct}%
        </span>
      </div>

      {excerpt ? (
        <>
          <p
            className={`mt-2 text-[12px] leading-5 text-muted-foreground ${expanded ? "" : "line-clamp-3"}`}
          >
            {excerpt}
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={async () => {
                await navigator.clipboard.writeText(excerpt);
                setCopied(true);
                toast.success("Excerpt copied");
                window.setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
              Copy excerpt
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setExpanded((v) => !v)}
            >
              {expanded ? "Collapse" : "Expand"}
            </Button>
          </div>
        </>
      ) : null}
    </article>
  );
});

export function DocumentRowStats({ doc }: { doc: DocumentRecord }) {
  return (
    <div className="grid grid-cols-2 gap-2 text-[12px] text-muted-foreground sm:grid-cols-4">
      <div>
        Retrievals{" "}
        <span className="font-medium tabular text-foreground">
          {formatNumber(doc.retrieval_count)}
        </span>
      </div>
      <div>
        Gaps{" "}
        <span className="font-medium tabular text-foreground">
          {formatNumber(doc.knowledge_gap_count)}
        </span>
      </div>
      <div>
        Feedback{" "}
        <span className="font-medium tabular text-foreground">
          {formatNumber(doc.feedback_count)}
        </span>
      </div>
      <div>
        Avg conf{" "}
        <span className="font-medium tabular text-foreground">
          {doc.average_confidence != null
            ? formatPercent(doc.average_confidence)
            : "—"}
        </span>
      </div>
    </div>
  );
}
