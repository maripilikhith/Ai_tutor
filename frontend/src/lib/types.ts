/**
 * AI Study Companion — Shared TypeScript Types
 *
 * All types matching the backend Pydantic schemas.
 * Single source of truth for frontend data shapes.
 */

// ── Auth ──
export interface User {
  id: string;
  full_name: string;
  avatar_url: string | null;
  role: "user" | "admin";
  onboarding_completed: boolean;
  created_at: string;
}

// ── Spaces ──
export interface Space {
  id: string;
  name: string;
  description: string;
  color: string;
  icon: string;
  project_count: number;
  created_at: string;
  updated_at: string;
}

// ── Projects ──
export interface Project {
  id: string;
  space_id: string;
  name: string;
  description: string;
  learning_goal: string;
  status: "active" | "archived" | "completed";
  material_count: number;
  quiz_count: number;
  avg_mastery: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectDashboard {
  project: Project;
  recent_activity: LearningEvent[];
  mastery_summary: ConceptMastery[];
  recommendations: Recommendation[];
  stats: {
    material_count: number;
    quiz_count: number;
    avg_quiz_score: number;
    conversation_count: number;
    avg_mastery: number;
    concept_count: number;
  };
}

// ── Materials ──
export interface Material {
  id: string;
  project_id: string;
  file_name: string;
  file_size_bytes: number;
  file_type: string;
  status: "queued" | "processing" | "ready" | "failed";
  page_count: number;
  error_message: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
}

// ── Conversations & Messages ──
export interface Conversation {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface Citation {
  file_name: string;
  page_number: number | null;
  chunk_id: string | null;
}

// ── Quiz ──
export interface QuizQuestion {
  question_id: string;
  question_type: "mcq" | "open_ended";
  difficulty: "easy" | "medium" | "hard";
  question_text: string;
  concept_name: string;
  options: { label: string; text: string }[];
  question_order: number;
  total_questions: number;
  source_reference?: string;
}

export interface QuizAnswer {
  is_correct: boolean;
  score: number;
  correct_answer: string | null;
  explanation: string;
  evaluation: AIEvaluation | null;
  source_reference?: string;
  next_question: QuizQuestion | null;
}

export interface AIEvaluation {
  score: number;
  understanding: string;
  accuracy: string;
  relevance: string;
  key_concepts_covered: string[];
  missing_concepts: string[];
  strengths: string[];
  weaknesses: string[];
  feedback: string;
}

export interface QuizSummary {
  quiz_id: string;
  total_questions: number;
  correct_count: number;
  score_percentage: number;
  concepts_tested: { concept_name: string; is_correct: boolean; score: number }[];
  completed_at: string | null;
}

export interface QuizRecord {
  id: string;
  total_questions: number;
  answered_count: number;
  correct_count: number;
  score_percentage: number;
  status: "in_progress" | "completed";
  created_at: string;
  completed_at: string | null;
}

export interface QuizListResponse {
  items: QuizRecord[];
  total: number;
}

// ── Mastery ──
export interface ConceptMastery {
  id: string;
  concept_id: string;
  concept_name: string;
  mastery_score: number;
  trend: "improving" | "stable" | "declining" | "new";
  quiz_attempts: number;
  correct_count: number;
  incorrect_count: number;
  last_tested_at: string | null;
}

export interface GrowthDataPoint {
  date: string;
  concept_name: string;
  mastery_score: number;
}

// ── Recommendations ──
export interface Recommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  related_concepts: string[];
  related_materials: string[];
  status: "active" | "completed" | "dismissed";
  created_at: string;
}

// ── Events ──
export interface LearningEvent {
  id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  created_at: string;
}

// ── Analytics ──
export interface StatCard {
  label: string;
  value: number | string;
  change?: number;
  trend?: string;
}

export interface AnalyticsData {
  stats: StatCard[];
  activity_over_time: { date: string; count: number }[];
  mastery_trends: Record<string, unknown>[];
  quiz_performance: { date: string; score: number }[];
  heatmap_data: { date: string; count: number; level: number }[];
}

// ── Generic ──
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}
