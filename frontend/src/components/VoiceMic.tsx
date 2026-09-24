import { useEffect, useRef, useState } from 'react'

/**
 * Voice command mic — Web Speech API (SpeechRecognition).
 * On-device speech-to-text (English + Hinglish). Hides if unsupported.
 */
export default function VoiceMic({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [supported, setSupported] = useState(false)
  const [listening, setListening] = useState(false)
  const recRef = useRef<any>(null)

  useEffect(() => {
    const w = window as any
    const SR = w.SpeechRecognition || w.webkitSpeechRecognition
    if (!SR) return
    setSupported(true)
    const rec = new SR()
    rec.lang = 'en-IN' // English-India handles Hinglish better
    rec.interimResults = false
    rec.maxAlternatives = 1
    rec.onresult = (e: any) => {
      const text = e.results?.[0]?.[0]?.transcript
      if (text) onTranscript(text)
    }
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
    recRef.current = rec
    return () => { try { rec.stop() } catch { /* noop */ } }
  }, [onTranscript])

  if (!supported) return null

  const toggle = () => {
    const rec = recRef.current
    if (!rec) return
    if (listening) { rec.stop(); setListening(false) }
    else { try { rec.start(); setListening(true) } catch { setListening(false) } }
  }

  return (
    <button
      onClick={toggle}
      title={listening ? 'Listening… tap to stop' : 'Voice command (English / Hinglish)'}
      aria-label={listening ? 'Stop listening' : 'Start voice command'}
      className={`relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border transition-all ${
        listening
          ? 'border-red-500 text-red-400 shadow-[0_0_16px_rgba(239,68,68,0.5)] animate-pulse'
          : 'border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10'
      }`}
    >
      {listening && <span className="absolute inline-flex h-full w-full animate-ping rounded-lg bg-red-500/30" />}
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
        {listening ? (
          <><rect x="9" y="9" width="6" height="6" rx="1" /><path d="M12 2a4 4 0 0 0-4 4v6a4 4 0 0 0 8 0V6a4 4 0 0 0-4-4z" opacity="0" /></>
        ) : (
          <><path d="M12 2a4 4 0 0 0-4 4v6a4 4 0 0 0 8 0V6a4 4 0 0 0-4-4z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="22" /></>
        )}
      </svg>
    </button>
  )
}
