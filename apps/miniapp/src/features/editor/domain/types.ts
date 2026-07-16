export interface SizeMm { width: number; height: number }

export interface EmbroideryArea extends SizeMm {
  relativeX: number
  relativeY: number
}

export interface BagDefinition extends SizeMm {
  id: string
  name: string
  imageUrl: string
  basePriceCents: number
  embroideryArea: EmbroideryArea
}

export interface PatternCategory { id: string; name: string }

export interface PatternDefinition extends SizeMm {
  id: string
  categoryId: string
  name: string
  imageUrl: string
  priceCents: number
}

/** Center coordinates are ratios relative to the embroidery area. */
export interface PatternPlacement {
  id: string
  patternId: string
  centerXRatio: number
  centerYRatio: number
}

export interface PixelSize { width: number; height: number }
export interface PixelPoint { x: number; y: number }
