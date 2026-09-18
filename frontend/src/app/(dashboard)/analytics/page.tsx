/**
 * Global Analytics Page
 */

"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, BarChart3 } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { AnalyticsData } from "@/lib/types";

export default function GlobalAnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AnalyticsData>("/analytics").then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" /></div>;
  if (!data) return <div className="text-center py-20 text-[var(--text-muted)]">No data available</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Analytics</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">Your learning analytics across all projects</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 stagger-children">
        {data.stats.map((stat, i) => (
          <div key={i} className="stat-card text-center py-4">
            <p className="text-xl font-bold text-[var(--text-primary)]">{stat.value}</p>
            <p className="text-xs text-[var(--text-muted)]">{stat.label}</p>
          </div>
        ))}
      </div>

      {data.activity_over_time.length > 0 && (
        <div className="gradient-card p-6">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Activity Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data.activity_over_time}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="date" tick={{ fill: "#6B7280", fontSize: 10 }} />
              <YAxis tick={{ fill: "#6B7280", fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "#1E1E2A", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#F0F0F5" }} />
              <Area type="monotone" dataKey="count" stroke="#6C5CE7" fill="rgba(108,92,231,0.2)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {data.heatmap_data.length > 0 && (
        <div className="gradient-card p-6">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Contribution Heatmap</h3>
          <div className="flex gap-1 flex-wrap">
            {data.heatmap_data.map((d, i) => (
              <div key={i} className="w-3.5 h-3.5 rounded-sm" style={{ backgroundColor: d.level === 0 ? "var(--bg-input)" : `rgba(108, 92, 231, ${0.25 + d.level * 0.2})` }} title={`${d.date}: ${d.count} activities`} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
