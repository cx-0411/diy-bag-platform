/**
 * A small synthesized firework burst. Keeping it generated in code avoids a
 * heavyweight audio dependency and means the H5 preview is ready immediately.
 */
export function playSaveCelebration(): void {
  if (typeof AudioContext === 'undefined') return

  try {
    const context = new AudioContext()
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
