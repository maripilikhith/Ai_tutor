/**
 * Admin Activity Log Page
 */

"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, Activity } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface ActivityItem {
  id: string;
  event_type: string;
  user_id: string;
  created_at: string;
}

export default function AdminActivityPage() {
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ items: ActivityItem[] }>("/admin/activity-log")
      .then((d) => setItems(d.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Activity Log</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">System-wide event log across all users</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
        </div>
      ) : (
        <div className="gradient-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-default)] text-[var(--text-muted)] text-xs uppercase tracking-wide">
                <th className="text-left px-4 py-3">Event</th>
                <th className="text-left px-4 py-3">User</th>
                <th className="text-left px-4 py-3">Time</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)] transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Activity className="w-3.5 h-3.5 text-[var(--primary-light)]" />
                      <span className="text-[var(--text-secondary)] font-medium">{item.event_type.replace(/_/g, " ")}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-[var(--text-muted)] text-xs font-mono">{item.user_id?.slice(0, 8)}…</td>
                  <td className="px-4 py-3 text-[var(--text-muted)] text-xs">{formatDate(item.created_at)}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td colSpan={3} className="px-4 py-8 text-center text-[var(--text-muted)]">No activity yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
