import { describe, expect, it } from 'vitest'
import { clampPlacement, millimetresToPixels, placementPixelPoint, pixelPointToPlacement } from '../domain/geometry'
import type { EmbroideryArea, PatternDefinition, PatternPlacement } from '../domain/types'
const area: EmbroideryArea = { width: 180, height: 120, relativeX: .2, relativeY: .28, relativeWidth: .6, relativeHeight: .5 }
const pattern: PatternDefinition = { id: 'p', categoryId: 'c', name: '测试', imageUrl: '', width: 42, height: 42, priceCents: 1200 }
const placement: PatternPlacement = { id: 'a', patternId: 'p', centerXRatio: .5, centerYRatio: .5, rotationDegrees: 0, zIndex: 0 }
describe('DIY editor geometry', () => {
  it('converts millimetres to pixels', () => expect(millimetresToPixels(42, 180, 360)).toBe(84))
  it('converts ratio coordinates to pixels', () => expect(placementPixelPoint(placement, pattern, area, { width: 360, height: 240 })).toEqual({ x: 138, y: 78 }))
  it('converts pixels to normalized center coordinates', () => expect(pixelPointToPlacement({ x: 138, y: 78 }, placement, pattern, area, { width: 360, height: 240 })).toEqual(placement))
  it('clamps a full rectangle inside embroidery boundaries', () => expect(clampPlacement({ ...placement, centerXRatio: 0, centerYRatio: 1 }, pattern, area)).toEqual({ ...placement, centerXRatio: 42 / 180 / 2, centerYRatio: 1 - 42 / 120 / 2 }))
  it('keeps rotated pattern corners inside embroidery boundaries', () => expect(clampPlacement({ ...placement, rotationDegrees: 45, centerXRatio: 0, centerYRatio: 0 }, pattern, area).centerXRatio).toBeGreaterThan(42 / 180 / 2))
})
