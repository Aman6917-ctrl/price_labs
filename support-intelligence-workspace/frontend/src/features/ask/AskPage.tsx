import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Brain,
  Copy,
  Database,
  Flag,
  Layers,
  Search,
  ThumbsDown,
  ThumbsUp,
  Timer,
} from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { askQuestion, flagGap, submitFeedback } from "@/api";
import { HealthBadge, QualityBadge } from "@/components/badges";
import { CitationCard, DocumentCard } from "@/components/cards/DocumentCard";
import { PageContainer } from "@/components/cards/StatCard";
import { ActionAlert } from "@/components/ui/ActionAlert";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Markdown } from "@/components/ui/Markdown";
import { MetricTile } from "@/components/ui/MetricTile";
import { ScoreMeter } from "@/components/ui/ScoreMeter";
import { ErrorState } from "@/components/ui/states";
import { AnalyzeStepper } from "@/features/ask/AnalyzeStepper";
import type { AskResponse, KnowledgeGapReason } from "@/types/api";

const GAP_REASONS: { value: KnowledgeGapReason; label: string }[] = [
  { value: "missing_documentation", label: "Missing Documentation" },
  { value: "outdated_documentation", label: "Outdated Documentation" },
  { value: "incorrect_documentation", label: "Incorrect Documentation" },
  { value: "confusing_documentation", label: "Confusing Documentation" },
];

const EXAMPLES = [
  "Why are prices not updating?",
  "Booking.com sync issue",
  "How does dynamic pricing work?",
  "How do I set a minimum stay?",
  "Does PriceLabs support Airbnb integration?",
];

const ASK_METRICS_KEY = "siw-last-ask-metrics";

export function AskPage() {
  const [question, setQuestion] = useState("");
  const [sessionId] = useState(() => `session_${crypto.randomUUID().slice(0, 8)}`);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [gapOpen, setGapOpen] = useState(false);
  const [gapReason, setGapReason] =
    useState<KnowledgeGapReason>("missing_documentation");
  const [gapNotes, setGapNotes] = useState("");

  const ask = useMutation({
    mutationFn: () =>
      askQuestion({ question: question.trim(), session_id: sessionId }),
    onSuccess: (data) => {
      setResult(data);
      const unsupported = Boolean(data.metadata?.unsupported_topic);
      if (unsupported) {
        setGapOpen(true);
        setGapReason("missing_documentation");
      }
      try {
        const token = (data.metadata?.token_usage ?? {}) as Record<string, unknown>;
        localStorage.setItem(
          ASK_METRICS_KEY,
          JSON.stringify({
            total_tokens: token.total_tokens ?? null,
            estimated_cost_usd: token.estimated_cost_usd ?? null,
            total_ms: data.processing.total_ms,
            confidence: data.confidence.score,
            at: Date.now(),
          }),
        );
      } catch {
        /* ignore */
      }
      toast.success(
        unsupported
          ? "Knowledge gap detected — review and flag if needed"
          : "Analysis complete",
      );
    },
    onError: (err: Error) => toast.error(err.message || "Ask failed"),
  });

  const feedback = useMutation({
    mutationFn: (type: "thumbs_up" | "thumbs_down") => {
      if (!result?.question_id)
        throw new Error("Persist a question first (Mongo required)");
      return submitFeedback({
        question_id: result.question_id,
        feedback_type: type,
      });
    },
    onSuccess: () => toast.success("Feedback saved"),
    onError: (err: Error) => toast.error(err.message),
  });

  const gap = useMutation({
    mutationFn: () =>
      flagGap({
        reason: gapReason,
        category: result?.retrieved_documents[0]?.category ?? "uncategorized",
        description: gapNotes || undefined,
        question_id: result?.question_id ?? undefined,
        retrieved_document_ids:
          result?.retrieved_documents.map((d) => d.document_id) ?? [],
        topic: question.slice(0, 80) || undefined,
      }),
    onSuccess: () => {
      toast.success("Knowledge gap flagged");
      setGapOpen(false);
      setGapNotes("");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const healthByDoc = useMemo(() => {
    const map = new Map<string, string>();
    result?.document_health.forEach((h) => map.set(h.document_id, h.health));
    return map;
  }, [result]);

  const unsupported = Boolean(result?.metadata?.unsupported_topic);
  const looselyRelated = useMemo(() => {
    const raw = result?.metadata?.loosely_related_documents;
    return Array.isArray(raw)
      ? (raw as Array<{
          document_id: string;
          title: string;
          category: string;
          similarity: number;
        }>)
      : [];
  }, [result]);

  return (
    <PageContainer
      title="Ask Workspace"
      description="Paste a customer question. Review grounded evidence, confidence, and the recommended next action before you reply."
    >
      <section className="panel p-4 md:p-5">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <label
            htmlFor="customer-question"
            className="text-[13px] font-medium text-foreground"
          >
            Customer question
          </label>
          <span className="font-mono text-[11px] text-muted-foreground">
            {sessionId}
          </span>
        </div>
        <Textarea
          id="customer-question"
          className="mt-2 min-h-[132px] resize-y"
          placeholder="Paste the customer question here…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={ask.isPending}
        />

        {!result && !ask.isPending && !question.trim() ? (
          <div className="mt-3 border border-dashed border-border bg-muted/30 px-3 py-3">
            <p className="text-[12px] font-medium text-foreground">
              Example questions
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setQuestion(ex)}
                  className="rounded-md border border-border bg-card px-2.5 py-1 text-[12px] text-foreground transition-colors hover:border-foreground/20 hover:bg-accent"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button
            type="button"
            disabled={question.trim().length < 3 || ask.isPending}
            onClick={() => ask.mutate()}
            aria-busy={ask.isPending}
          >
            {ask.isPending ? (
              <>
                <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                Analyzing…
              </>
            ) : (
              <>
                <Search className="h-3.5 w-3.5" /> Analyze
              </>
            )}
          </Button>
          <p className="text-[12px] text-muted-foreground">
            Grounded on internal docs · Claude + MiniLM
          </p>
        </div>

        <AnalyzeStepper active={ask.isPending} />

        {ask.isError ? (
          <div className="mt-3">
            <ErrorState
              title="Analysis failed"
              description={
                ask.error instanceof Error ? ask.error.message : "Request failed"
              }
              onRetry={() => ask.mutate()}
            />
          </div>
        ) : null}
      </section>

      {result ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.18 }}
          className="grid gap-4 xl:grid-cols-[1.4fr_1fr]"
        >
          <div className="space-y-4">
            <section className="panel p-4 md:p-5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-[13px] font-semibold">Suggested response</h2>
                <QualityBadge label={result.quality.label} />
              </div>

              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <ScoreMeter
                  label="Confidence"
                  score={result.confidence.score}
                  level={result.confidence.level}
                />
                <ScoreMeter
                  label="Coverage"
                  score={result.coverage.score}
                  hint={result.coverage.label}
                />
              </div>

              <div className="mt-3">
                <ActionAlert
                  action={result.recommended_action}
                  reason={result.recommended_action_reason}
                />
              </div>

              <div className="mt-3 border border-border bg-background p-4">
                <Markdown content={result.answer} />
              </div>

              <div className="mt-3 flex flex-wrap gap-1.5">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    await navigator.clipboard.writeText(result.answer);
                    toast.success("Copied to clipboard");
                  }}
                >
                  <Copy className="h-3.5 w-3.5" /> Copy
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setGapOpen((v) => !v)}
                >
                  <Flag className="h-3.5 w-3.5" /> Flag gap
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!result.question_id || feedback.isPending}
                  onClick={() => feedback.mutate("thumbs_up")}
                >
                  <ThumbsUp className="h-3.5 w-3.5" /> Helpful
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!result.question_id || feedback.isPending}
                  onClick={() => feedback.mutate("thumbs_down")}
                >
                  <ThumbsDown className="h-3.5 w-3.5" /> Not helpful
                </Button>
              </div>

              {gapOpen ? (
                <div className="mt-3 space-y-2 border border-border bg-muted/40 p-3">
                  <p className="text-[13px] font-medium">Flag knowledge gap</p>
                  <Select
                    value={gapReason}
                    onChange={(e) =>
                      setGapReason(e.target.value as KnowledgeGapReason)
                    }
                  >
                    {GAP_REASONS.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </Select>
                  <Input
                    placeholder="Additional notes"
                    value={gapNotes}
                    onChange={(e) => setGapNotes(e.target.value)}
                  />
                  <Button
                    type="button"
                    size="sm"
                    disabled={gap.isPending}
                    onClick={() => gap.mutate()}
                  >
                    Save gap report
                  </Button>
                </div>
              ) : null}
            </section>

            <section className="panel p-4 md:p-5">
              <h2 className="text-[13px] font-semibold">Why this answer</h2>
              <p className="mt-2 text-[13px] leading-5 text-muted-foreground">
                {result.why_this_answer}
              </p>
              {result.quality.reasons?.length ? (
                <ul className="mt-3 list-disc space-y-1 pl-5 text-[12px] text-muted-foreground">
                  {result.quality.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              ) : null}
            </section>

            <section className="panel p-4 md:p-5">
              <h2 className="text-[13px] font-semibold">Processing metrics</h2>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
                <MetricTile
                  label="Embedding"
                  valueMs={result.processing.embedding_ms}
                  icon={Layers}
                />
                <MetricTile
                  label="Retrieval"
                  valueMs={result.processing.retrieval_ms}
                  icon={Database}
                />
                <MetricTile
                  label="Rerank"
                  valueMs={result.processing.rerank_ms}
                  icon={Search}
                />
                <MetricTile
                  label="LLM"
                  valueMs={result.processing.llm_ms}
                  icon={Brain}
                />
                <MetricTile
                  label="Total"
                  valueMs={result.processing.total_ms}
                  icon={Timer}
                />
              </div>
              <p className="mt-3 font-mono text-[11px] text-muted-foreground">
                request_id · {result.request_id}
              </p>
            </section>
          </div>

          <div className="space-y-4">
            <section className="panel p-4 md:p-5">
              <h2 className="text-[13px] font-semibold">Supporting documents</h2>
              {unsupported ? (
                <div className="mt-3 border border-warning/25 bg-warning/[0.05] p-3">
                  <p className="text-[13px] font-medium text-foreground">
                    No documentation supports this topic
                  </p>
                  <p className="mt-1 text-[12px] leading-5 text-muted-foreground">
                    Nearest vector matches are only loosely related and were not
                    used as evidence.
                  </p>
                  {looselyRelated.length ? (
                    <ul className="mt-3 space-y-1.5">
                      {looselyRelated.map((d) => (
                        <li
                          key={d.document_id}
                          className="flex items-center justify-between gap-2 border border-border bg-card px-2.5 py-2 text-[12px]"
                        >
                          <span className="min-w-0 truncate font-medium">
                            {d.title}
                            <span className="ml-1 font-normal text-muted-foreground">
                              · {d.category}
                            </span>
                          </span>
                          <span className="shrink-0 tabular text-muted-foreground">
                            {Math.round(d.similarity * 100)}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ) : (
                <div className="mt-3 space-y-2.5">
                  {result.retrieved_documents.length ? (
                    result.retrieved_documents.map((doc) => (
                      <DocumentCard
                        key={doc.document_id}
                        doc={doc}
                        health={healthByDoc.get(doc.document_id)}
                      />
                    ))
                  ) : (
                    <p className="text-[13px] text-muted-foreground">
                      No documents retrieved.
                    </p>
                  )}
                </div>
              )}
            </section>

            <section className="panel p-4 md:p-5">
              <h2 className="text-[13px] font-semibold">Citations</h2>
              <div className="mt-3 space-y-2.5">
                {unsupported || !result.citations.length ? (
                  <p className="text-[13px] text-muted-foreground">
                    {unsupported
                      ? "No citations — the knowledge base does not cover this topic."
                      : "No citations available for this answer."}
                  </p>
                ) : (
                  result.citations.map((c) => (
                    <CitationCard
                      key={`${c.document_id}-${c.title}`}
                      title={c.title}
                      category={c.category}
                      similarity={c.similarity}
                      excerpt={c.excerpt}
                    />
                  ))
                )}
              </div>
            </section>

            <section className="panel p-4 md:p-5">
              <h2 className="text-[13px] font-semibold">Document health</h2>
              <ul className="mt-3 space-y-1.5">
                {result.document_health.length ? (
                  result.document_health.map((h) => (
                    <li
                      key={h.document_id}
                      className="flex items-start justify-between gap-2 border border-border px-3 py-2"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-medium">
                          {h.title}
                        </p>
                        <p className="mt-0.5 text-[12px] text-muted-foreground">
                          {h.reason}
                        </p>
                      </div>
                      <HealthBadge health={h.health} />
                    </li>
                  ))
                ) : (
                  <p className="text-[13px] text-muted-foreground">
                    {unsupported
                      ? "Health checks apply only when supporting documents are used."
                      : "No health rows for this answer."}
                  </p>
                )}
              </ul>
            </section>
          </div>
        </motion.div>
      ) : null}
    </PageContainer>
  );
}
