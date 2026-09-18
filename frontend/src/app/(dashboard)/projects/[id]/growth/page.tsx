/**
 * Growth Page — Mastery growth chart over time
 */

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Loader2, TrendingUp } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import type { GrowthDataPoint } from "@/lib/types";

const COLORS = ["#6C5CE7", "#10B981", "#F59E0B", "#3B82F6", "#EC4899", "#06B6D4", "#EF4444", "#A29BFE"];

export default function GrowthPage() {
  const { id } = useParams();
  const projectId = id as string;
  const [dataPoints, setDataPoints] = useState<GrowthDataPoint[]>([]);
  const [concepts, setConcepts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ data_points: GrowthDataPoint[]; concepts: string[] }>(`/projects/${projectId}/growth`)
      .then((data) => { setDataPoints(data.data_points); setConcepts(data.concepts); })
      .catch(() => {}).finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="flex items-center justify-center h-40"><Loader2 className="w-6 h-6 text-[var(--primary)] animate-spin" /></div>;

  if (dataPoints.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-in">
        <TrendingUp className="w-16 h-16 mx-auto text-[var(--text-muted)] mb-4" />
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">No growth data yet</h3>
        <p className="text-sm text-[var(--text-muted)]">Take multiple quizzes to see your progress over time</p>
      </div>
    );
  }

  // Transform data for recharts: pivot by date
  const dateMap = new Map<string, Record<string, number>>();
  for (const dp of dataPoints) {
    if (!dateMap.has(dp.date)) dateMap.set(dp.date, {});
    dateMap.get(dp.date)![dp.concept_name] = dp.mastery_score;
  }
  const chartData = Array.from(dateMap.entries()).map(([date, values]) => ({ date, ...values }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="gradient-card p-6">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-6">Mastery Growth Over Time</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" tick={{ fill: "#6B7280", fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fill: "#6B7280", fontSize: 12 }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1E1E2A", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#F0F0F5" }}
              labelStyle={{ color: "#9CA3AF" }}
            />
            <Legend wrapperStyle={{ color: "#9CA3AF", fontSize: 12 }} />
            {concepts.map((concept, i) => (
              <Line key={concept} type="monotone" dataKey={concept} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 4 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
