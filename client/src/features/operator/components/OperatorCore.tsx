"use client";

import { useEffect, useRef } from "react";

export default function OperatorCore({ analyser }: { analyser: AnalyserNode | null }) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const element = canvas.current;
    const context = element?.getContext("2d");
    if (!element || !context) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const samples = new Uint8Array(256);
    const frequencies = new Uint8Array(128);
    let frame = 0;
    let lastFrame = 0;
    let level = 0;

    function draw(time: number) {
      if (!element || !context) return;
      frame = requestAnimationFrame(draw);
      if (document.hidden || time - lastFrame < 32) return;
      lastFrame = time;
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      const size = element.clientWidth;
      if (element.width !== Math.round(size * ratio)) {
        element.width = Math.round(size * ratio);
        element.height = element.width;
      }
      context.setTransform(element.width / 400, 0, 0, element.height / 400, 0, 0);
      context.clearRect(0, 0, 400, 400);
      let energy = 0;
      if (analyser) {
        analyser.getByteTimeDomainData(samples);
        analyser.getByteFrequencyData(frequencies);
        for (const sample of samples) energy += ((sample - 128) / 128) ** 2;
        energy = Math.min(1, Math.sqrt(energy / samples.length) * 4);
      }
      level += (energy - level) * 0.22;
      let phase = time / 4500;
      let amplitude = level;
      if (motion.matches) { phase = 0; amplitude = 0; }

      context.translate(200, 200);
      // Quiet organic drift is distinct from the larger, measured audio response.
      for (let layer = 0; layer < 6; layer += 1) {
        const base = 145 + layer * 5;
        context.beginPath();
        for (let point = 0; point <= 240; point += 1) {
          const angle = point / 240 * Math.PI * 2;
          const bin = frequencies[point % 100] / 255;
          const ripple = Math.sin(angle * 5 + phase + layer * 0.65) * (3 + amplitude * 13)
            + Math.sin(angle * 8 - phase * 0.7 + layer) * (2 + amplitude * bin * 13);
          const radius = base + ripple;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;
          if (point === 0) context.moveTo(x, y);
          else context.lineTo(x, y);
        }
        context.closePath();
        context.strokeStyle = `rgba(222, 145, 98, ${0.38 + layer * 0.10})`;
        context.lineWidth = 1.1;
        if (layer === 2 || layer === 4) context.setLineDash([1, 5]);
        else context.setLineDash([]);
        context.stroke();
      }
      context.setLineDash([1, 7]);
      context.strokeStyle = "#b47b58";
      for (const radius of [61, 117]) {
        context.beginPath();
        context.arc(0, 0, radius + amplitude * 4, 0, Math.PI * 2);
        context.stroke();
      }
      context.setLineDash([]);
      const coreRadius = 36 + amplitude * 7;
      context.beginPath();
      context.arc(0, 0, coreRadius, 0, Math.PI * 2);
      context.fillStyle = "#211b17";
      context.fill();
      context.strokeStyle = "#df986c";
      context.lineWidth = 1.4;
      context.stroke();
      // Deterministic points give the core depth without a rendered 3D globe.
      for (let point = 0; point < 140; point += 1) {
        const distance = Math.sqrt(point / 140) * (coreRadius - 4);
        const angle = point * 2.39996 + phase * 0.12;
        context.beginPath();
        context.arc(Math.cos(angle) * distance, Math.sin(angle) * distance, 0.65 + (point % 3) * 0.2, 0, Math.PI * 2);
        context.fillStyle = `rgba(233, 159, 111, ${0.3 + (point % 5) * 0.12})`;
        context.fill();
      }
    }
    frame = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frame);
  }, [analyser]);

  return <canvas ref={canvas} className="operator-core" role="img" aria-label="Mula's layered core. Its rings respond to the AI voice." />;
}
