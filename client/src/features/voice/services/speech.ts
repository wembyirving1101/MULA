export type VoiceState = "idle" | "preparing" | "speaking";

export function speechChunks(markdown: string): string[] {
  // Speak prose, not fenced code, HTML, markdown syntax or raw destinations.
  const text = markdown
    .replace(/```[\s\S]*?(?:```|$)/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/<[^>]*>/g, " ")
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/^[\s]*[>#*\-]+\s*/gm, "")
    .replace(/[*_`~|]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  const chunks: string[] = [];
  let remaining = text;
  while (remaining.length > 0) {
    let end = Math.min(1000, remaining.length);
    if (end < remaining.length) {
      const sentence = remaining.slice(0, end).search(/[.!?]\s+[^.!?]*$/);
      if (sentence >= 200) end = sentence + 1;
      else {
        const space = remaining.lastIndexOf(" ", end);
        if (space > 0) end = space;
      }
      // Do not cut a surrogate pair in the rare case of a long unbroken token.
      const code = remaining.charCodeAt(end - 1);
      if (code >= 0xd800 && code <= 0xdbff) end -= 1;
    }
    chunks.push(remaining.slice(0, end).trim());
    remaining = remaining.slice(end).trim();
  }
  return chunks;
}

export class SpeechPlayer {
  private context: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private source: AudioBufferSourceNode | null = null;
  private request: AbortController | null = null;
  private generation = 0;
  private finishPlayback: (() => void) | null = null;
  private onState: (state: VoiceState) => void;
  private onAnalyser: (analyser: AnalyserNode) => void;

  constructor(onState: (state: VoiceState) => void, onAnalyser: (analyser: AnalyserNode) => void) {
    this.onState = onState;
    this.onAnalyser = onAnalyser;
  }

  async unlock() {
    if (!this.context) {
      if (typeof AudioContext === "undefined") throw new Error("AI voice is not supported in this browser. Chat still works.");
      this.context = new AudioContext();
      this.analyser = this.context.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;
      this.analyser.connect(this.context.destination);
      this.onAnalyser(this.analyser);
    }
    await this.context.resume();
    if (this.context.state !== "running") throw new Error("Select Play reply to allow audio in your browser.");
  }

  stop() {
    // Invalidates synthesis and decoding too, preventing late audio after mute.
    this.generation += 1;
    this.request?.abort();
    this.request = null;
    if (this.source) {
      this.source.onended = null;
      this.source.stop();
      this.source.disconnect();
      this.source = null;
    }
    this.finishPlayback?.();
    this.finishPlayback = null;
    this.onState("idle");
  }

  async speak(text: string) {
    this.stop();
    const generation = this.generation;
    const chunks = speechChunks(text);
    if (!chunks.length) return;
    try {
      await this.unlock();
      if (generation !== this.generation) return;
      const context = this.context!;
      for (const chunk of chunks) {
        if (generation !== this.generation) return;
        this.onState("preparing");
        const request = new AbortController();
        this.request = request;
        const timeout = setTimeout(() => request.abort(), 35000);
        let bytes: ArrayBuffer;
        try {
          const response = await fetch("/api/speech", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: chunk }), signal: request.signal,
          });
          if (!response.ok) {
            const failure = await response.json();
            if (typeof failure.detail === "string") throw new Error(failure.detail);
            throw new Error("Could not create AI voice. Chat still works.");
          }
          bytes = await response.arrayBuffer();
        } finally {
          clearTimeout(timeout);
        }
        if (generation !== this.generation) return;
        const buffer = await context.decodeAudioData(bytes);
        if (generation !== this.generation) return;
        const source = context.createBufferSource();
        source.buffer = buffer;
        source.connect(this.analyser!);
        this.source = source;
        await new Promise<void>((resolve) => {
          this.finishPlayback = resolve;
          source.onended = () => {
            source.disconnect();
            this.source = null;
            this.finishPlayback = null;
            resolve();
          };
          source.start();
          this.onState("speaking");
        });
      }
    } catch (failure) {
      if (generation !== this.generation) return;
      this.stop();
      if (failure instanceof Error && failure.name === "AbortError") {
        throw new Error("Voice generation timed out. You can still read the reply.");
      }
      throw failure;
    } finally {
      if (generation === this.generation) {
        this.request = null;
        this.onState("idle");
      }
    }
  }

  async dispose() {
    this.stop();
    if (this.context) await this.context.close();
    this.context = null;
  }
}
