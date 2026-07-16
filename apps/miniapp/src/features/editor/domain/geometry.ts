import type { EmbroideryArea, PatternDefinition, PatternPlacement, PixelPoint, PixelSize } from './types'

export function canPlacePattern(pattern: PatternDefinition, area: EmbroideryArea): boolean {
  return pattern.width <= area.width && pattern.height <= area.height
}

export function patternPixelSize(pattern: PatternDefinition, area: EmbroideryArea, areaPixels: PixelSize): PixelSize {
  return {
    width: (pattern.width / area.width) * areaPixels.width,
    height: (pattern.height / area.height) * areaPixels.height,
  }
}

export function maxPlacementRatio(pattern: PatternDefinition, area: EmbroideryArea): PixelPoint {
  if (!canPlacePattern(pattern, area)) {
    return { x: 0, y: 0 }
  }

  return {
    x: 1 - pattern.width / area.width,
    y: 1 - pattern.height / area.height,
  }
}

export function clampPlacement(
  placement: PatternPlacement,
  pattern: PatternDefinition,
  area: EmbroideryArea,
): PatternPlacement {
  const max = maxPlacementRatio(pattern, area)

  return {
    ...placement,
    xRatio: clamp(placement.xRatio, 0, max.x),
    yRatio: clamp(placement.yRatio, 0, max.y),
  }
}

export function placementPixelPoint(placement: PatternPlacement, areaPixels: PixelSize): PixelPoint {
  return {
    x: placement.xRatio * areaPixels.width,
    y: placement.yRatio * areaPixels.height,
  }
}

export function pixelPointToPlacement(
  pixelPoint: PixelPoint,
  placement: PatternPlacement,
  pattern: PatternDefinition,
  area: EmbroideryArea,
  areaPixels: PixelSize,
): PatternPlacement {
  return clampPlacement(
    {
      ...placement,
      xRatio: pixelPoint.x / areaPixels.width,
      yRatio: pixelPoint.y / areaPixels.height,
    },
    pattern,
    area,
  )
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

