/**
 * Mastery Page — Compact grid with progress bars
 */

"use client";

import useSWR from "swr";
import { useParams } from "next/navigation";
import { api, swrFetcher } from "@/lib/api";
import { getMasteryLevel, getTrendInfo } from "@/lib/utils";
import { Brain, Loader2 } from "lucide-react";
import type { ConceptMastery } from "@/lib/types";

export default function MasteryPage() {
  const { id } = useParams();
  const projectId = id as string;

  const { data, isLoading: loading } = useSWR<{ items: ConceptMastery[]; avg_mastery: number }>(`/projects/${projectId}/mastery`, swrFetcher, { keepPreviousData: true });
  const mastery = data?.items || [];
  const avgMastery = data?.avg_mastery || 0;

  if (loading && !data) return (
    <div className="space-y-4 animate-fade-in">
      <div className="h-20 w-full skeleton" />
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {[...Array(6)].map((_, i) => <div key={i} className="h-32 skeleton" />)}
      </div>
    </div>
  );

  if (mastery.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-in">
        <Brain className="w-16 h-16 mx-auto text-[var(--text-muted)] mb-4" />
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">No mastery data yet</h3>
        <p className="text-sm text-[var(--text-muted)]">Take a quiz to start tracking your progress</p>
      </div>
    );
  }

  const overall = getMasteryLevel(avgMastery);

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Overall summary — compact single row */}
      <div className="gradient-card px-5 py-3 flex items-center gap-4">
        <span className="text-2xl font-bold" style={{ color: overall.color }}>{avgMastery.toFixed(0)}%</span>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-[var(--text-primary)]">Overall Mastery</span>
            <span className="text-xs" style={{ color: overall.color }}>{overall.label}</span>
          </div>
          <div className="w-full bg-[var(--bg-input)] rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full transition-all duration-700"
              style={{ width: `${avgMastery}%`, backgroundColor: overall.color }}
            />
          </div>
        </div>
        <span className="text-xs text-[var(--text-muted)] flex-shrink-0">{mastery.length} topics</span>
      </div>

      {/* Concept grid — 2 columns of compact cards */}
      <div className="grid sm:grid-cols-2 gap-3">
        {mastery.map((concept) => {
          const level = getMasteryLevel(concept.mastery_score);
          const trend = getTrendInfo(concept.trend);
          return (
            <div key={concept.id} className="gradient-card px-4 py-3">
              {/* Name + score on one line */}
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-[var(--text-primary)] truncate pr-2">{concept.concept_name}</p>
                <span className="text-sm font-bold flex-shrink-0" style={{ color: level.color }}>
                  {concept.mastery_score.toFixed(0)}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-[var(--bg-input)] rounded-full h-1.5 mb-2">
                <div
                  className="h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${concept.mastery_score}%`, backgroundColor: level.color }}
                />
              </div>

              {/* Trend + attempts — tiny footer */}
              <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)]">
                <span style={{ color: trend.color }}>{trend.icon} {trend.label}</span>
                <span>{concept.quiz_attempts} attempts · {concept.correct_count}✓ {concept.incorrect_count}✗</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
