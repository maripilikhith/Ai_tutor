/**
 * Auth Callback — Handles Supabase OAuth redirect
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { Brain } from "lucide-react";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const handleCallback = async () => {
      const { error } = await supabase.auth.getSession();
      if (error) {
        router.replace("/login?error=callback_failed");
      } else {
        router.replace("/dashboard");
      }
    };
    handleCallback();
  }, [router]);

  return (
    <div className="h-screen flex items-center justify-center bg-[var(--bg-primary)]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--primary)] to-[var(--primary-dark)] flex items-center justify-center animate-pulse-glow">
          <Brain className="w-7 h-7 text-white" />
        </div>
        <p className="text-sm text-[var(--text-muted)]">Completing sign in...</p>
      </div>
    </div>
  );
}
