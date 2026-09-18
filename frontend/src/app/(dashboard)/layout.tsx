/**
 * Dashboard Layout
 *
 * Layout wrapper for all authenticated pages.
 * Includes the sidebar and main content area.
 */

"use client";

import { useAuth } from "@/components/providers/auth-provider";
import { Sidebar } from "@/components/layout/sidebar";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-3 border-[var(--primary)] border-t-transparent rounded-full animate-spin-slow" />
          <p className="text-sm text-[var(--text-muted)]">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 mt-14 md:mt-0 md:ml-[var(--current-sidebar-width,var(--sidebar-width))] transition-all duration-300 overflow-y-auto">
        <div className="p-4 md:p-6 lg:p-8 max-w-7xl">{children}</div>
      </main>
    </div>
  );
}
