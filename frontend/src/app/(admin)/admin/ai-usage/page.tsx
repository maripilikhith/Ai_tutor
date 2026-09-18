/**
 * Admin AI Usage Page
 */

"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, Cpu, Zap, Clock } from "lucide-react";

interface AIUsageStats {
  total_requests: number;
  total_tokens: number;
  avg_latency_ms: number;
  success_rate: number;
  by_feature: Array<{ feature: string; requests: number; tokens: number }>;
  by_model: Array<{ model: string; requests: number }>;
}

export default function AdminAIUsagePage() {
  const [data, setData] = useState<AIUsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AIUsageStats>("/admin/ai-usage")
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">AI Usage</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">Token consumption, latency, and model metrics</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Cpu, label: "Total Requests", value: data?.total_requests?.toLocaleString() ?? "0" },
          { icon: Zap, label: "Total Tokens", value: data?.total_tokens?.toLocaleString() ?? "0" },
          { icon: Clock, label: "Avg Latency", value: `${data?.avg_latency_ms ?? 0}ms` },
          { icon: Cpu, label: "Success Rate", value: `${((data?.success_rate ?? 0) * 100).toFixed(1)}%` },
        ].map((stat) => (
          <div key={stat.label} className="stat-card">
            <stat.icon className="w-5 h-5 text-[var(--primary-light)] mb-2" />
            <p className="text-xl font-bold text-[var(--text-primary)]">{stat.value}</p>
            <p className="text-xs text-[var(--text-muted)]">{stat.label}</p>
          </div>
        ))}
      </div>

      {data?.by_feature && data.by_feature.length > 0 && (
        <div className="gradient-card p-5">
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Usage by Feature</h2>
          <div className="space-y-2">
            {data.by_feature.map((f) => (
              <div key={f.feature} className="flex items-center justify-between text-sm">
                <span className="text-[var(--text-secondary)] capitalize">{f.feature}</span>
                <div className="flex gap-4">
                  <span className="text-[var(--text-muted)] text-xs">{f.requests} reqs</span>
                  <span className="text-[var(--primary-light)] text-xs font-medium">{f.tokens?.toLocaleString()} tokens</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
