/**
 * AI Study Companion — API Client
 *
 * Centralized HTTP client for calling the FastAPI backend.
 * Automatically attaches the Supabase JWT token to every request.
 *
 * Usage:
 *   const data = await api.get("/spaces");
 *   const space = await api.post("/spaces", { name: "Physics" });
 */

import { supabase } from "./supabase";

const RAW_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const cleanUrl = RAW_API_URL.replace(/\/+$/, "");
const API_BASE = cleanUrl.endsWith("/api") ? cleanUrl : `${cleanUrl}/api`;

/**
 * Get the current user's JWT token for API authorization.
 */
async function getAuthToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

/**
 * Build headers with authorization token.
 */
async function buildHeaders(
  extra?: Record<string, string>
): Promise<Record<string, string>> {
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extra,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Generic API error class.
 */
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
    this.name = "ApiError";
  }
}

/**
 * Parse the API response, throw ApiError on non-2xx status.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "An error occurred";
    try {
      const errorBody = await response.json();
      detail = errorBody.detail || JSON.stringify(errorBody);
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/**
 * The API client object — all backend calls go through here.
 */
export const api = {
  /**
   * GET request to the backend.
   */
  async get<T = unknown>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${API_BASE}${path}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.set(key, value);
      });
    }
    const headers = await buildHeaders();
    const response = await fetch(url.toString(), { headers });
    return handleResponse<T>(response);
  },

  /**
   * POST request to the backend.
   */
  async post<T = unknown>(path: string, body?: unknown): Promise<T> {
    const headers = await buildHeaders();
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  /**
   * PUT request to the backend.
   */
  async put<T = unknown>(path: string, body?: unknown): Promise<T> {
    const headers = await buildHeaders();
    const response = await fetch(`${API_BASE}${path}`, {
      method: "PUT",
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  /**
   * DELETE request to the backend.
   */
  async delete<T = unknown>(path: string): Promise<T> {
    const headers = await buildHeaders();
    const response = await fetch(`${API_BASE}${path}`, {
      method: "DELETE",
      headers,
    });
    return handleResponse<T>(response);
  },

  /**
   * Upload a file (multipart/form-data).
   */
  async upload<T = unknown>(path: string, file: File): Promise<T> {
    const token = await getAuthToken();
    const formData = new FormData();
    formData.append("file", file);

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    // Don't set Content-Type — browser will set it with boundary

    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers,
      body: formData,
    });
    return handleResponse<T>(response);
  },

  /**
   * SSE streaming request (for AI Tutor).
   * Returns an async generator yielding parsed SSE events.
   */
  async *stream(
    path: string,
    body: unknown
  ): AsyncGenerator<{ type: string; [key: string]: unknown }> {
    const headers = await buildHeaders();
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new ApiError(response.status, "Stream request failed");
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data;
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  },
};
