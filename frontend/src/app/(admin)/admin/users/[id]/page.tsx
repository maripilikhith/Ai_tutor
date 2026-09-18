"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Loader2, ArrowLeft, User, Mail, Calendar, Cpu, Zap, Activity } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface UserDetail {
  profile: {
    id: string;
    full_name: string;
    email: string;
    role: string;
    created_at: string;
  };
  ai_usage?: {
    total_requests: number;
    total_tokens: number;
    by_feature: Array<{ feature: string; requests: number; tokens: number }>;
  };
}

export default function UserDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [data, setData] = useState<UserDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<UserDetail>(`/admin/users/${id}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" /></div>;
  if (!data) return <div className="text-center py-12 text-[var(--text-muted)]">User not found</div>;

  const { profile, ai_usage } = data;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <button onClick={() => router.push("/admin/users")} className="p-2 hover:bg-[var(--bg-input)] rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5 text-[var(--text-secondary)]" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">User Details</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">Inspection view for {profile.full_name}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Profile Card */}
        <div className="gradient-card p-6">
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <User className="w-4 h-4 text-[var(--primary)]" /> Profile Information
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-xs text-[var(--text-muted)]">Full Name</p>
              <p className="font-medium text-[var(--text-primary)]">{profile.full_name || "—"}</p>
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] flex items-center gap-1"><Mail className="w-3 h-3" /> Email</p>
              <p className="font-medium text-[var(--text-primary)]">{profile.email}</p>
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)]">Role</p>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium inline-block mt-1 ${
                profile.role === "admin"
                  ? "bg-[var(--accent-red)]/10 text-[var(--accent-red)]"
                  : "bg-[var(--primary)]/10 text-[var(--primary-light)]"
              }`}>
                {profile.role}
              </span>
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] flex items-center gap-1"><Calendar className="w-3 h-3" /> Joined</p>
              <p className="text-sm text-[var(--text-secondary)]">{formatDate(profile.created_at)}</p>
            </div>
          </div>
        </div>

        {/* AI Usage Card */}
        <div className="gradient-card p-6">
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[var(--accent-cyan)]" /> AI Usage Metrics
          </h2>
          {ai_usage ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[var(--bg-input)] rounded-lg p-3 border border-[var(--border-default)]">
                  <p className="text-xs text-[var(--text-muted)] mb-1">Total Tokens Burned</p>
                  <p className="text-xl font-bold text-[var(--primary-light)] flex items-center gap-1">
                    <Zap className="w-4 h-4" /> {ai_usage.total_tokens.toLocaleString()}
                  </p>
                </div>
                <div className="bg-[var(--bg-input)] rounded-lg p-3 border border-[var(--border-default)]">
                  <p className="text-xs text-[var(--text-muted)] mb-1">Total API Requests</p>
                  <p className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-1">
                    <Activity className="w-4 h-4" /> {ai_usage.total_requests.toLocaleString()}
                  </p>
                </div>
              </div>

              {ai_usage.by_feature.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-[var(--text-secondary)] mb-2 uppercase tracking-wide">Usage by Feature</h3>
                  <div className="space-y-2">
                    {ai_usage.by_feature.map((f) => (
                      <div key={f.feature} className="flex items-center justify-between text-sm bg-[var(--bg-input)] p-2 rounded-md border border-[var(--border-subtle)]">
                        <span className="text-[var(--text-primary)] capitalize font-medium">{f.feature.replace("_", " ")}</span>
                        <div className="flex gap-4">
                          <span className="text-[var(--text-muted)] text-xs">{f.requests} reqs</span>
                          <span className="text-[var(--primary-light)] text-xs font-semibold">{f.tokens.toLocaleString()} tokens</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">No AI usage data available for this user.</p>
          )}
        </div>
      </div>
    </div>
  );
}
