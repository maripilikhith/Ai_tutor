/**
 * Spaces List Page
 *
 * Grid of all user spaces with project counts.
 * Includes create space modal and delete option.
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Plus, BookOpen, Loader2, X, Trash2 } from "lucide-react";
import type { Space } from "@/lib/types";

const SPACE_COLORS = [
  "#6C5CE7", "#00B894", "#E17055", "#0984E3",
  "#D63031", "#FDCB6E", "#E84393", "#00CEC9",
];
const SPACE_ICONS = ["📚", "🧪", "💻", "🎨", "📐", "🌍", "🧠", "🎯"];

export default function SpacesPage() {
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Space | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadSpaces();
  }, []);

  async function loadSpaces() {
    try {
      const data = await api.get<{ items: Space[] }>("/spaces");
      setSpaces(data.items);
    } catch {} finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/spaces/${deleteTarget.id}`);
      setSpaces((prev) => prev.filter((s) => s.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch {} finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Spaces</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Organize your learning into spaces
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Space
        </button>
      </div>

      {spaces.length > 0 ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
          {spaces.map((space) => (
            <div key={space.id} className="gradient-card p-5 group relative">
              {/* Delete button — top right on hover */}
              <button
                onClick={(e) => { e.preventDefault(); setDeleteTarget(space); }}
                className="absolute top-3 right-3 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 hover:text-red-400 text-[var(--text-muted)] transition-all"
                title="Delete space"
              >
                <Trash2 className="w-4 h-4" />
              </button>

              <Link href={`/spaces/${space.id}`} className="block">
                <div className="flex items-center gap-3 mb-3">
                  <span
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                    style={{ backgroundColor: `${space.color}20` }}
                  >
                    {space.icon}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-[var(--text-primary)] truncate group-hover:text-[var(--primary-light)] transition-colors">
                      {space.name}
                    </h3>
                    <p className="text-xs text-[var(--text-muted)]">
                      {space.project_count} project{space.project_count !== 1 ? "s" : ""} · {formatDate(space.updated_at)}
                    </p>
                  </div>
                </div>
                {space.description && (
                  <p className="text-sm text-[var(--text-muted)] line-clamp-2">{space.description}</p>
                )}
              </Link>
            </div>
          ))}
        </div>
      ) : (
        <div className="gradient-card p-12 text-center">
          <BookOpen className="w-16 h-16 mx-auto text-[var(--text-muted)] mb-4" />
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">No spaces yet</h3>
          <p className="text-sm text-[var(--text-muted)] mb-6 max-w-md mx-auto">
            Spaces help you organize your learning. Create one for each subject or course.
          </p>
          <button onClick={() => setShowCreate(true)} className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" /> Create Your First Space
          </button>
        </div>
      )}

      {/* Create Space Modal */}
      {showCreate && (
        <CreateSpaceModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); loadSpaces(); }} />
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setDeleteTarget(null)}>
          <div className="glass-card p-6 w-full max-w-sm mx-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="font-semibold text-[var(--text-primary)]">Delete Space</h3>
                <p className="text-xs text-[var(--text-muted)]">This action cannot be undone</p>
              </div>
            </div>
            <p className="text-sm text-[var(--text-secondary)] mb-6">
              Are you sure you want to delete <span className="font-semibold text-[var(--text-primary)]">{deleteTarget.name}</span>? All projects and learning data inside it will be permanently deleted.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setDeleteTarget(null)} className="btn-secondary flex-1">Cancel</button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-colors text-sm font-medium disabled:opacity-50"
              >
                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {deleting ? "Deleting..." : "Delete Space"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CreateSpaceModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState(SPACE_COLORS[0]);
  const [icon, setIcon] = useState(SPACE_ICONS[0]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post("/spaces", { name, description, color, icon });
      onCreated();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create space. Please try again.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-card p-6 w-full max-w-md mx-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Create Space</h2>
          <button onClick={onClose} className="p-1 hover:bg-[var(--bg-card-hover)] rounded-lg">
            <X className="w-5 h-5 text-[var(--text-muted)]" />
          </button>
        </div>

        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input-field" placeholder="e.g., Computer Science" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="input-field resize-none h-20" placeholder="What will you learn here?" />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Icon</label>
            <div className="flex gap-2 flex-wrap">
              {SPACE_ICONS.map((i) => (
                <button key={i} type="button" onClick={() => setIcon(i)}
                  className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl transition-all ${icon === i ? "bg-[var(--primary)]/20 ring-2 ring-[var(--primary)]" : "bg-[var(--bg-input)] hover:bg-[var(--bg-card-hover)]"}`}
                >{i}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Color</label>
            <div className="flex gap-2">
              {SPACE_COLORS.map((c) => (
                <button key={c} type="button" onClick={() => setColor(c)}
                  className={`w-8 h-8 rounded-full transition-all ${color === c ? "ring-2 ring-offset-2 ring-offset-[var(--bg-card)] ring-white" : ""}`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={saving || !name} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              {saving ? "Creating..." : "Create Space"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
