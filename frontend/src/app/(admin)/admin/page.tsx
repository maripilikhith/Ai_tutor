/**
 * Admin Dashboard Page
 */

"use client";

import useSWR from "swr";
import Link from "next/link";
import { api, swrFetcher } from "@/lib/api";
import { Loader2, Users, FolderOpen, Brain, AlertTriangle, Activity, Shield, Cpu } from "lucide-react";

interface AdminDashboard {
  total_users: number;
  total_spaces: number;
  total_projects: number;
  total_quizzes: number;
  pending_jobs: number;
  failed_jobs: number;
}

export default function AdminPage() {
  const { data, isLoading: loading } = useSWR<AdminDashboard>("/admin/dashboard", swrFetcher);

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)] flex items-center gap-2"><Shield className="w-6 h-6 text-[var(--primary)]" /> Admin Panel</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">System overview and management</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 stagger-children">
        <AdminStat icon={Users} label="Users" value={data?.total_users ?? 0} />
        <AdminStat icon={FolderOpen} label="Spaces" value={data?.total_spaces ?? 0} />
        <AdminStat icon={FolderOpen} label="Projects" value={data?.total_projects ?? 0} />
        <AdminStat icon={Brain} label="Quizzes" value={data?.total_quizzes ?? 0} />
        <AdminStat icon={Activity} label="Pending Jobs" value={data?.pending_jobs ?? 0} color="var(--accent-amber)" />
        <AdminStat icon={AlertTriangle} label="Failed Jobs" value={data?.failed_jobs ?? 0} color="var(--accent-red)" />
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Link href="/admin/users" className="gradient-card p-5 group">
          <Users className="w-8 h-8 text-[var(--primary-light)] mb-3" />
          <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--primary-light)]">User Management</h3>
          <p className="text-xs text-[var(--text-muted)] mt-1">View and inspect user accounts</p>
        </Link>
        <Link href="/admin/ai-usage" className="gradient-card p-5 group">
          <Cpu className="w-8 h-8 text-[var(--accent-cyan)] mb-3" />
          <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--primary-light)]">AI Usage</h3>
          <p className="text-xs text-[var(--text-muted)] mt-1">Token usage, costs, and model metrics</p>
        </Link>
        <Link href="/admin/activity" className="gradient-card p-5 group">
          <Activity className="w-8 h-8 text-[var(--accent-green)] mb-3" />
          <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--primary-light)]">Activity Log</h3>
          <p className="text-xs text-[var(--text-muted)] mt-1">System-wide event log</p>
        </Link>
      </div>
    </div>
  );
}

function AdminStat({ icon: Icon, label, value, color }: { icon: React.ComponentType<{ className?: string }>; label: string; value: number; color?: string }) {
  return (
    <div className="stat-card text-center py-4">
      <div className="flex justify-center mb-2" style={{ color: color || "var(--text-muted)" }}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-xl font-bold text-[var(--text-primary)]">{value}</p>
      <p className="text-[10px] text-[var(--text-muted)]">{label}</p>
    </div>
  );
}
