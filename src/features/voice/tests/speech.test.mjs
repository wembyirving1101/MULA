import assert from "node:assert/strict";
import test from "node:test";
import { SpeechPlayer, speechChunks } from "../services/speech.ts";

test("speech reads prose and strips fenced code, markup and raw URLs", () => {
  const result = speechChunks("# Hello **Rafa**\nVisit [the shop](https://shop.test).\n```js\nsecret()\n```\n![logo](img.png) https://raw.test");
  assert.deepEqual(result, ["Hello Rafa Visit the shop."]);
  assert.deepEqual(speechChunks("```js\nunfinished code"), []);
});

test("long replies are bounded without losing words or splitting emoji", () => {
  const text = "Here is another sentence. ".repeat(200) + "😀".repeat(600);
  const chunks = speechChunks(text);
  assert.ok(chunks.length > 1);
  assert.ok(chunks.every((chunk) => chunk.length <= 1000 && chunk.isWellFormed()));
  assert.equal(chunks.join("").replaceAll(" ", ""), text.replaceAll(" ", ""));
});

function mockAudio(context) {
  const sources = [];
  let finishDecode;
  let holdDecode = false;
  class FakeAudioContext {
    state = "running";
    destination = {};
    async resume() {}
    async close() {}
    createAnalyser() { return { connect() {} }; }
    async decodeAudioData() {
      if (holdDecode) return new Promise((resolve) => { finishDecode = resolve; });
      return {};
    }
    createBufferSource() {
      const source = { started: false, stopped: false, onended: null, connect() {}, disconnect() {}, start() { this.started = true; }, stop() { this.stopped = true; } };
      sources.push(source);
      return source;
    }
  }
  const previous = globalThis.AudioContext;
  globalThis.AudioContext = FakeAudioContext;
  context.after(() => { globalThis.AudioContext = previous; });
  return { sources, hold() { holdDecode = true; }, decode() { finishDecode({}); } };
}

const tick = () => new Promise((resolve) => setImmediate(resolve));

test("mute stops active audio immediately and cancels the rest of the reply", async (context) => {
  const audio = mockAudio(context);
  const fetch = context.mock.method(globalThis, "fetch", async () => new Response(new Uint8Array([1])));
  const states = [];
  const player = new SpeechPlayer((state) => states.push(state), () => {});
  const speaking = player.speak("A long sentence. ".repeat(100));
  await tick();
  assert.equal(audio.sources[0].started, true);
  player.stop();
  await speaking;
  assert.equal(audio.sources[0].stopped, true);
  assert.equal(fetch.mock.callCount(), 1);
  assert.equal(states.at(-1), "idle");
  await player.dispose();
});

test("late synthesis response cannot play after mute even if fetch ignores abort", async (context) => {
  const audio = mockAudio(context);
  let finish;
  let signal;
  context.mock.method(globalThis, "fetch", async (_url, options) => {
    signal = options.signal;
    return new Promise((resolve) => { finish = resolve; });
  });
  const player = new SpeechPlayer(() => {}, () => {});
  const speaking = player.speak("Hello");
  await tick();
  player.stop();
  assert.equal(signal.aborted, true);
  finish(new Response(new Uint8Array([1])));
  await speaking;
  assert.equal(audio.sources.length, 0);
  await player.dispose();
});

test("mute during audio decoding prevents a late source from starting", async (context) => {
  const audio = mockAudio(context);
  audio.hold();
  context.mock.method(globalThis, "fetch", async () => new Response(new Uint8Array([1])));
  const player = new SpeechPlayer(() => {}, () => {});
  const speaking = player.speak("Hello");
  await tick();
  player.stop();
  audio.decode();
  await speaking;
  assert.equal(audio.sources.length, 0);
  await player.dispose();
});

test("voice provider errors leave playback idle and surface a useful error", async (context) => {
  mockAudio(context);
  context.mock.method(globalThis, "fetch", async () => Response.json({ detail: "Voice is busy" }, { status: 429 }));
  const states = [];
  const player = new SpeechPlayer((state) => states.push(state), () => {});
  await assert.rejects(player.speak("Hello"), /Voice is busy/);
  assert.equal(states.at(-1), "idle");
  await player.dispose();
});
