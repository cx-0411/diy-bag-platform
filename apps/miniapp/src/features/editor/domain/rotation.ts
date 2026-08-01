/** Angle helpers for a continuous, pointer-driven rotation interaction. */
export interface RotationSession {
  lastPointerAngle: number
  rotationDegrees: number
}

export function pointerAngleDegrees(pointerX: number, pointerY: number, centerX: number, centerY: number): number {
  return Math.atan2(pointerY - centerY, pointerX - centerX) * 180 / Math.PI
}

export function normalizeRotation(degrees: number): number {
  return ((degrees % 360) + 360) % 360
}

/**
 * Adds only the shortest delta between two pointer samples. This avoids the
 * 180°/-180° discontinuity that makes a rotation handle appear to jump.
 */
export function advanceRotation(session: RotationSession, nextPointerAngle: number): RotationSession {
  let delta = nextPointerAngle - session.lastPointerAngle
  if (delta > 180) delta -= 360
  if (delta < -180) delta += 360
  return { lastPointerAngle: nextPointerAngle, rotationDegrees: normalizeRotation(session.rotationDegrees + delta) }
}
