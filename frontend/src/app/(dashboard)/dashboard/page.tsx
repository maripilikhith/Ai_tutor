/**
 * Home Dashboard Page
 *
 * The main landing page after login showing:
 * - Greeting + stats overview
 * - Spaces grid with project counts
 * - Recent activity timeline
 * - Active recommendations
 */

"use client";

import useSWR from "swr";
import Link from "next/link";
import { api, swrFetcher } from "@/lib/api";
import { useAuth } from "@/components/providers/auth-provider";
import { formatDate } from "@/lib/utils";
import {
  BookOpen,
  Brain,
  BarChart3,
  Target,
  Plus,
  ArrowRight,
  Sparkles,
  Clock,
  TrendingUp,
  Loader2,
  Volume2,
} from "lucide-react";
import type { Space, Recommendation, LearningEvent } from "@/lib/types";

interface HomeDashboard {
  profile: { full_name: string } | null;
  spaces: (Space & { project_count: number })[];
  recent_activity: LearningEvent[];
  recommendations: Recommendation[];
  stats: {
    total_spaces: number;
    total_projects: number;
    total_quizzes: number;
    avg_mastery: number;
    concepts_learned: number;
  };
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading: loading } = useSWR<HomeDashboard>("/home", swrFetcher);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
      </div>
    );
  }

  const stats = data?.stats;
  const greeting = getGreeting();
  const name =
    data?.profile?.full_name ||
    user?.user_metadata?.full_name ||
    "Student";

  const playWelcomeAudio = () => {
    if (!("speechSynthesis" in window)) {
      alert("Your browser does not support text-to-speech.");
      return;
    }
    const utterance = new SpeechSynthesisUtterance(
      `Welcome back to A I Study Companion, ${name.split(" ")[0]}! You have ${stats?.total_projects || 0} active projects, and your average mastery is ${stats?.avg_mastery || 0} percent. Keep up the great work!`
    );
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)] flex items-center gap-3">
            {greeting}, {name.split(" ")[0]} 👋
            <button 
              onClick={playWelcomeAudio}
              className="p-2 rounded-full hover:bg-[var(--bg-elevated)] text-[var(--text-muted)] hover:text-[var(--primary-light)] transition-colors"
              title="Play Voice Tour"
            >
              <Volume2 className="w-5 h-5" />
            </button>
          </h1>
          <p className="text-[var(--text-muted)] mt-1">
            Here&apos;s your learning overview
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-children">
        <StatCard
          icon={BookOpen}
          label="Projects"
          value={stats?.total_projects ?? 0}
          color="var(--primary)"
        />
        <StatCard
          icon={Brain}
          label="Quizzes Taken"
          value={stats?.total_quizzes ?? 0}
          color="var(--accent-cyan)"
        />
        <StatCard
          icon={TrendingUp}
          label="Avg Mastery"
          value={`${stats?.avg_mastery ?? 0}%`}
          color="var(--accent-green)"
        />
        <StatCard
          icon={Target}
          label="Concepts"
          value={stats?.concepts_learned ?? 0}
          color="var(--accent-amber)"
        />
      </div>

      {/* Two column layout */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Spaces (2/3 width) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              Your Spaces
            </h2>
            <Link
              href="/spaces"
              className="text-sm text-[var(--text-accent)] hover:text-[var(--primary)] flex items-center gap-1 transition-colors"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {data?.spaces && data.spaces.length > 0 ? (
            <div className="grid sm:grid-cols-2 gap-3 stagger-children">
              {data.spaces.slice(0, 4).map((space) => (
                <Link
                  key={space.id}
                  href={`/spaces/${space.id}`}
                  className="gradient-card p-4 block group"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                      style={{ backgroundColor: `${space.color}20` }}
                    >
                      {space.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-[var(--text-primary)] truncate group-hover:text-[var(--primary-light)] transition-colors">
                        {space.name}
                      </h3>
                      <p className="text-xs text-[var(--text-muted)]">
                        {space.project_count} project
                        {space.project_count !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  {space.description && (
                    <p className="text-xs text-[var(--text-muted)] line-clamp-2">
                      {space.description}
                    </p>
                  )}
                </Link>
              ))}

              {/* Create space card */}
              <Link
                href="/spaces?create=true"
                className="border-2 border-dashed border-[var(--border-default)] rounded-2xl p-4 flex items-center justify-center gap-2 text-[var(--text-muted)] hover:text-[var(--primary-light)] hover:border-[var(--primary)] transition-all"
              >
                <Plus className="w-5 h-5" />
                <span className="text-sm font-medium">New Space</span>
              </Link>
            </div>
          ) : (
            <div className="gradient-card p-8 text-center">
              <BookOpen className="w-12 h-12 mx-auto text-[var(--text-muted)] mb-3" />
              <h3 className="font-medium text-[var(--text-primary)] mb-1">
                No spaces yet
              </h3>
              <p className="text-sm text-[var(--text-muted)] mb-4">
                Create your first space to organize your learning
              </p>
              <Link href="/spaces?create=true" className="btn-primary inline-flex items-center gap-2">
                <Plus className="w-4 h-4" /> Create Space
              </Link>
            </div>
          )}
        </div>

        {/* Right sidebar — Activity + Recommendations */}
        <div className="space-y-6">


          {/* Recent Activity */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-[var(--text-muted)]" />
              Recent Activity
            </h3>
            {data?.recent_activity && data.recent_activity.length > 0 ? (
              <div className="space-y-1">
                {data.recent_activity.slice(0, 6).map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-[var(--bg-card)] transition-colors"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-[var(--primary)]" />
                    <p className="text-xs text-[var(--text-secondary)] flex-1">
                      {formatEventType(event.event_type)}
                    </p>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {formatDate(event.created_at)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--text-muted)] py-4 text-center">
                No activity yet
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Helper Components ──

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="stat-card">
      <div className="flex items-center gap-3 mb-2">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${color}15`, color }}
        >
          <Icon className="w-4.5 h-4.5" />
        </div>
      </div>
      <p className="text-2xl font-bold text-[var(--text-primary)]">{value}</p>
      <p className="text-xs text-[var(--text-muted)] mt-0.5">{label}</p>
    </div>
  );
}

// ── Helpers ──

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function formatEventType(type: string): string {
  const map: Record<string, string> = {
    space_created: "Created a new space",
    project_created: "Started a new project",
    material_uploaded: "Uploaded a document",
    material_processed: "Document ready",
    tutor_message_sent: "Chat with AI Tutor",
    quiz_started: "Started a quiz",
    quiz_completed: "Completed a quiz",
    mastery_updated: "Mastery updated",
    recommendation_generated: "New recommendations",
  };
  return map[type] || type.replace(/_/g, " ");
}
