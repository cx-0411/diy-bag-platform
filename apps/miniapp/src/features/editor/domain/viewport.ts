export const MIN_VIEWPORT_ZOOM = .85
export const MAX_VIEWPORT_ZOOM = 1.35

/** Only changes the visual viewport scale; it never changes pattern dimensions. */
export function nextViewportZoom(current: number, delta: number): number {
  return Math.min(MAX_VIEWPORT_ZOOM, Math.max(MIN_VIEWPORT_ZOOM, Math.round((current + delta) * 100) / 100))
}
