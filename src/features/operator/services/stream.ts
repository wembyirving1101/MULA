export type ChatEvent = {
  type: "session" | "token" | "done" | "error";
  session_id?: string;
  content?: string;
  detail?: string;
  truncated?: boolean;
};

export async function readChatStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: ChatEvent) => void,
) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let pending = "";
  let finished = false;

  function processLine(line: string) {
    if (!line.trim()) return;
    const event: ChatEvent = JSON.parse(line);
    if (event.type === "error") {
      throw new Error(
        event.detail || "The reply could not be completed. Try again.",
      );
    }
    if (event.type === "done") finished = true;
    onEvent(event);
  }

  try {
    while (!finished) {
      const result = await reader.read();
      if (result.done) break;
      // A network chunk can split a JSON line or even a multibyte character.
      pending += decoder.decode(result.value, { stream: true });
      let newline = pending.indexOf("\n");
      while (newline !== -1) {
        processLine(pending.slice(0, newline));
        pending = pending.slice(newline + 1);
        newline = pending.indexOf("\n");
      }
    }
    pending += decoder.decode();
    if (pending.trim()) processLine(pending);
    if (!finished) {
      throw new Error(
        "The connection ended before the reply finished. Please try again.",
      );
    }
  } finally {
    // Cancel also propagates Stop and interrupted reads through the proxy.
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
