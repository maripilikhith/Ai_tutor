/**
 * Admin Layout
 *
 * Protected layout for admin-only pages.
 * Redirects non-admin users to the dashboard immediately.
 */

"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/auth-provider";
import { cn } from "@/lib/utils";
import {
  Shield,
  Users,
  Activity,
  Cpu,
  LayoutDashboard,
  ChevronLeft,
  Brain,
  Loader2,
} from "lucide-react";

const adminNav = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/ai-usage", label: "AI Usage", icon: Cpu },
  { href: "/admin/activity", label: "Activity Log", icon: Activity },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isAdmin = user?.user_metadata?.role === "admin";

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    if (!isAdmin) {
      router.push("/dashboard");
    }
  }, [user, loading, isAdmin, router]);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
      </div>
    );
  }

  if (!user || !isAdmin) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)]">
      {/* Admin Sidebar */}
      <aside className="w-56 flex-shrink-0 flex flex-col bg-[var(--bg-secondary)] border-r border-[var(--border-default)]">
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-[var(--border-default)]">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--accent-red)] to-[var(--primary)] flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-[var(--text-primary)] leading-tight">
              Admin Panel
            </h1>
            <p className="text-[10px] text-[var(--text-muted)]">AI Study Companion</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {adminNav.map((item) => {
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn("nav-item", isActive && "active")}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Back to app */}
        <div className="px-3 py-4 border-t border-[var(--border-default)]">
          <Link
            href="/dashboard"
            className="nav-item text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            <ChevronLeft className="w-5 h-5" />
            <span className="text-sm">Back to App</span>
          </Link>
          <div className="mt-3 px-2">
            <p className="text-[10px] text-[var(--text-muted)] truncate">
              {user?.email}
            </p>
            <span className="inline-flex items-center gap-1 text-[10px] bg-[var(--accent-red)]/10 text-[var(--accent-red)] px-2 py-0.5 rounded-full mt-1">
              <Shield className="w-2.5 h-2.5" /> Admin
            </span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 max-w-7xl">{children}</div>
      </main>
    </div>
  );
}
