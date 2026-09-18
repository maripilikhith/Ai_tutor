/**
 * Materials Page — Upload & manage learning materials
 */

"use client";

import useSWR from "swr";
import { useState } from "react";
import { useParams } from "next/navigation";
import { api, swrFetcher } from "@/lib/api";
import { formatDate, formatFileSize } from "@/lib/utils";
import { Upload, FileText, Loader2, Trash2, CheckCircle, AlertCircle, Clock } from "lucide-react";
import type { Material } from "@/lib/types";

export default function MaterialsPage() {
  const { id } = useParams();
  const projectId = id as string;
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const { data, isLoading: loading, mutate } = useSWR<{ items: Material[] }>(`/projects/${projectId}/materials`, swrFetcher, {
    refreshInterval: (data) => {
      const stillProcessing = data?.items.some((m) => m.status === "processing" || m.status === "queued");
      return stillProcessing ? 5000 : 0;
    }
  });

  const materials = data?.items || [];

  const handleUpload = async (files: FileList) => {
    setUploading(true);
    for (const file of Array.from(files)) {
      if (file.type !== "application/pdf") continue;
      try {
        await api.upload(`/projects/${projectId}/materials`, file);
      } catch {}
    }
    setUploading(false);
    mutate();
  };

  const handleDelete = async (materialId: string) => {
    try {
      await api.delete(`/projects/${projectId}/materials/${materialId}`);
      mutate({ items: materials.filter((m) => m.id !== materialId) }, false);
    } catch {}
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files);
  };

  if (loading) return <div className="flex items-center justify-center h-40"><Loader2 className="w-6 h-6 text-[var(--primary)] animate-spin" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Upload Zone */}
      <div
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
          dragActive
            ? "border-[var(--primary)] bg-[var(--primary)]/5"
            : "border-[var(--border-default)] hover:border-[var(--border-hover)]"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleUpload(e.target.files)}
        />
        {uploading ? (
          <Loader2 className="w-10 h-10 mx-auto text-[var(--primary)] animate-spin mb-3" />
        ) : (
          <Upload className="w-10 h-10 mx-auto text-[var(--text-muted)] mb-3" />
        )}
        <p className="text-sm font-medium text-[var(--text-primary)]">
          {uploading ? "Uploading..." : "Drop PDF files here or click to browse"}
        </p>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          PDF files only · Max 50MB per file
        </p>
      </div>

      {/* Materials List */}
      {materials.length > 0 ? (
        <div className="space-y-2">
          {materials.map((material) => (
            <div key={material.id} className="gradient-card p-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-[var(--primary)]/10 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-[var(--primary-light)]" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--text-primary)] truncate">{material.file_name}</p>
                <div className="flex items-center gap-3 mt-0.5">
                  <span className="text-xs text-[var(--text-muted)]">{formatFileSize(material.file_size_bytes)}</span>
                  {material.page_count > 0 && <span className="text-xs text-[var(--text-muted)]">{material.page_count} pages</span>}
                  <span className="text-xs text-[var(--text-muted)]">{formatDate(material.created_at)}</span>
                </div>
              </div>
              <StatusBadge status={material.status} />
              <button onClick={() => handleDelete(material.id)} className="p-2 rounded-lg hover:bg-red-500/10 text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-[var(--text-muted)]">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No materials uploaded yet</p>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "ready": return <span className="badge badge-success"><CheckCircle className="w-3 h-3" /> Ready</span>;
    case "processing": return <span className="badge badge-warning"><Loader2 className="w-3 h-3 animate-spin" /> Processing</span>;
    case "queued": return <span className="badge badge-info"><Clock className="w-3 h-3" /> Queued</span>;
    case "failed": return <span className="badge badge-danger"><AlertCircle className="w-3 h-3" /> Failed</span>;
    default: return <span className="badge">{status}</span>;
  }
}
