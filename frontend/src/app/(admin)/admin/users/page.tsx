/**
 * Admin Users Page
 */

"use client";

import useSWR from "swr";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, swrFetcher } from "@/lib/api";
import { Loader2, User, Search, ChevronRight } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface AdminUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
  space_count: number;
  project_count: number;
  quiz_count: number;
  created_at: string;
}

export default function AdminUsersPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const { data, isLoading: loading } = useSWR<{ items: AdminUser[] }>("/admin/users", swrFetcher);
  const users = data?.items || [];

  const filtered = users.filter(
    (u) =>
      u.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">User Management</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">View and inspect all registered users</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-9 w-full max-w-sm"
        />
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
                <th className="text-left px-4 py-3">User</th>
                <th className="text-left px-4 py-3">Role</th>
                <th className="text-center px-4 py-3">Spaces</th>
                <th className="text-center px-4 py-3">Projects</th>
                <th className="text-center px-4 py-3">Quizzes</th>
                <th className="text-left px-4 py-3">Joined</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr
                  key={u.id}
                  onClick={() => router.push(`/admin/users/${u.id}`)}
                  className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)] cursor-pointer transition-colors group"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--accent-cyan)] flex items-center justify-center">
                        <User className="w-3.5 h-3.5 text-white" />
                      </div>
                      <div>
                        <p className="font-medium text-[var(--text-primary)]">{u.full_name || "—"}</p>
                        <p className="text-[10px] text-[var(--text-muted)]">{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      u.role === "admin"
                        ? "bg-[var(--accent-red)]/10 text-[var(--accent-red)]"
                        : "bg-[var(--primary)]/10 text-[var(--primary-light)]"
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-[var(--text-secondary)]">{u.space_count}</td>
                  <td className="px-4 py-3 text-center text-[var(--text-secondary)]">{u.project_count}</td>
                  <td className="px-4 py-3 text-center text-[var(--text-secondary)]">{u.quiz_count}</td>
                  <td className="px-4 py-3 text-[var(--text-muted)] text-xs">
                    <div className="flex items-center justify-between">
                      {formatDate(u.created_at)}
                      <ChevronRight className="w-4 h-4 text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-[var(--text-muted)]">No users found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
