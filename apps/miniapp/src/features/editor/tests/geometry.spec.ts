import { describe, expect, it } from 'vitest'

import { canPlacePattern, clampPlacement, patternPixelSize, pixelPointToPlacement } from '../domain/geometry'
import type { EmbroideryArea, PatternDefinition, PatternPlacement } from '../domain/types'

const area: EmbroideryArea = { width: 180, height: 120, relativeX: 0.2, relativeY: 0.28 }
const flower: PatternDefinition = { id: 'flower', name: '小花', width: 42, height: 42, priceCents: 1200, color: '#e16b8c', symbol: '✿' }
const placement: PatternPlacement = { id: 'p1', patternId: 'flower', xRatio: 0, yRatio: 0 }

describe('DIY editor geometry', () => {
  it('converts fixed millimetre dimensions to current screen pixels', () => {
    expect(patternPixelSize(flower, area, { width: 360, height: 240 })).toEqual({ width: 84, height: 84 })
  })

  it('does not allow a pattern that exceeds the embroidery area', () => {
    expect(canPlacePattern({ ...flower, width: 181 }, area)).toBe(false)
  })

  it('clamps normalized top-left coordinates so the whole pattern remains inside', () => {
    expect(clampPlacement({ ...placement, xRatio: 1, yRatio: 1 }, flower, area)).toEqual({
      ...placement,
      xRatio: 1 - 42 / 180,
      yRatio: 1 - 42 / 120,
    })
  })

  it('converts dragged pixels to normalized storage coordinates and clamps them', () => {
    expect(pixelPointToPlacement({ x: 500, y: -30 }, placement, flower, area, { width: 360, height: 240 })).toEqual({
      ...placement,
      xRatio: 1 - 42 / 180,
      yRatio: 0,
    })
  })
})

