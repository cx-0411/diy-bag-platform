export interface SizeMm { width: number; height: number }

export interface EmbroideryArea extends SizeMm {
  relativeX: number
  relativeY: number
  relativeWidth: number
  relativeHeight: number
}

export interface BagDefinition extends SizeMm {
  id: string
  name: string
  imageUrl: string
  basePriceCents: number
  embroideryArea: EmbroideryArea
}

export interface PatternCategory { id: string; name: string; icon?: string; description?: string }

export interface PatternDefinition extends SizeMm {
  id: string
  categoryId: string
  name: string
  imageUrl: string
  priceCents: number
  patternVersionId?: string
}

/** Center coordinates are ratios relative to the embroidery area. */
export interface PatternPlacement {
  id: string
  patternId: string
  centerXRatio: number
  centerYRatio: number
  /** Rotation is allowed; physical size remains fixed. */
  rotationDegrees: number
  zIndex: number
}

export interface PixelSize { width: number; height: number }
export interface PixelPoint { x: number; y: number }
