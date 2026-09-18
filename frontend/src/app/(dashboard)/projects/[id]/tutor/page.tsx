/**
 * AI Tutor Page — Streaming chat with citations
 */

"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { formatDate, cn } from "@/lib/utils";
import { Send, Loader2, Bot, User, FileText, Sparkles, Plus, MessageSquare, Mic, MicOff } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import type { Conversation, Citation } from "@/lib/types";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
}

export default function TutorPage() {
  const { id } = useParams();
  const projectId = id as string;
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load conversations
  const loadConversations = () => {
    api.get<{ items: Conversation[] }>(`/projects/${projectId}/conversations`)
      .then((data) => setConversations(data.items))
      .catch(() => {});
  };

  useEffect(() => {
    loadConversations();
  }, [projectId]);

  // Load messages when conversation changes
  useEffect(() => {
    if (!activeConvId) return;
    // Don't fetch if we're actively streaming a new conversation, 
    // as it will overwrite the optimistic AI placeholder.
    if (streaming) return;

    api.get<{ messages: ChatMessage[] }>(`/conversations/${activeConvId}`)
      .then((data) => setMessages(data.messages))
      .catch(() => {});
  }, [activeConvId]); // Intentionally omitting 'streaming' so it only fires on activeConvId change

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const message = text || input.trim();
    if (!message || streaming) return;

    setInput("");
    setSuggestions([]);
    setStreaming(true);

    // Optimistic UI: add user message
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: message,
      citations: [],
    };
    setMessages((prev) => [...prev, userMsg]);

    // Add placeholder for assistant
    const assistantMsg: ChatMessage = {
      id: `temp-ai-${Date.now()}`,
      role: "assistant",
      content: "",
      citations: [],
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const stream = api.stream(`/projects/${projectId}/tutor/chat`, {
        message,
        conversation_id: activeConvId,
      });

      for await (const event of stream) {
        if (event.type === "conversation_id") {
          const convId = event.conversation_id as string;
          setActiveConvId(convId);
          loadConversations();
        } else if (event.type === "content") {
          const content = event.content as string;
          setMessages((prev) => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            const last = updated[lastIndex];
            if (last?.role === "assistant") {
              updated[lastIndex] = { ...last, content: last.content + content };
            }
            return updated;
          });
        } else if (event.type === "citations") {
          const citations = event.citations as Citation[];
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              last.citations = citations;
            }
            return [...updated];
          });
        } else if (event.type === "suggestions") {
          setSuggestions(event.suggestions as string[]);
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant" && !last.content) {
          last.content = "Sorry, something went wrong. Please try again.";
        }
        return [...updated];
      });
    } finally {
      setStreaming(false);
    }
  };

  const startNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
    setSuggestions([]);
  };

  const startListening = () => {
    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support voice input. Try using Google Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => setIsListening(true);
    
    recognition.onresult = (event: any) => {
      const current = event.resultIndex;
      const transcript = event.results[current][0].transcript;
      setInput((prev) => {
        // If it's the final result, maybe we want to append, but for simplicity we'll just set it
        // Actually, interim results overwrite, so we need to be careful if we have existing text.
        // Easiest is to just replace the input while listening.
        return transcript;
      });
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    
    recognition.start();
  };

  return (
    <div className="flex h-[calc(100vh-180px)] md:h-[calc(100vh-140px)] gap-4">
      {/* History Sidebar */}
      <div className="hidden md:flex w-64 flex-col gap-4">
        <button onClick={startNewConversation} disabled={streaming} className="btn-primary text-sm flex items-center gap-2 justify-center disabled:opacity-50 disabled:cursor-not-allowed">
          <Plus className="w-4 h-4" /> New Chat
        </button>
        <div className="flex-1 overflow-y-auto space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setActiveConvId(conv.id)}
              disabled={streaming}
              className={`w-full text-left p-2.5 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                activeConvId === conv.id ? "bg-[var(--primary)]/10 text-[var(--primary-light)]" : "text-[var(--text-muted)] hover:bg-[var(--bg-card)]"
              }`}
            >
              <p className="truncate font-medium">{conv.title}</p>
              <p className="text-[10px] opacity-60">{formatDate(conv.updated_at)}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col gradient-card overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--primary)] to-[var(--accent-cyan)] flex items-center justify-center mb-4 animate-pulse-glow">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">AI Tutor</h3>
              <p className="text-sm text-[var(--text-muted)] max-w-sm">
                Ask me anything about your learning materials. I&apos;ll reference your documents and track your understanding.
              </p>
              <div className="flex gap-2 mt-6 flex-wrap justify-center">
                {["Explain the key concepts", "Quiz me on this topic", "Summarize the materials"].map((q) => (
                  <button key={q} onClick={() => sendMessage(q)} className="btn-secondary text-xs py-1.5 px-3">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-cyan)] flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-[var(--bg-elevated)] border border-[var(--border-default)]"
                    : "bg-[var(--bg-input)] border border-transparent"
                }`}>
                  <div className="prose-ai text-sm max-w-none">
                    {msg.content ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    )}
                  </div>
                  {msg.citations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-white/10 flex gap-1.5 flex-wrap">
                      {msg.citations.map((c, i) => (
                        <span key={i} className="inline-flex items-center gap-1 text-[10px] bg-white/10 rounded-full px-2 py-0.5">
                          <FileText className="w-2.5 h-2.5" />
                          {c.file_name}{c.page_number ? ` p.${c.page_number}` : ""}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-lg bg-[var(--bg-elevated)] flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-[var(--text-muted)]" />
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && !streaming && (
          <div className="px-4 pb-2 flex gap-2 flex-wrap">
            {suggestions.map((s) => (
              <button key={s} onClick={() => sendMessage(s)} className="text-xs bg-[var(--primary)]/10 text-[var(--primary-light)] px-3 py-1.5 rounded-full hover:bg-[var(--primary)]/20 transition-colors">
                <Sparkles className="w-3 h-3 inline mr-1" />{s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-[var(--border-default)]">
          <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="flex gap-2 relative">
            <div className="relative flex-1">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="input-field w-full pr-10"
                placeholder={isListening ? "Listening..." : "Ask anything about your materials..."}
                disabled={streaming}
              />
              <button
                type="button"
                onClick={startListening}
                disabled={streaming || isListening}
                className={cn(
                  "absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md transition-colors",
                  isListening 
                    ? "text-[var(--accent-red)] animate-pulse" 
                    : "text-[var(--text-muted)] hover:text-[var(--primary-light)] hover:bg-[var(--bg-elevated)]"
                )}
                title="Voice input"
              >
                {isListening ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
              </button>
            </div>
            <button type="submit" disabled={!input.trim() || streaming} className="btn-primary px-4">
              {streaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
