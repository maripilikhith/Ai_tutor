/**
 * Profile Page
 * 
 * Lets users update their display name, bio, and avatar URL.
 * Avatar can be pasted as a URL (Google photo URL works out of the box).
 */

"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/auth-provider";
import { User, Camera, Loader2, CheckCircle, Mail, BookOpen, Edit2, X } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface Profile {
  id: string;
  full_name: string;
  email: string;
  avatar_url: string | null;
  bio: string | null;
  created_at: string | null;
  use_custom_key?: boolean;
  gemini_api_key?: string;
}

export default function ProfilePage() {
  const { user, updateUserMetadata } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [avatarInput, setAvatarInput] = useState(false);
  const [useCustomKey, setUseCustomKey] = useState(false);
  const [geminiApiKey, setGeminiApiKey] = useState("");

  useEffect(() => {
    api.get<Profile>("/profile")
      .then((data) => {
        setProfile(data);
        setName(data.full_name || "");
        setBio(data.bio || "");
        setAvatarUrl(data.avatar_url || "");
        setUseCustomKey(data.use_custom_key || false);
        setGeminiApiKey(data.gemini_api_key || "");
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.put<Profile>("/profile", {
        full_name: name.trim() || undefined,
        bio: bio.trim() || undefined,
        avatar_url: avatarUrl.trim() || undefined,
        use_custom_key: useCustomKey,
        gemini_api_key: geminiApiKey.trim() || undefined,
      });
      
      // Update the auth session metadata so sidebar and other components update instantly
      if (updateUserMetadata) {
        await updateUserMetadata({
          full_name: updated.full_name,
          avatar_url: updated.avatar_url,
        }).catch(console.error);
      }

      setProfile(updated);
      setSaved(true);
      setEditMode(false);
      setAvatarInput(false);
      setTimeout(() => setSaved(false), 3000);
    } catch {} finally { setSaving(false); }
  };

  const handleCancel = () => {
    if (profile) {
      setName(profile.full_name || "");
      setBio(profile.bio || "");
      setAvatarUrl(profile.avatar_url || "");
      setUseCustomKey(profile.use_custom_key || false);
      setGeminiApiKey(profile.gemini_api_key || "");
    }
    setEditMode(false);
    setAvatarInput(false);
  };

  const displayAvatar = avatarUrl || profile?.avatar_url || user?.user_metadata?.avatar_url || null;
  const displayName = profile?.full_name || user?.user_metadata?.full_name || "User";
  const email = profile?.email || user?.email || "";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">My Profile</h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">Manage your account details</p>
        </div>
        {!editMode && (
          <button onClick={() => setEditMode(true)} className="btn-secondary flex items-center gap-2 text-sm">
            <Edit2 className="w-4 h-4" /> Edit Profile
          </button>
        )}
      </div>

      {/* Avatar + Name card */}
      <div className="gradient-card p-6">
        <div className="flex items-start gap-5">
          {/* Avatar */}
          <div className="relative flex-shrink-0">
            <div className="w-20 h-20 rounded-2xl overflow-hidden bg-gradient-to-br from-[var(--primary)] to-[var(--accent-cyan)] flex items-center justify-center">
              {displayAvatar ? (
                <img src={displayAvatar} alt={displayName} className="w-full h-full object-cover" />
              ) : (
                <span className="text-3xl font-bold text-white">{displayName.charAt(0).toUpperCase()}</span>
              )}
            </div>
            {editMode && (
              <button
                onClick={() => setAvatarInput((v) => !v)}
                className="absolute -bottom-2 -right-2 w-7 h-7 rounded-full bg-[var(--primary)] flex items-center justify-center shadow-lg hover:opacity-90 transition-opacity"
                title="Change avatar"
              >
                <Camera className="w-3.5 h-3.5 text-white" />
              </button>
            )}
          </div>

          {/* Name + email */}
          <div className="flex-1 min-w-0">
            {editMode ? (
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field text-lg font-semibold mb-2"
                placeholder="Your display name"
              />
            ) : (
              <h2 className="text-xl font-bold text-[var(--text-primary)] mb-1">{displayName}</h2>
            )}
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Mail className="w-3.5 h-3.5" />
              <span>{email}</span>
            </div>
            {profile?.created_at && (
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mt-1">
                <BookOpen className="w-3 h-3" />
                <span>Member since {formatDate(profile.created_at)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Avatar URL input */}
        {editMode && avatarInput && (
          <div className="mt-4 pt-4 border-t border-[var(--border-default)]">
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
              Avatar URL <span className="text-[var(--text-muted)]">(paste an image link)</span>
            </label>
            <input
              type="url"
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              className="input-field text-sm"
              placeholder="https://example.com/photo.jpg"
            />
          </div>
        )}
      </div>

      {/* Bio card */}
      <div className="gradient-card p-6">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">About</h3>
        {editMode ? (
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className="input-field resize-none h-24 text-sm"
            placeholder="Tell us a bit about yourself — what you're studying, your goals..."
          />
        ) : (
          <p className="text-sm text-[var(--text-muted)]">
            {profile?.bio || "No bio yet. Click Edit Profile to add one."}
          </p>
        )}
      </div>

      {/* Account info card */}
      <div className="gradient-card p-6">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Account Info</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-[var(--border-default)]">
            <span className="text-sm text-[var(--text-muted)]">Email</span>
            <span className="text-sm text-[var(--text-primary)]">{email}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-[var(--border-default)]">
            <span className="text-sm text-[var(--text-muted)]">Sign-in method</span>
            <span className="text-sm text-[var(--text-primary)] capitalize">
              {user?.app_metadata?.provider || "email"}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-[var(--text-muted)]">Account ID</span>
            <span className="text-xs font-mono text-[var(--text-muted)] truncate max-w-[180px]">{user?.id}</span>
          </div>
        </div>
      </div>

      {/* AI Settings Card */}
      <div className="gradient-card p-6">
        <div className="flex flex-col gap-1 mb-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">AI Settings</h3>
          <p className="text-xs text-[var(--text-muted)]">
            By default, we use the system's AI key. You can provide your own to avoid rate limits.
          </p>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2 border-b border-[var(--border-default)]">
            <span className="text-sm text-[var(--text-primary)] font-medium">Use Custom API Key</span>
            <button 
              onClick={() => editMode && setUseCustomKey(!useCustomKey)}
              disabled={!editMode}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${useCustomKey ? 'bg-[var(--primary)]' : 'bg-[var(--bg-card-hover)]'} ${!editMode && 'opacity-50 cursor-not-allowed'}`}
            >
              <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${useCustomKey ? 'translate-x-5' : 'translate-x-1'}`} />
            </button>
          </div>
          
          {(useCustomKey || (editMode && useCustomKey)) && (
            <div className="pt-2 animate-fade-in">
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                Gemini API Key
              </label>
              {editMode ? (
                <input
                  type="password"
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  className="input-field text-sm font-mono"
                  placeholder="AIzaSy..."
                />
              ) : (
                <div className="text-sm font-mono text-[var(--text-primary)] bg-[var(--bg-body)] p-3 rounded-xl border border-[var(--border-default)]">
                  {profile?.gemini_api_key ? '••••••••••••••••••••••••' : 'Not configured'}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Save / Cancel buttons */}
      {editMode && (
        <div className="flex gap-3 justify-end">
          <button onClick={handleCancel} className="btn-secondary flex items-center gap-2">
            <X className="w-4 h-4" /> Cancel
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
            {saving
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
              : <><CheckCircle className="w-4 h-4" /> Save Changes</>
            }
          </button>
        </div>
      )}

      {/* Saved toast */}
      {saved && (
        <div className="fixed bottom-6 right-6 flex items-center gap-2 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 text-[var(--accent-green)] text-sm px-4 py-2.5 rounded-xl shadow-lg animate-fade-in">
          <CheckCircle className="w-4 h-4" /> Profile updated!
        </div>
      )}
    </div>
  );
}
