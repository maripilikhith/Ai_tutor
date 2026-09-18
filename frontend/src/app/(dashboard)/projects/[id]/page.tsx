/**
 * Project Overview Page
 *
 * Quick stats + recent activity + recommendations for this project.
 */

"use client";

import useSWR from "swr";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, swrFetcher } from "@/lib/api";
import { formatDate, getMasteryLevel } from "@/lib/utils";
import { Loader2, BookOpen, Brain, HelpCircle, MessageSquare, TrendingUp, Sparkles } from "lucide-react";
import type { ConceptMastery, Recommendation } from "@/lib/types";

interface ProjectOverview {
  stats: { label: string; value: string | number }[];
}

export default function ProjectOverviewPage() {
  const { id } = useParams();
  const projectId = id as string;
  
  const { data: overview, isLoading: overviewLoading } = useSWR<ProjectOverview>(`/projects/${projectId}/analytics`, swrFetcher);
  const { data: masteryData, isLoading: masteryLoading } = useSWR<{ items: ConceptMastery[] }>(`/projects/${projectId}/mastery`, swrFetcher);
  const { data: recsData, isLoading: recsLoading } = useSWR<{ items: Recommendation[] }>(`/projects/${projectId}/recommendations`, swrFetcher);

  const loading = overviewLoading || masteryLoading || recsLoading;
  const mastery = masteryData?.items || [];
  const recs = recsData?.items || [];

  if (loading) return <div className="flex items-center justify-center h-40"><Loader2 className="w-6 h-6 text-[var(--primary)] animate-spin" /></div>;

  const s = overview?.stats || [];

  const getStat = (label: string, fallback: string | number = 0) => {
    return s.find(x => x.label === label)?.value ?? fallback;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 stagger-children">
        <MiniStat icon={BookOpen} label="Materials" value={getStat("Materials")} />
        <MiniStat icon={HelpCircle} label="Quizzes" value={getStat("Quizzes Taken")} />
        <MiniStat icon={TrendingUp} label="Avg Score" value={getStat("Avg Quiz Score", "0%")} />
        <MiniStat icon={MessageSquare} label="Chats" value={getStat("Conversations")} />
        <MiniStat icon={Brain} label="Mastery" value={getStat("Avg Mastery", "0%")} />
        <MiniStat icon={Sparkles} label="Concepts" value={getStat("Concepts")} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top Concepts */}
        <div className="gradient-card p-5">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Concept Mastery</h3>
          {mastery.length > 0 ? (
            <div className="space-y-3">
              {mastery.slice(0, 6).map((c) => {
                const level = getMasteryLevel(c.mastery_score);
                return (
                  <div key={c.id} className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-[var(--text-primary)] truncate">{c.concept_name}</span>
                        <span className="text-xs font-medium" style={{ color: level.color }}>{c.mastery_score.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-[var(--bg-input)] rounded-full h-1.5">
                        <div className="h-1.5 rounded-full transition-all" style={{ width: `${c.mastery_score}%`, backgroundColor: level.color }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)] text-center py-6">Take a quiz to see mastery data</p>
          )}
        </div>

        {/* Recommendations */}
        <div className="gradient-card p-5">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[var(--accent-amber)]" /> Recommendations
          </h3>
          {recs.length > 0 ? (
            <div className="space-y-3">
              {recs.slice(0, 4).map((rec) => (
                <div key={rec.id} className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-default)]">
                  <p className="text-sm font-medium text-[var(--text-primary)]">{rec.title}</p>
                  <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-2">{rec.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)] text-center py-6">Complete a quiz to get recommendations</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3 flex-wrap">
        <Link href={`/projects/${projectId}/materials`} className="btn-secondary text-sm">📄 Upload Materials</Link>
        <Link href={`/projects/${projectId}/tutor`} className="btn-primary text-sm">💬 Start Tutoring</Link>
        <Link href={`/projects/${projectId}/quiz`} className="btn-secondary text-sm">🧠 Take Quiz</Link>
      </div>
    </div>
  );
}

function MiniStat({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string | number }) {
  return (
    <div className="stat-card text-center py-4">
      <Icon className="w-5 h-5 mx-auto text-[var(--text-muted)] mb-2" />
      <p className="text-lg font-bold text-[var(--text-primary)]">{value}</p>
      <p className="text-[10px] text-[var(--text-muted)]">{label}</p>
    </div>
  );
}
