import { advanceRotation, normalizeRotation, pointerAngleDegrees } from './rotation'
import { describe, expect, it } from 'vitest'

describe('rotation helpers', () => {
  it('converts a pointer into an angle around the selected pattern', () => {
    expect(pointerAngleDegrees(10, 0, 0, 0)).toBe(0)
    expect(pointerAngleDegrees(0, 10, 0, 0)).toBe(90)
  })

  it('keeps rotating smoothly when the pointer crosses the -180/180 boundary', () => {
    expect(advanceRotation({ lastPointerAngle: 170, rotationDegrees: 10 }, -170)).toEqual({ lastPointerAngle: -170, rotationDegrees: 30 })
  })

  it('normalizes stored angles', () => {
    expect(normalizeRotation(-15)).toBe(345)
    expect(normalizeRotation(375)).toBe(15)
  })
})
