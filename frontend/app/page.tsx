"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import Markdown from "react-markdown";
import { readChatStream } from "../lib/stream";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  note?: string;
};

const suggestions = [
  {
    title: "Plan a delivery",
    text: "Help me plan a delivery for my shop. What details do you need?",
    icon: "↗",
  },
  {
    title: "Organize my day",
    text: "Help me create a daily operations checklist for a small shop.",
    icon: "☷",
  },
  {
    title: "Explore LARAS",
    text: "What can LARAS help me with right now?",
    icon: "✳",
  },
];

function Mark() {
  return (
    <span className="mark" aria-hidden="true">
      ✳
    </span>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Ready when you are");
  const controller = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const form = useRef<HTMLFormElement>(null);

  useEffect(() => {
    // Avoid restarting a smooth-scroll animation for every streamed token.
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  useEffect(() => {
    return () => controller.current?.abort();
  }, []);

  function updateReply(id: string, text: string, note?: string) {
    setMessages((previous) =>
      previous.map((message) => {
        if (message.id === id) return { ...message, text, note };
        return message;
      }),
    );
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;

    const abort = new AbortController();
    controller.current = abort;
    const replyId = crypto.randomUUID();
    setMessages((previous) => [
      ...previous,
      { id: crypto.randomUUID(), role: "user", text },
      { id: replyId, role: "assistant", text: "" },
    ]);
    setDraft("");
    setError("");
    setBusy(true);
    setStatus("Connecting to Operator…");
    let reply = "";
    let firstToken = true;
    const start = performance.now();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, stream: true }),
        signal: abort.signal,
      });
      if (!response.ok) {
        const failure = await response.json();
        if (typeof failure.detail === "string") throw new Error(failure.detail);
        throw new Error(
          "Please send a message of 1–8,000 characters and try again.",
        );
      }
      if (!response.body)
        throw new Error("Streaming is unavailable in this browser.");

      await readChatStream(response.body, (chunk) => {
        if (chunk.type === "token" && typeof chunk.content === "string") {
          if (firstToken) {
            setStatus(
              `Reply started in ${((performance.now() - start) / 1000).toFixed(1)}s`,
            );
            firstToken = false;
          }
          reply += chunk.content;
          updateReply(replyId, reply);
        }
        if (chunk.type === "done" && chunk.truncated) {
          updateReply(
            replyId,
            reply,
            "Reply reached its length limit. Ask for a shorter answer or a specific section.",
          );
        }
      });
    } catch (failure) {
      if (abort.signal.aborted) {
        updateReply(replyId, reply, "Stopped by you.");
        setStatus("Reply stopped");
      } else {
        let detail =
          "Could not complete the reply. Check your connection and try again.";
        if (failure instanceof Error) detail = failure.message;
        setError(detail);
        updateReply(replyId, reply, "Reply incomplete.");
        // Restore the question so a failed request can be edited and sent again.
        setDraft(text);
        setStatus("Could not complete reply");
      }
    } finally {
      controller.current = null;
      setBusy(false);
      input.current?.focus();
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      form.current?.requestSubmit();
    }
  }

  function newChat() {
    setMessages([]);
    setDraft("");
    setError("");
    setStatus("Ready when you are");
    input.current?.focus();
  }

  let sendLabel = "Send message";
  if (busy) sendLabel = "Sending…";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="LARAS home">
          <Mark />
          <span>
            LARAS<span className="brand-period">.</span>
          </span>
        </a>
        <p className="sidebar-caption">A little order. A lot of possibility.</p>
        <button className="new-chat" onClick={newChat} disabled={busy}>
          <span>＋</span> New chat
        </button>
        <div className="sidebar-section">YOUR WORKSPACE</div>
        <div className="active-nav">
          <span aria-hidden="true">◌</span> Operator{" "}
          <span className="nav-dot" />
        </div>
        <div className="sidebar-bottom">
          <div className="local-icon">⌂</div>
          <div>
            <strong>Your local workspace</strong>
            <span>Simple, focused assistance</span>
          </div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="mobile-brand">LARAS / </span>
            <strong>Operator</strong>
            <span className="header-divider">/</span>
            <span>Your operations assistant</span>
          </div>
          <span className="version-badge">EARLY PREVIEW</span>
          <button className="mobile-new-chat" onClick={newChat} disabled={busy}>
            ＋ New chat
          </button>
        </header>
        <div className="conversation">
          {messages.length === 0 && (
            <section className="welcome">
              <div className="welcome-symbol">
                <Mark />
              </div>
              <div className="eyebrow">LET’S MAKE WORK A LITTLE LIGHTER</div>
              <h1>
                What’s on your
                <br />
                <em>to-do list?</em>
              </h1>
              <p>
                Talk through a delivery, untangle a workflow, or find your next
                step.
                <br className="desktop-break" /> Your Operator is here to help
                you figure it out.
              </p>
              <div className="suggestions">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion.title}
                    className="suggestion"
                    onClick={() => {
                      setDraft(suggestion.text);
                      input.current?.focus();
                    }}
                  >
                    <span className="suggestion-icon" aria-hidden="true">
                      {suggestion.icon}
                    </span>
                    <span>{suggestion.title}</span>
                    <span className="suggestion-arrow" aria-hidden="true">
                      ↗
                    </span>
                  </button>
                ))}
              </div>
            </section>
          )}

          {messages.length > 0 && (
            <section
              className="messages"
              role="log"
              aria-label="Chat messages"
              aria-live="polite"
            >
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="message-label">
                    {message.role === "assistant" && <Mark />}
                    {message.role === "assistant" && <span>Operator</span>}
                    {message.role === "user" && <span>You</span>}
                  </div>
                  {message.text && (
                    <div className="message-text">
                      {message.role === "assistant" && (
                        <Markdown
                          skipHtml
                          components={{
                            a: (props) => (
                              <a
                                {...props}
                                target="_blank"
                                rel="noreferrer noopener"
                              />
                            ),
                          }}
                        >
                          {message.text}
                        </Markdown>
                      )}
                      {message.role === "user" && message.text}
                    </div>
                  )}
                  {!message.text && !message.note && (
                    <div className="waiting">
                      <span />
                      <span />
                      <span />
                      <span className="waiting-label">
                        Preparing your reply
                      </span>
                    </div>
                  )}
                  {message.note && (
                    <p className="message-note">{message.note}</p>
                  )}
                </article>
              ))}
            </section>
          )}
          <div ref={bottom} />
        </div>

        <div className="composer-wrap">
          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}
          <form ref={form} className="composer" onSubmit={sendMessage}>
            <label htmlFor="message" className="sr-only">
              Message Operator
            </label>
            <textarea
              ref={input}
              id="message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={8000}
              rows={2}
              placeholder="Tell me what you’re working on…"
              disabled={busy}
            />
            <div className="composer-toolbar">
              <span>
                <span className="small-star">✳</span> Operator AI
              </span>
              {busy && (
                <button
                  type="button"
                  className="stop-button"
                  onClick={() => controller.current?.abort()}
                >
                  ■ Stop
                </button>
              )}
              {!busy && (
                <button
                  type="submit"
                  className="send-button"
                  disabled={!draft.trim()}
                  aria-label={sendLabel}
                >
                  ↑
                </button>
              )}
            </div>
          </form>
          <div className="composer-meta">
            <span className="status" role="status">
              <span />
              {status}
            </span>
            <span>Enter to send · Shift + Enter for a new line</span>
          </div>
          <p className="scope-note">
            Planning and guidance only. No live business data or actions. Each
            message is independent; include the details you need.
          </p>
        </div>
      </main>
    </div>
  );
}
