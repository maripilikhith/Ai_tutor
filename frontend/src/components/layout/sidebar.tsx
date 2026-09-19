/**
 * Sidebar Component
 *
 * Main navigation sidebar with:
 * - App logo
 * - Navigation links
 * - Space quick-access tree
 * - User profile section
 */

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import useSWR from "swr";
import { useAuth } from "@/components/providers/auth-provider";
import { api, swrFetcher } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  Home,
  BookOpen,
  BarChart3,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  CornerDownRight,
  Brain,
  Shield,
  Folder,
  FolderOpen,
  Sun,
  Moon,
  Menu
} from "lucide-react";
import { useTheme } from "next-themes";

interface ProjectSimple {
  id: string;
  name: string;
}

interface SidebarSpace {
  id: string;
  name: string;
  projects: ProjectSimple[];
}

interface ProfileData {
  full_name: string;
  avatar_url: string | null;
}

const navItems = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/spaces", label: "Spaces", icon: BookOpen },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

function SpacesTree({ pathname, closeMobile }: { pathname: string, closeMobile?: () => void }) {
  const [spaces, setSpaces] = useState<SidebarSpace[]>([]);
  const [expandedSpaces, setExpandedSpaces] = useState<Record<string, boolean>>({});
  const [expandedProjects, setExpandedProjects] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.get<{ items: SidebarSpace[] }>("/spaces")
      .then((res) => {
        setSpaces(res.items || []);
        // Expand first space by default if available
        if (res.items?.length > 0) {
          setExpandedSpaces({ [res.items[0].id]: true });
        }
      })
      .catch(console.error);
  }, []);

  const toggleSpace = (id: string) => {
    setExpandedSpaces(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleProject = (id: string) => {
    setExpandedProjects(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (spaces.length === 0) return null;

  return (
    <div className="mt-6 px-3">
      <div className="flex items-center justify-between px-2 mb-2">
        <span className="text-[10px] font-bold text-[var(--text-muted)] tracking-wider uppercase">My Spaces</span>
        <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />
      </div>

      <div className="space-y-1">
        {spaces.map(space => (
          <div key={space.id} className="animate-fade-in">
            {/* Space Row */}
            <div 
              onClick={() => toggleSpace(space.id)}
              className="flex items-center justify-between px-2 py-1.5 cursor-pointer rounded-md hover:bg-[var(--bg-card)] transition-colors group"
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <ChevronRight className={cn("w-3.5 h-3.5 text-[var(--text-muted)] transition-transform flex-shrink-0", expandedSpaces[space.id] && "rotate-90")} />
                {expandedSpaces[space.id] ? (
                  <FolderOpen className="w-4 h-4 text-[var(--primary)] flex-shrink-0" />
                ) : (
                  <Folder className="w-4 h-4 text-[var(--primary-light)] flex-shrink-0" />
                )}
                <span className="text-sm font-medium text-[var(--text-primary)] truncate group-hover:text-white transition-colors">{space.name}</span>
              </div>
              <span className="text-[10px] text-[var(--text-muted)] flex-shrink-0">{space.projects?.length || 0} items</span>
            </div>

            {/* Projects for this Space */}
            {expandedSpaces[space.id] && space.projects?.map(project => (
              <div key={project.id} className="ml-5 mt-1 border-l border-[var(--border-subtle)] pl-2">
                <div 
                  onClick={() => toggleProject(project.id)}
                  className="flex items-center gap-2 px-2 py-1.5 cursor-pointer rounded-md hover:bg-[var(--bg-card)] transition-colors group"
                >
                  <ChevronRight className={cn("w-3.5 h-3.5 text-[var(--text-muted)] transition-transform flex-shrink-0", expandedProjects[project.id] && "rotate-90")} />
                  {expandedProjects[project.id] ? (
                    <FolderOpen className="w-3.5 h-3.5 text-[var(--accent-green)] flex-shrink-0 group-hover:text-[var(--accent-cyan)] transition-colors" />
                  ) : (
                    <Folder className="w-3.5 h-3.5 text-[var(--accent-green)] flex-shrink-0 group-hover:text-[var(--accent-cyan)] transition-colors" />
                  )}
                  <span className="text-[13px] font-medium text-[var(--text-secondary)] truncate group-hover:text-[var(--text-primary)] transition-colors">{project.name}</span>
                </div>

                {/* Project Sub-tabs */}
                {expandedProjects[project.id] && (
                  <div className="ml-4 mt-1 space-y-0.5">
                  {[
                    { name: "Dashboard", path: "" },
                    { name: "Materials", path: "/materials" },
                    { name: "AI Tutor", path: "/tutor", badge: "LIVE" },
                    { name: "Quiz", path: "/quiz" },
                    { name: "Mastery", path: "/mastery" },
                    { name: "Growth", path: "/growth" },
                  ].map(tab => {
                    const href = `/projects/${project.id}${tab.path}`;
                    const isActive = pathname === href;
                    return (
                      <Link
                        key={tab.name}
                        href={href}
                        onClick={closeMobile}
                        className={cn(
                          "flex items-center justify-between px-3 py-1.5 rounded-md text-xs transition-colors group",
                          isActive 
                            ? "bg-[var(--primary)]/10 text-[var(--primary-light)] font-medium" 
                            : "text-[var(--text-muted)] hover:bg-[var(--bg-card)] hover:text-[var(--text-secondary)]"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          {tab.name === "AI Tutor" && <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)]" />}
                          <span>{tab.name}</span>
                        </div>
                        {tab.badge && (
                          <span className="text-[8px] px-1.5 py-0.5 bg-[var(--primary)]/20 text-[var(--primary-light)] font-bold rounded uppercase">
                            {tab.badge}
                          </span>
                        )}
                      </Link>
                    );
                  })}
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const { data: profile } = useSWR<ProfileData>("/profile", swrFetcher);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  // Sync sidebar width for layout.tsx to use
  useEffect(() => {
    document.documentElement.style.setProperty(
      '--current-sidebar-width', 
      collapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)'
    );
  }, [collapsed]);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const isAdmin = user?.user_metadata?.role === "admin";

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-[var(--bg-secondary)] border-b border-[var(--border-default)] flex items-center justify-between px-4 z-30">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--primary-dark)] flex items-center justify-center">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-sm text-[var(--text-primary)]">AI Study Companion</span>
        </div>
        <button 
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)]"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-fade-in"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Content */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 h-screen flex flex-col",
          "bg-[var(--bg-secondary)] border-r border-[var(--border-default)]",
          "transition-all duration-300 ease-in-out",
          // Desktop width
          collapsed ? "md:w-[var(--sidebar-collapsed)]" : "md:w-[var(--sidebar-width)]",
          // Mobile responsive: hidden by sliding left, full width or fixed width
          "w-[var(--sidebar-width)]",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          "overflow-y-auto overflow-x-hidden"
        )}
      >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-[var(--border-default)] sticky top-0 bg-[var(--bg-secondary)] z-10">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--primary)] to-[var(--primary-dark)] flex items-center justify-center flex-shrink-0">
          <Brain className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <h1 className="text-sm font-semibold text-[var(--text-primary)] leading-tight">
              AI Study
            </h1>
            <p className="text-[10px] text-[var(--text-muted)]">Companion</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1">
        <div className="px-3 space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href + "/"));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn("nav-item", isActive && "active")}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span className="text-sm">{item.label}</span>}
              </Link>
            );
          })}
        </div>

        {/* Dynamic Spaces Tree */}
        {!collapsed && <SpacesTree pathname={pathname} />}

        {/* Admin shortcut for admins */}
        {isAdmin && (
          <div className="px-3 mt-6">
            <div className="my-3 border-t border-[var(--border-default)]" />
            <Link
              href="/admin"
              className={cn("nav-item text-[var(--accent-red)]/80 hover:text-[var(--accent-red)]")}
              title={collapsed ? "Admin Panel" : undefined}
            >
              <Shield className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span className="text-sm">Admin Panel</span>}
            </Link>
          </div>
        )}
      </nav>

      {/* Theme & Collapse toggle */}
      <div className="sticky bottom-[73px] bg-[var(--bg-secondary)] pt-2 pb-2 flex items-center justify-between px-3 border-t border-[var(--border-default)]">
        {mounted && !collapsed && (
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="flex items-center gap-2 p-2 rounded-lg hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            title="Toggle theme"
          >
            {theme === "dark" ? (
              <>
                <Sun className="w-4 h-4" />
                <span className="text-xs font-medium">Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4" />
                <span className="text-xs font-medium">Dark Mode</span>
              </>
            )}
          </button>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "p-2 rounded-lg hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors",
            collapsed && "mx-auto"
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* User section — click to go to profile */}
      <div className="px-3 py-3 border-t border-[var(--border-default)] sticky bottom-0 bg-[var(--bg-secondary)] z-10">
        <Link href="/profile" className="flex items-center gap-3 rounded-lg p-1 hover:bg-[var(--bg-card-hover)] transition-colors group">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--accent-cyan)] flex items-center justify-center flex-shrink-0 overflow-hidden">
            {profile?.avatar_url || user?.user_metadata?.avatar_url || user?.user_metadata?.picture ? (
              <img src={profile?.avatar_url || user?.user_metadata?.avatar_url || user?.user_metadata?.picture} alt="avatar" className="w-full h-full object-cover" />
            ) : (
              <span className="text-xs font-bold text-white">
                {(profile?.full_name || user?.user_metadata?.full_name || user?.email || "U").charAt(0).toUpperCase()}
              </span>
            )}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--text-primary)] truncate group-hover:text-[var(--primary-light)] transition-colors">
                {profile?.full_name || user?.user_metadata?.full_name || "Student"}
              </p>
              <p className="text-xs text-[var(--text-muted)] truncate">
                {user?.email}
              </p>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={(e) => { e.preventDefault(); signOut(); }}
              className="p-1.5 rounded-md hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </Link>
      </div>
    </aside>
    </>
  );
}
