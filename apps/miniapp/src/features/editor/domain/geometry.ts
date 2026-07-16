import type { EmbroideryArea, PatternDefinition, PatternPlacement, PixelPoint, PixelSize } from './types'

export function canPlacePattern(pattern: PatternDefinition, area: EmbroideryArea): boolean {
  return pattern.width <= area.width && pattern.height <= area.height
}

export function millimetresToPixels(millimetres: number, areaMillimetres: number, areaPixels: number): number {
  return (millimetres / areaMillimetres) * areaPixels
}

export function patternPixelSize(pattern: PatternDefinition, area: EmbroideryArea, areaPixels: PixelSize): PixelSize {
  return { width: millimetresToPixels(pattern.width, area.width, areaPixels.width), height: millimetresToPixels(pattern.height, area.height, areaPixels.height) }
}

export function clampPlacement(placement: PatternPlacement, pattern: PatternDefinition, area: EmbroideryArea): PatternPlacement {
  const minX = pattern.width / area.width / 2
  const minY = pattern.height / area.height / 2
  return { ...placement, centerXRatio: clamp(placement.centerXRatio, minX, 1 - minX), centerYRatio: clamp(placement.centerYRatio, minY, 1 - minY) }
}

export function placementPixelPoint(placement: PatternPlacement, pattern: PatternDefinition, area: EmbroideryArea, areaPixels: PixelSize): PixelPoint {
  const size = patternPixelSize(pattern, area, areaPixels)
  return { x: placement.centerXRatio * areaPixels.width - size.width / 2, y: placement.centerYRatio * areaPixels.height - size.height / 2 }
}

export function pixelPointToPlacement(pixelTopLeft: PixelPoint, placement: PatternPlacement, pattern: PatternDefinition, area: EmbroideryArea, areaPixels: PixelSize): PatternPlacement {
  const size = patternPixelSize(pattern, area, areaPixels)
  return clampPlacement({ ...placement, centerXRatio: (pixelTopLeft.x + size.width / 2) / areaPixels.width, centerYRatio: (pixelTopLeft.y + size.height / 2) / areaPixels.height }, pattern, area)
}

function clamp(value: number, min: number, max: number): number { return Math.min(Math.max(value, min), max) }
