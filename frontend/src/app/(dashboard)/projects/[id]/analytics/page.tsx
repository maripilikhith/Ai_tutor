/**
 * Project Analytics Page
 */

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Loader2, BarChart3 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, AreaChart, Area } from "recharts";
import type { AnalyticsData } from "@/lib/types";

export default function ProjectAnalyticsPage() {
  const { id } = useParams();
  const projectId = id as string;
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AnalyticsData>(`/projects/${projectId}/analytics`)
      .then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="flex items-center justify-center h-40"><Loader2 className="w-6 h-6 text-[var(--primary)] animate-spin" /></div>;
  if (!data) return <div className="text-center py-16 text-[var(--text-muted)]">No analytics data</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {data.stats.map((stat, i) => (
          <div key={i} className="stat-card text-center py-4">
            <p className="text-lg font-bold text-[var(--text-primary)]">{stat.value}</p>
            <p className="text-[10px] text-[var(--text-muted)]">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Activity Over Time */}
        {data.activity_over_time.length > 0 && (
          <div className="gradient-card p-6">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Activity Over Time</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={data.activity_over_time}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" tick={{ fill: "#6B7280", fontSize: 10 }} />
                <YAxis tick={{ fill: "#6B7280", fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: "#1E1E2A", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#F0F0F5" }} />
                <Area type="monotone" dataKey="count" stroke="#6C5CE7" fill="rgba(108,92,231,0.2)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Quiz Performance */}
        {data.quiz_performance.length > 0 && (
          <div className="gradient-card p-6">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Quiz Performance</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data.quiz_performance}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" tick={{ fill: "#6B7280", fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#6B7280", fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: "#1E1E2A", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#F0F0F5" }} />
                <Bar dataKey="score" fill="#6C5CE7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Heatmap (simplified) */}
      {data.heatmap_data.length > 0 && (
        <div className="gradient-card p-6">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Activity Heatmap</h3>
          <div className="flex gap-1 flex-wrap">
            {data.heatmap_data.map((d, i) => (
              <div
                key={i}
                className="w-3 h-3 rounded-sm transition-colors"
                style={{ backgroundColor: d.level === 0 ? "var(--bg-input)" : `rgba(108, 92, 231, ${0.25 + d.level * 0.2})` }}
                title={`${d.date}: ${d.count} activities`}
              />
            ))}
          </div>
          <div className="flex items-center gap-2 mt-3 text-[10px] text-[var(--text-muted)]">
            <span>Less</span>
            {[0, 1, 2, 3, 4].map((l) => (
              <div key={l} className="w-3 h-3 rounded-sm" style={{ backgroundColor: l === 0 ? "var(--bg-input)" : `rgba(108, 92, 231, ${0.25 + l * 0.2})` }} />
            ))}
            <span>More</span>
          </div>
        </div>
      )}
    </div>
  );
}
