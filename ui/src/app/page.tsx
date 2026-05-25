"use client";

import { useState, useRef, useEffect, useCallback, FormEvent, KeyboardEvent } from "react";
import { checkHealth, sendMessage } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
}

const EXAMPLE_PROMPTS = [
  "I spent ₹500 on groceries today",
  "What did I spend last week?",
  "Set a food budget of ₹5000/month",
  "Show my spending by category",
];

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function generateId(): string {
  return Math.random().toString(36).slice(2, 10);
}

export default function ChatPage() {
  const [threadId, setThreadId] = useState("user-1");
  const [threadInputVal, setThreadInputVal] = useState("user-1");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Health check on mount + every 30s
  const runHealthCheck = useCallback(async () => {
    setBackendStatus("checking");
    const ok = await checkHealth();
    setBackendStatus(ok ? "online" : "offline");
  }, []);

  useEffect(() => {
    runHealthCheck();
    const interval = setInterval(runHealthCheck, 30000);
    return () => clearInterval(interval);
  }, [runHealthCheck]);

  const applyThreadId = () => {
    const trimmed = threadInputVal.trim();
    if (!trimmed) return;
    setThreadId(trimmed);
    setMessages([]);
    setError(null);
  };

  const handleSend = async (messageText?: string) => {
    const text = (messageText ?? input).trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const response = await sendMessage({ message: text, thread_id: threadId });
      const aiMsg: Message = {
        id: generateId(),
        role: "ai",
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFormSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSend();
  };

  const statusLabel =
    backendStatus === "checking" ? "Connecting…" :
    backendStatus === "online" ? "Backend online" : "Backend offline";

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon">💰</div>
            <div>
              <div className="logo-title">Finance AI</div>
              <div className="logo-subtitle">Agentic Expense Tracker</div>
            </div>
          </div>
        </div>

        <div className="sidebar-content">

          {/* Session / Thread ID */}
          <div>
            <div className="section-label">Session</div>
            <div className="thread-input-group">
              <input
                id="thread-id-input"
                className="thread-input"
                value={threadInputVal}
                onChange={(e) => setThreadInputVal(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && applyThreadId()}
                placeholder="Enter user / session ID"
                spellCheck={false}
              />
              <button
                onClick={applyThreadId}
                style={{
                  background: "var(--accent)",
                  color: "white",
                  border: "none",
                  borderRadius: "var(--radius-md)",
                  padding: "7px 12px",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  transition: "background 0.15s",
                }}
                onMouseOver={(e) => (e.currentTarget.style.background = "var(--accent-hover)")}
                onMouseOut={(e) => (e.currentTarget.style.background = "var(--accent)")}
              >
                Apply
              </button>
              <div className="thread-hint">
                Changing the session ID switches users and clears this chat view.
              </div>
              <div className="thread-badge">
                <span>🔑</span> {threadId}
              </div>
            </div>
          </div>

          {/* Backend Status */}
          <div>
            <div className="section-label">Backend</div>
            <div className="status-row">
              <div className={`status-dot ${backendStatus === "checking" ? "" : backendStatus}`} />
              <span className="status-text">{statusLabel}</span>
            </div>
            <div style={{ marginTop: 6, fontSize: 11, color: "var(--text-muted)" }}>
              GET / · POST /chat
            </div>
          </div>

          {/* Capabilities */}
          <div>
            <div className="section-label">Capabilities</div>
            <div className="cap-list">
              {[
                ["📊", "Track & categorize expenses"],
                ["📅", "Monthly spending summaries"],
                ["🎯", "Budget creation & monitoring"],
                ["🔍", "Semantic expense search"],
                ["🧠", "Persistent memory across sessions"],
                ["💡", "Financial insights & advice"],
              ].map(([icon, label]) => (
                <div className="cap-item" key={label}>
                  <span className="cap-icon">{icon}</span>
                  <span>{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Stack info */}
          <div>
            <div className="section-label">Stack</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
              {["FastAPI", "LangGraph", "PostgreSQL", "Redis", "Qdrant", "Groq"].map((t) => (
                <span
                  key={t}
                  style={{
                    fontSize: 10,
                    padding: "3px 8px",
                    background: "var(--bg-tertiary)",
                    border: "1px solid var(--border)",
                    borderRadius: 20,
                    color: "var(--text-muted)",
                    fontWeight: 500,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main chat area ── */}
      <div className="chat-area">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-title">Chat</div>
          <div className="header-thread-tag">
            <span>🔑</span> {threadId}
          </div>
        </header>

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 && !loading ? (
            <div className="empty-state">
              <div className="empty-icon">🤖</div>
              <div className="empty-title">Finance AI Agent</div>
              <div className="empty-desc">
                Ask me anything about your finances. I can track expenses,
                set budgets, and give you insights — all in natural language.
              </div>
              <div className="example-chips">
                {EXAMPLE_PROMPTS.map((p) => (
                  <button
                    key={p}
                    className="chip"
                    onClick={() => handleSend(p)}
                    disabled={loading}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message-row ${msg.role}`}
                >
                  <div className={`avatar ${msg.role}`}>
                    {msg.role === "user" ? "U" : "🤖"}
                  </div>
                  <div className="message-content">
                    <div className={`bubble ${msg.role}`}>{msg.content}</div>
                    <div className="message-time">{formatTime(msg.timestamp)}</div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row ai">
                  <div className="avatar ai">🤖</div>
                  <div className="message-content">
                    <div className="typing-bubble">
                      <div className="typing-dot" />
                      <div className="typing-dot" />
                      <div className="typing-dot" />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Error bar */}
        {error && (
          <div className="error-bar">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Input */}
        <div className="input-area">
          <form onSubmit={handleFormSubmit}>
            <div className="input-wrapper">
              <textarea
                id="chat-input"
                ref={textareaRef}
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message Finance AI…"
                rows={1}
                disabled={loading}
              />
              <button
                id="send-btn"
                type="submit"
                className="send-btn"
                disabled={!input.trim() || loading}
                aria-label="Send message"
              >
                ↑
              </button>
            </div>
          </form>
          <div className="input-footer">
            Press <kbd style={{ background: "var(--bg-tertiary)", padding: "1px 5px", borderRadius: 4, border: "1px solid var(--border)", fontSize: 10 }}>Enter</kbd> to send · <kbd style={{ background: "var(--bg-tertiary)", padding: "1px 5px", borderRadius: 4, border: "1px solid var(--border)", fontSize: 10 }}>Shift+Enter</kbd> for new line
          </div>
        </div>
      </div>
    </div>
  );
}
