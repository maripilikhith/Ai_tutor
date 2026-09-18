/**
 * Project Layout
 *
 * Provides sub-navigation for project features:
 * Overview, Materials, Tutor, Quiz, Mastery, Growth, Analytics
 */

"use client";

import { useEffect, useState } from "react";
import useSWR, { preload } from "swr";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { api, swrFetcher } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ArrowLeft, Loader2, BookOpen, MessageSquare, HelpCircle, BarChart3, TrendingUp, Brain } from "lucide-react";
import type { Project } from "@/lib/types";

const tabs = [
  { href: "", label: "Overview", icon: BookOpen, apiPath: "" },
  { href: "/materials", label: "Materials", icon: BookOpen, apiPath: "/materials" },
  { href: "/tutor", label: "AI Tutor", icon: MessageSquare, apiPath: "" },
  { href: "/quiz", label: "Quiz", icon: HelpCircle, apiPath: "/quizzes" },
  { href: "/mastery", label: "Mastery", icon: Brain, apiPath: "/mastery" },
  { href: "/growth", label: "Growth", icon: TrendingUp, apiPath: "/growth" },
  { href: "/analytics", label: "Analytics", icon: BarChart3, apiPath: "/analytics" },
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();
  const projectId = params.id as string;
  const { data: project, isLoading: loading } = useSWR<Project>(`/projects/${projectId}`, swrFetcher, { keepPreviousData: true });

  if (loading && !project) return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg skeleton" />
        <div className="space-y-2">
          <div className="h-6 w-48 skeleton" />
          <div className="h-4 w-64 skeleton" />
        </div>
      </div>
      <div className="h-10 w-full skeleton" />
      <div className="h-64 w-full skeleton" />
    </div>
  );

  if (!project) return <div className="text-center py-20 text-[var(--text-muted)]">Project not found</div>;

  const basePath = `/projects/${projectId}`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href={`/spaces/${project.space_id}`} className="p-2 rounded-lg hover:bg-[var(--bg-card)] text-[var(--text-muted)]">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">{project.name}</h1>
          {project.learning_goal && <p className="text-sm text-[var(--text-muted)]">{project.learning_goal}</p>}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 overflow-x-auto pb-1 border-b border-[var(--border-default)]">
        {tabs.map((tab) => {
          const href = `${basePath}${tab.href}`;
          const isActive = tab.href === "" ? pathname === basePath : pathname.startsWith(href);
          return (
            <Link
              key={tab.href}
              href={href}
              onMouseEnter={() => {
                if (tab.apiPath) {
                  preload(`/projects/${projectId}${tab.apiPath}`, swrFetcher);
                }
              }}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap",
                isActive
                  ? "text-[var(--primary-light)] border-b-2 border-[var(--primary)] bg-[var(--primary)]/5"
                  : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </Link>
          );
        })}
      </div>

      {/* Content */}
      <div>{children}</div>
    </div>
  );
}
