"use client";

import { Mic, MicOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";

/**
 * Voice command mic — uses the browser's Web Speech API (SpeechRecognition).
 * Real, on-device speech-to-text; no audio leaves the page except to the
 * browser's speech service. Gracefully hides if unsupported.
 */
export function VoiceMic({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const recRef = useRef<any>(null);

  useEffect(() => {
    const w = window as any;
    const SR = w.SpeechRecognition || w.webkitSpeechRecognition;
    if (!SR) return;
    setSupported(true);
    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e: any) => {
      const text = e.results?.[0]?.[0]?.transcript;
      if (text) onTranscript(text);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    return () => {
      try {
        rec.stop();
      } catch {
        /* noop */
      }
    };
  }, [onTranscript]);

  if (!supported) return null;

  const toggle = () => {
    const rec = recRef.current;
    if (!rec) return;
    if (listening) {
      rec.stop();
      setListening(false);
    } else {
      try {
        rec.start();
        setListening(true);
      } catch {
        setListening(false);
      }
    }
  };

  return (
    <button
      onClick={toggle}
      aria-label={listening ? "Stop listening" : "Start voice command"}
      title={listening ? "Listening… tap to stop" : "Voice command"}
      className={`relative flex h-9 w-9 items-center justify-center rounded-lg border transition-all duration-200 ${
        listening
          ? "border-red-500 text-red-400 shadow-[0_0_16px_rgba(239,68,68,0.5)]"
          : "border-accent-dim text-accent hover:bg-accent/10 hover:shadow-glow-lg"
      }`}
    >
      {listening && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-lg bg-red-500/30" />
      )}
      {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
    </button>
  );
}
