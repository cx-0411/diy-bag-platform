export interface SizeMm {
  width: number
  height: number
}

export interface EmbroideryArea extends SizeMm {
  /** Relative to the bag image, used by later API-driven rendering. */
  relativeX: number
  relativeY: number
}

export interface PatternDefinition extends SizeMm {
  id: string
  name: string
  priceCents: number
  color: string
  symbol: string
}

/** Top-left coordinates are ratios relative to the embroidery area. */
export interface PatternPlacement {
  id: string
  patternId: string
  xRatio: number
  yRatio: number
}

export interface PixelSize {
  width: number
  height: number
}

export interface PixelPoint {
  x: number
  y: number
}

