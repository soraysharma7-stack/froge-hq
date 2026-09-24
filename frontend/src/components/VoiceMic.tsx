import { useEffect, useRef, useState } from 'react'

/**
 * Voice command mic — Web Speech API (SpeechRecognition).
 * On-device speech-to-text (English + Hinglish). Shows clear feedback on errors.
 */
export default function VoiceMic({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [supported, setSupported] = useState(false)
  const [listening, setListening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const recRef = useRef<any>(null)

  useEffect(() => {
    const w = window as any
    const SR = w.SpeechRecognition || w.webkitSpeechRecognition
    if (!SR) { setSupported(false); return }
    setSupported(true)
    const rec = new SR()
    rec.lang = 'en-IN' // English-India handles Hinglish better
    rec.interimResults = true // show live transcription
    rec.maxAlternatives = 1
    rec.onresult = (e: any) => {
      const text = e.results?.[0]?.[0]?.transcript
      if (text) onTranscript(text)
    }
    rec.onend = () => setListening(false)
    rec.onerror = (e: any) => {
      setListening(false)
      setError(
        e.error === 'not-allowed' || e.error === 'service-not-allowed'
          ? 'Mic blocked — allow microphone permission'
          : e.error === 'network'
            ? 'Voice service needs internet'
            : `Voice error: ${e.error || 'unknown'}`,
      )
      setTimeout(() => setError(null), 4000)
    }
    recRef.current = rec
    return () => { try { rec.stop() } catch { /* noop */ } }
  }, [onTranscript])

  if (!supported) return null

  const toggle = () => {
    const rec = recRef.current
    if (!rec) return
    setError(null)
    if (listening) { rec.stop(); setListening(false) }
    else {
      try {
        rec.start()
        setListening(true)
      } catch (e: any) {
        setError('Could not start voice — check mic permission')
        setTimeout(() => setError(null), 4000)
      }
    }
  }

  return (
    <div className="relative flex items-center">
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
      {error && (
        <div className="absolute left-10 top-1/2 -translate-y-1/2 whitespace-nowrap rounded border border-red-500/50 bg-black/90 px-2 py-1 font-mono text-[9px] text-red-300">
          {error}
        </div>
      )}
    </div>
  )
}
