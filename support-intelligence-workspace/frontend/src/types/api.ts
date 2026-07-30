/** Shared API types matching backend schemas. */

export type ConfidenceLevel = "high" | "medium" | "low";
export type AnswerQuality = "excellent" | "good" | "needs_review" | "poor";
export type DocumentHealth = "healthy" | "needs_review" | "outdated";
export type RecommendedAction =
  | "send_response"
  | "verify_documentation"
  | "flag_knowledge_gap"
  | "escalate_to_human";

export type KnowledgeGapReason =
  | "missing_documentation"
  | "outdated_documentation"
  | "incorrect_documentation"
  | "confusing_documentation";

export type FeedbackType =
  | "thumbs_up"
  | "thumbs_down"
  | "positive"
  | "negative"
  | "edited"
  | "regenerated"
  | "copied";

export interface NamedCount {
  key: string;
  count: number;
  label?: string | null;
}

export interface AnalyticsDashboard {
  questions_today: number;
  questions_this_week: number;
  knowledge_gaps_total: number;
  feedback_count: number;
  positive_feedback_pct: number | null;
  negative_feedback_pct: number | null;
  average_confidence: number | null;
  average_coverage: number | null;
  average_quality: number | null;
  average_processing_time_ms: number | null;
  most_retrieved_documents: NamedCount[];
  top_missing_topics: NamedCount[];
  knowledge_gaps_by_category: NamedCount[];
  confidence_distribution: Record<string, number>;
  coverage_distribution: Record<string, number>;
  document_health_distribution: Record<string, number>;
  recommended_action_distribution: Record<string, number>;
  recent_knowledge_gaps: number;
  total_tokens?: number | null;
  estimated_cost_usd?: number | null;
  questions_total?: number;
}

export interface AskCitation {
  title: string;
  category: string;
  version: string;
  last_updated: string;
  similarity: number;
  document_id: string;
  excerpt?: string | null;
}

export interface RetrievedDocument {
  document_id: string;
  title: string;
  category: string;
  version: string;
  last_updated: string;
  similarity: number;
  excerpt?: string | null;
}

export interface DocumentHealthItem {
  document_id: string;
  title: string;
  category: string;
  health: DocumentHealth;
  reason: string;
  last_updated: string;
  version: string;
}

export interface AskResponse {
  request_id: string;
  answer: string;
  confidence: { level: ConfidenceLevel; score: number };
  coverage: { score: number; label: string };
  quality: { label: AnswerQuality; reasons: string[] };
  citations: AskCitation[];
  why_this_answer: string;
  recommended_action: RecommendedAction;
  recommended_action_reason?: string | null;
  retrieved_documents: RetrievedDocument[];
  document_health: DocumentHealthItem[];
  question_id?: string | null;
  processing: {
    embedding_ms: number;
    retrieval_ms: number;
    rerank_ms: number;
    llm_ms: number;
    total_ms: number;
  };
  metadata: Record<string, unknown>;
}

export interface KnowledgeGap {
  id: string;
  created_at: string;
  updated_at: string;
  reason: KnowledgeGapReason;
  category: string;
  description?: string | null;
  question_id?: string | null;
  document_id?: string | null;
  retrieved_document_ids: string[];
  session_id?: string | null;
  topic?: string | null;
}

export interface DocumentRecord {
  id: string;
  created_at: string;
  updated_at: string;
  document_id: string;
  title: string;
  category: string;
  source: string;
  version: string;
  tags: string[];
  last_updated?: string | null;
  health: DocumentHealth;
  retrieval_count: number;
  knowledge_gap_count: number;
  feedback_count: number;
  chunk_count: number;
  average_confidence?: number | null;
  average_coverage?: number | null;
  average_quality?: number | null;
  last_retrieved?: string | null;
}

export interface DocumentStats {
  document_id: string;
  title: string;
  health: DocumentHealth;
  retrieval_count: number;
  knowledge_gap_count: number;
  feedback_count: number;
  average_confidence?: number | null;
  average_coverage?: number | null;
  average_quality?: number | null;
  last_retrieved?: string | null;
}

export interface FeedbackResponse {
  id: string;
  created_at: string;
  updated_at: string;
  question_id: string;
  feedback_type: FeedbackType;
  comment?: string | null;
}
