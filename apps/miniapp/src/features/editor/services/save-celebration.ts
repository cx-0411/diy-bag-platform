let preparedContext: AudioContext | null = null

function createContext(): AudioContext | null {
  if (typeof AudioContext === 'undefined') return null
  try { return new AudioContext() } catch { return null }
}

/** Call from the user's Save button gesture so later playback is permitted. */
export function prepareSaveCelebration(): void {
  if (preparedContext) void preparedContext.close()
  preparedContext = createContext()
  if (preparedContext) void preparedContext.resume()
}

export function cancelSaveCelebration(): void {
  if (preparedContext) void preparedContext.close()
  preparedContext = null
}

/** Play only after the rendered preview image has completed loading. */
export function playSaveCelebration(): void {
  try {
    const context = preparedContext ?? createContext()
    preparedContext = null
    if (!context) return
    const now = context.currentTime
    const master = context.createGain()
    master.gain.setValueAtTime(.0001, now)
    master.gain.exponentialRampToValueAtTime(.15, now + .025)
    master.gain.exponentialRampToValueAtTime(.0001, now + .9)
    master.connect(context.destination)

    const sparkleFrequencies = [440, 660, 880, 1047, 1319, 1568, 1760]
    sparkleFrequencies.forEach((frequency, index) => {
      const oscillator = context.createOscillator()
      const gain = context.createGain()
      const start = now + .05 + index * .055
      oscillator.type = index % 2 ? 'sine' : 'triangle'
      oscillator.frequency.setValueAtTime(frequency, start)
      oscillator.frequency.exponentialRampToValueAtTime(frequency * 1.55, start + .16)
      gain.gain.setValueAtTime(.0001, start)
      gain.gain.exponentialRampToValueAtTime(.075, start + .012)
      gain.gain.exponentialRampToValueAtTime(.0001, start + .22)
      oscillator.connect(gain); gain.connect(master)
      oscillator.start(start); oscillator.stop(start + .24)
    })

    window.setTimeout(() => { void context.close() }, 1100)
  } catch {
    // Some mini-program runtimes restrict web audio. Saving must still succeed.
  }
}
