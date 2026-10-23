import assert from "node:assert/strict";
import test from "node:test";
import { readChatStream } from "../lib/stream.ts";

function body(chunks) {
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk);
      controller.close();
    },
  });
}

test("handles JSON and multibyte text split across network chunks", async () => {
  const encoded = new TextEncoder().encode(
    '{"type":"token","content":"Halo 👋"}\n{"type":"done","truncated":false}\n',
  );
  const chunks = Array.from(encoded, (byte) => new Uint8Array([byte]));
  const events = [];
  await readChatStream(body(chunks), (event) => events.push(event));
  assert.equal(events[0].content, "Halo 👋");
  assert.equal(events[1].type, "done");
});

test("reports interrupted streams instead of silently accepting a partial reply", async () => {
  await assert.rejects(
    readChatStream(
      body([new TextEncoder().encode('{"type":"token","content":"Hello"}\n')]),
      () => {},
    ),
    /before the reply finished/,
  );
});

test("reports upstream errors and cancels the reader", async () => {
  let cancelled = false;
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(
        new TextEncoder().encode('{"type":"error","detail":"Model missing"}\n'),
      );
    },
    cancel() {
      cancelled = true;
    },
  });
  await assert.rejects(
    readChatStream(stream, () => {}),
    /Model missing/,
  );
  assert.equal(cancelled, true);
});

test("allows a final event without a trailing newline", async () => {
  const events = [];
  await readChatStream(
    body([new TextEncoder().encode('{"type":"done"}')]),
    (event) => events.push(event),
  );
  assert.equal(events.length, 1);
});
