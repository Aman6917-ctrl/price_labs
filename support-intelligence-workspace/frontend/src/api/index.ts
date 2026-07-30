import { api } from "./client";
import type {
  AnalyticsDashboard,
  AskResponse,
  DocumentRecord,
  DocumentStats,
  FeedbackResponse,
  FeedbackType,
  KnowledgeGap,
  KnowledgeGapReason,
} from "@/types/api";

export const fetchAnalytics = () =>
  api.get<AnalyticsDashboard>("/api/analytics");

export const askQuestion = (payload: {
  question: string;
  session_id?: string;
  top_k?: number;
}) => api.post<AskResponse>("/api/ask/", payload);

export const fetchGaps = (limit = 50) =>
  api.get<KnowledgeGap[]>(`/api/gaps?limit=${limit}`);

export const flagGap = (payload: {
  reason: KnowledgeGapReason;
  category: string;
  description?: string;
  question_id?: string;
  document_id?: string;
  retrieved_document_ids?: string[];
  topic?: string;
}) => api.post<KnowledgeGap>("/api/flag-gap", payload);

export const submitFeedback = (payload: {
  question_id: string;
  feedback_type: FeedbackType;
  comment?: string;
}) => api.post<FeedbackResponse>("/api/feedback", payload);

export const fetchDocuments = (limit = 100) =>
  api.get<DocumentRecord[]>(`/api/documents/?limit=${limit}`);

export const fetchDocument = (documentId: string) =>
  api.get<DocumentRecord>(`/api/documents/${encodeURIComponent(documentId)}`);

export const fetchDocumentStats = (documentId: string) =>
  api.get<DocumentStats>(
    `/api/documents/${encodeURIComponent(documentId)}/stats`,
  );
