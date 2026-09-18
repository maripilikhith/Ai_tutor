/**
 * Quiz Page — Adaptive quiz with MCQ + open-ended questions
 */

"use client";

import useSWR from "swr";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api, swrFetcher } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Brain, Loader2, CheckCircle, XCircle, ArrowRight, Trophy, RotateCcw, BookOpen, History, Trash2 } from "lucide-react";
import type { QuizQuestion, QuizAnswer, QuizSummary, QuizListResponse, QuizRecord } from "@/lib/types";

type QuizState = "idle" | "in_progress" | "evaluating" | "feedback" | "completed";

export default function QuizPage() {
  const { id } = useParams();
  const projectId = id as string;
  const [state, setState] = useState<QuizState>("idle");
  const [quizId, setQuizId] = useState<string | null>(null);
  const [question, setQuestion] = useState<QuizQuestion | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState("");
  const [openAnswer, setOpenAnswer] = useState("");
  const [feedback, setFeedback] = useState<QuizAnswer | null>(null);
  const [summary, setSummary] = useState<QuizSummary | null>(null);
  const [totalQuestions, setTotalQuestions] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: pastQuizzesData, isLoading: loadingPast, mutate: mutatePastQuizzes } = useSWR<QuizListResponse>(
    state === "idle" ? `/projects/${projectId}/quizzes` : null,
    swrFetcher
  );
  const pastQuizzes = pastQuizzesData?.items || [];

  const deleteQuiz = async (quizIdToDelete: string) => {
    if (!confirm("Are you sure you want to delete this quiz?")) return;
    try {
      await api.delete(`/quiz/${quizIdToDelete}`);
      const filteredQuizzes = pastQuizzes.filter((q) => q.id !== quizIdToDelete);
      mutatePastQuizzes({ items: filteredQuizzes, total: filteredQuizzes.length }, false);
    } catch (err) {
      console.error("Failed to delete quiz", err);
    }
  };

  const startQuiz = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.post<{ quiz_id: string; total_questions: number; first_question: QuizQuestion }>(
        `/projects/${projectId}/quiz/start`,
        { total_questions: totalQuestions }
      );
      setQuizId(data.quiz_id);
      setQuestion(data.first_question);
      setState("in_progress");
      resetAnswers();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to start quiz. Please try again.";
      setError(msg);
    } finally { setLoading(false); }
  };

  const submitAnswer = async () => {
    if (!quizId || !question) return;
    const answer = question.question_type === "mcq" ? selectedAnswer : openAnswer;
    if (!answer.trim()) return;

    setState("evaluating");
    try {
      const result = await api.post<QuizAnswer>(`/quiz/${quizId}/answer`, {
        question_id: question.question_id,
        answer,
      });
      setFeedback(result);
      setState("feedback");
    } catch { setState("in_progress"); }
  };

  const nextQuestion = () => {
    if (feedback?.next_question) {
      setQuestion(feedback.next_question);
      setFeedback(null);
      resetAnswers();
      setState("in_progress");
    } else {
      completeQuiz();
    }
  };

  const completeQuiz = async () => {
    if (!quizId) return;
    try {
      const result = await api.post<QuizSummary>(`/quiz/${quizId}/complete`);
      setSummary(result);
      setState("completed");
    } catch {}
  };

  const resetAnswers = () => {
    setSelectedAnswer("");
    setOpenAnswer("");
  };

  const resetQuiz = () => {
    setState("idle");
    setQuizId(null);
    setQuestion(null);
    setFeedback(null);
    setSummary(null);
    resetAnswers();
  };

  // ── Idle State ──
  if (state === "idle") {
    return (
      <div className="max-w-lg mx-auto text-center py-12 animate-fade-in">
        <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-[var(--primary)] to-[var(--accent-cyan)] flex items-center justify-center mb-6 animate-pulse-glow">
          <Brain className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Adaptive Quiz</h2>
        <p className="text-sm text-[var(--text-muted)] mb-8">
          Questions are generated from your materials and adapted to your mastery level.
        </p>

        <div className="gradient-card p-6 mb-6">
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-3">Number of Questions</label>
          <div className="flex gap-2 justify-center">
            {[5, 10, 15, 20].map((n) => (
              <button
                key={n}
                onClick={() => setTotalQuestions(n)}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  totalQuestions === n
                    ? "bg-[var(--primary)] text-white"
                    : "bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                )}
              >{n}</button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-400 text-center">
            {error}
          </div>
        )}

        <button onClick={startQuiz} disabled={loading} className="btn-primary px-8 py-3 text-base flex items-center gap-2 mx-auto">
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Brain className="w-5 h-5" />}
          {loading ? "Generating..." : "Start Quiz"}
        </button>

        {/* Past Quizzes Section */}
        <div className="mt-12 text-left">
          <div className="flex items-center gap-2 mb-4">
            <History className="w-5 h-5 text-[var(--text-secondary)]" />
            <h3 className="text-lg font-semibold text-[var(--text-primary)]">Quiz History</h3>
          </div>
          
          {loadingPast && !pastQuizzesData ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 w-full skeleton" />
              ))}
            </div>
          ) : pastQuizzes.length === 0 ? (
            <div className="gradient-card p-8 text-center text-[var(--text-muted)]">
              No quizzes taken yet. Start your first quiz above!
            </div>
          ) : (
            <div className="space-y-3">
              {pastQuizzes.map(quiz => (
                <div key={quiz.id} className="gradient-card p-4 flex items-center justify-between hover:border-[var(--primary)] transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn(
                        "text-sm font-semibold",
                        quiz.score_percentage >= 80 ? "text-[var(--accent-green)]" :
                        quiz.score_percentage >= 60 ? "text-yellow-500" : "text-[var(--accent-red)]"
                      )}>
                        {quiz.score_percentage}% Score
                      </span>
                      <span className="badge badge-purple text-[10px]">
                        {quiz.status === "completed" ? "Completed" : "In Progress"}
                      </span>
                    </div>
                    <div className="text-xs text-[var(--text-muted)]">
                      {quiz.answered_count} / {quiz.total_questions} questions answered • {new Date(quiz.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <button
                    onClick={() => deleteQuiz(quiz.id)}
                    className="p-2 text-[var(--text-muted)] hover:text-[var(--accent-red)] hover:bg-[var(--accent-red)]/10 rounded-lg transition-colors"
                    title="Delete Quiz"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Completed State ──
  if (state === "completed" && summary) {
    const scoreColor = summary.score_percentage >= 80 ? "var(--accent-green)" : summary.score_percentage >= 50 ? "var(--accent-amber)" : "var(--accent-red)";
    return (
      <div className="max-w-lg mx-auto text-center py-8 animate-fade-in">
        <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-[var(--accent-green)] to-[var(--accent-cyan)] flex items-center justify-center mb-6">
          <Trophy className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-1">Quiz Complete!</h2>
        <p className="text-6xl font-bold my-6" style={{ color: scoreColor }}>{summary.score_percentage.toFixed(0)}%</p>
        <p className="text-sm text-[var(--text-muted)] mb-6">
          {summary.correct_count} out of {summary.total_questions} correct
        </p>

        {summary.concepts_tested.length > 0 && (
          <div className="gradient-card p-4 mb-6 text-left">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Concepts Tested</h3>
            <div className="space-y-2">
              {summary.concepts_tested.map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  {c.is_correct ? <CheckCircle className="w-4 h-4 text-[var(--accent-green)]" /> : <XCircle className="w-4 h-4 text-[var(--accent-red)]" />}
                  <span className="text-sm text-[var(--text-secondary)]">{c.concept_name}</span>
                  <span className="ml-auto text-xs text-[var(--text-muted)]">{c.score.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <button onClick={resetQuiz} className="btn-primary flex items-center gap-2 mx-auto">
          <RotateCcw className="w-4 h-4" /> Take Another Quiz
        </button>
      </div>
    );
  }

  // ── In Progress / Evaluating / Feedback ──
  if (!question) return null;

  return (
    <div className="max-w-2xl mx-auto py-4 animate-fade-in">
      {/* Progress */}
      <div className="flex items-center gap-3 mb-6">
        <span className="text-sm text-[var(--text-muted)]">
          Question {question.question_order} of {question.total_questions}
        </span>
        <div className="flex-1 bg-[var(--bg-input)] rounded-full h-2">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-[var(--primary)] to-[var(--accent-cyan)] transition-all"
            style={{ width: `${(question.question_order / question.total_questions) * 100}%` }}
          />
        </div>
        <span className="badge badge-purple text-[10px]">{question.difficulty}</span>
      </div>

      {/* Question */}
      <div className="gradient-card p-6 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="badge badge-info text-[10px]">{question.question_type === "mcq" ? "Multiple Choice" : "Open Ended"}</span>
          {question.concept_name && <span className="text-xs text-[var(--text-muted)]">{question.concept_name}</span>}
        </div>
        <p className="text-lg font-medium text-[var(--text-primary)] leading-relaxed">{question.question_text}</p>
      </div>

      {/* Answer Area */}
      {question.question_type === "mcq" ? (
        <div className="space-y-2 mb-6">
          {question.options.map((opt) => {
            const isSelected = selectedAnswer === opt.label;
            const showCorrect = state === "feedback" && feedback?.correct_answer === opt.label;
            const showWrong = state === "feedback" && isSelected && !feedback?.is_correct;
            return (
              <button
                key={opt.label}
                onClick={() => state === "in_progress" && setSelectedAnswer(opt.label)}
                disabled={state !== "in_progress"}
                className={cn(
                  "w-full text-left p-4 rounded-xl border transition-all flex items-center gap-3",
                  isSelected && state === "in_progress" && "border-[var(--primary)] bg-[var(--primary)]/5",
                  showCorrect && "border-[var(--accent-green)] bg-[var(--accent-green)]/5",
                  showWrong && "border-[var(--accent-red)] bg-[var(--accent-red)]/5",
                  !isSelected && !showCorrect && !showWrong && "border-[var(--border-default)] hover:border-[var(--border-hover)]"
                )}
              >
                <span className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold flex-shrink-0",
                  isSelected ? "bg-[var(--primary)] text-white" : "bg-[var(--bg-input)] text-[var(--text-muted)]"
                )}>{opt.label}</span>
                <span className="text-sm text-[var(--text-primary)]">{opt.text}</span>
                {showCorrect && <CheckCircle className="w-5 h-5 text-[var(--accent-green)] ml-auto" />}
                {showWrong && <XCircle className="w-5 h-5 text-[var(--accent-red)] ml-auto" />}
              </button>
            );
          })}
        </div>
      ) : (
        <div className="mb-6">
          <textarea
            value={openAnswer}
            onChange={(e) => setOpenAnswer(e.target.value)}
            disabled={state !== "in_progress"}
            className="input-field h-32 resize-none"
            placeholder="Type your answer here..."
          />
        </div>
      )}

      {/* Feedback */}
      {state === "feedback" && feedback && (
        <div className={cn("gradient-card p-5 mb-6 border-l-4", feedback.is_correct ? "border-l-[var(--accent-green)]" : "border-l-[var(--accent-red)]")}>
          <div className="flex items-center gap-2 mb-2">
            {feedback.is_correct ? <CheckCircle className="w-5 h-5 text-[var(--accent-green)]" /> : <XCircle className="w-5 h-5 text-[var(--accent-red)]" />}
            <span className="font-semibold text-[var(--text-primary)]">{feedback.is_correct ? "Correct!" : "Incorrect"}</span>
            <span className="ml-auto text-sm font-medium" style={{ color: feedback.is_correct ? "var(--accent-green)" : "var(--accent-red)" }}>
              {feedback.score.toFixed(0)}%
            </span>
          </div>
          {feedback.explanation && <p className="text-sm text-[var(--text-secondary)] mt-2">{feedback.explanation}</p>}
          {feedback.evaluation && (
            <div className="mt-3 pt-3 border-t border-[var(--border-default)] text-sm text-[var(--text-muted)]">
              <p><strong>Feedback:</strong> {feedback.evaluation.feedback}</p>
            </div>
          )}
          {feedback.source_reference && (
            <div className="mt-3 pt-3 border-t border-[var(--border-default)] flex items-start gap-2 text-sm text-[var(--text-muted)]">
              <BookOpen className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <p><strong>Source:</strong> {feedback.source_reference}</p>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3">
        {state === "in_progress" && (
          <button
            onClick={submitAnswer}
            disabled={!(selectedAnswer || openAnswer.trim())}
            className="btn-primary flex items-center gap-2"
          >
            Submit Answer
          </button>
        )}
        {state === "evaluating" && (
          <button disabled className="btn-primary flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Evaluating...
          </button>
        )}
        {state === "feedback" && (
          <button onClick={nextQuestion} className="btn-primary flex items-center gap-2">
            {feedback?.next_question ? <><span>Next Question</span> <ArrowRight className="w-4 h-4" /></> : "View Results"}
          </button>
        )}
      </div>
    </div>
  );
}
