/**
 * Space Dashboard Page
 *
 * Shows a single space with its projects.
 */

"use client";

import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api, swrFetcher } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Plus, ArrowLeft, Loader2, FolderOpen, X, Trash2 } from "lucide-react";
import type { Space, Project } from "@/lib/types";

export default function SpaceDashboardPage() {
  const params = useParams();
  const spaceId = params.id as string;
  const router = useRouter();
  
  const { data: space, isLoading: spaceLoading } = useSWR<Space>(`/spaces/${spaceId}`, swrFetcher);
  const { data: projectsData, isLoading: projectsLoading, mutate: mutateProjects } = useSWR<{ items: Project[] }>(`/projects?space_id=${spaceId}`, swrFetcher);
  
  const projects = projectsData?.items || [];
  const loading = spaceLoading || projectsLoading;

  const [showCreate, setShowCreate] = useState(false);
  const [deleteProjectTarget, setDeleteProjectTarget] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState(false);
  const [deletingSpace, setDeletingSpace] = useState(false);
  const [confirmDeleteSpace, setConfirmDeleteSpace] = useState(false);

  async function handleDeleteProject() {
    if (!deleteProjectTarget) return;
    setDeletingProject(true);
    try {
      await api.delete(`/projects/${deleteProjectTarget.id}`);
      mutateProjects({ items: projects.filter((p) => p.id !== deleteProjectTarget.id) }, false);
      setDeleteProjectTarget(null);
    } catch {} finally { setDeletingProject(false); }
  }

  async function handleDeleteSpace() {
    setDeletingSpace(true);
    try {
      await api.delete(`/spaces/${spaceId}`);
      router.push("/spaces");
    } catch {} finally { setDeletingSpace(false); }
  }

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" /></div>;
  if (!space) return <div className="text-center py-20 text-[var(--text-muted)]">Space not found</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-2">
        <Link href="/spaces" className="p-2 rounded-lg hover:bg-[var(--bg-card)] text-[var(--text-muted)]"><ArrowLeft className="w-4 h-4" /></Link>
        <span className="text-2xl">{space.icon}</span>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">{space.name}</h1>
          {space.description && <p className="text-sm text-[var(--text-muted)]">{space.description}</p>}
        </div>
        {/* Delete this space */}
        <button
          onClick={() => setConfirmDeleteSpace(true)}
          className="p-2 rounded-lg hover:bg-red-500/10 hover:text-red-400 text-[var(--text-muted)] transition-colors"
          title="Delete this space"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--text-muted)]">{projects.length} project{projects.length !== 1 ? "s" : ""}</p>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {projects.length > 0 ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
          {projects.map((project) => (
            <div key={project.id} className="gradient-card p-5 group relative">
              {/* Delete project button */}
              <button
                onClick={() => setDeleteProjectTarget(project)}
                className="absolute top-3 right-3 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 hover:text-red-400 text-[var(--text-muted)] transition-all"
                title="Delete project"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <Link href={`/projects/${project.id}`} className="block">
                <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--primary-light)] transition-colors mb-1 pr-6">{project.name}</h3>
                {project.learning_goal && <p className="text-xs text-[var(--text-muted)] line-clamp-2 mb-3">{project.learning_goal}</p>}
                <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
                  <span>{project.material_count} materials</span>
                  <span>{project.quiz_count} quizzes</span>
                  <span>{project.avg_mastery.toFixed(0)}% mastery</span>
                </div>
                <div className="mt-3 w-full bg-[var(--bg-input)] rounded-full h-1.5">
                  <div className="h-1.5 rounded-full bg-gradient-to-r from-[var(--primary)] to-[var(--accent-cyan)] transition-all" style={{ width: `${project.avg_mastery}%` }} />
                </div>
              </Link>
            </div>
          ))}
        </div>
      ) : (
        <div className="gradient-card p-12 text-center">
          <FolderOpen className="w-16 h-16 mx-auto text-[var(--text-muted)] mb-4" />
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">No projects yet</h3>
          <p className="text-sm text-[var(--text-muted)] mb-6">Create a project to start learning</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" /> Create Project
          </button>
        </div>
      )}

      {showCreate && <CreateProjectModal spaceId={spaceId} onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); mutateProjects(); }} />}

      {/* Delete Project Modal */}
      {deleteProjectTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setDeleteProjectTarget(null)}>
          <div className="glass-card p-6 w-full max-w-sm mx-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center"><Trash2 className="w-5 h-5 text-red-400" /></div>
              <div>
                <h3 className="font-semibold text-[var(--text-primary)]">Delete Project</h3>
                <p className="text-xs text-[var(--text-muted)]">This action cannot be undone</p>
              </div>
            </div>
            <p className="text-sm text-[var(--text-secondary)] mb-6">
              Delete <span className="font-semibold text-[var(--text-primary)]">{deleteProjectTarget.name}</span>? All materials, chats, and quiz data will be permanently removed.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setDeleteProjectTarget(null)} className="btn-secondary flex-1">Cancel</button>
              <button onClick={handleDeleteProject} disabled={deletingProject} className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-colors text-sm font-medium disabled:opacity-50">
                {deletingProject ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {deletingProject ? "Deleting..." : "Delete Project"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Space Modal */}
      {confirmDeleteSpace && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setConfirmDeleteSpace(false)}>
          <div className="glass-card p-6 w-full max-w-sm mx-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center"><Trash2 className="w-5 h-5 text-red-400" /></div>
              <div>
                <h3 className="font-semibold text-[var(--text-primary)]">Delete Space</h3>
                <p className="text-xs text-[var(--text-muted)]">This will delete everything inside</p>
              </div>
            </div>
            <p className="text-sm text-[var(--text-secondary)] mb-6">
              Delete <span className="font-semibold text-[var(--text-primary)]">{space?.name}</span> and all its projects permanently?
            </p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDeleteSpace(false)} className="btn-secondary flex-1">Cancel</button>
              <button onClick={handleDeleteSpace} disabled={deletingSpace} className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-colors text-sm font-medium disabled:opacity-50">
                {deletingSpace ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {deletingSpace ? "Deleting..." : "Delete Space"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CreateProjectModal({ spaceId, onClose, onCreated }: { spaceId: string; onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [goal, setGoal] = useState("");
  const [saving, setSaving] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/projects", { name, description, learning_goal: goal, space_id: spaceId });
      onCreated();
    } catch {} finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-card p-6 w-full max-w-md mx-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Create Project</h2>
          <button onClick={onClose} className="p-1 hover:bg-[var(--bg-card-hover)] rounded-lg"><X className="w-5 h-5 text-[var(--text-muted)]" /></button>
        </div>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Project Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input-field" placeholder="e.g., Data Structures" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Learning Goal</label>
            <input type="text" value={goal} onChange={(e) => setGoal(e.target.value)} className="input-field" placeholder="What do you want to learn?" />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="input-field resize-none h-20" placeholder="Optional details" />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={saving || !name} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              {saving ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
