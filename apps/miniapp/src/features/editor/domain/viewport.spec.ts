import { describe, expect, it } from 'vitest'
import { MAX_VIEWPORT_ZOOM, MIN_VIEWPORT_ZOOM, nextViewportZoom } from './viewport'

describe('canvas viewport zoom', () => {
  it('keeps visual zoom inside its dedicated safe range', () => {
    expect(nextViewportZoom(MIN_VIEWPORT_ZOOM, -.1)).toBe(MIN_VIEWPORT_ZOOM)
    expect(nextViewportZoom(MAX_VIEWPORT_ZOOM, .1)).toBe(MAX_VIEWPORT_ZOOM)
    expect(nextViewportZoom(1, .1)).toBe(1.1)
  })
})
