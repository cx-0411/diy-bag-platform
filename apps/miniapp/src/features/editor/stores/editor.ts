import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { canPlacePattern, clampPlacement } from '../domain/geometry'
import type { EmbroideryArea, PatternDefinition, PatternPlacement } from '../domain/types'

const embroideryArea: EmbroideryArea = {
  width: 180,
  height: 120,
  relativeX: 0.2,
  relativeY: 0.28,
}

const patternCatalog: PatternDefinition[] = [
  { id: 'flower', name: '小花', width: 42, height: 42, priceCents: 1200, color: '#e16b8c', symbol: '✿' },
  { id: 'heart', name: '爱心', width: 38, height: 34, priceCents: 1000, color: '#d84b4b', symbol: '♥' },
  { id: 'star', name: '星星', width: 36, height: 36, priceCents: 900, color: '#d99b25', symbol: '★' },
]

function placementId(): string {
  return `placement-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export const useEditorStore = defineStore('editor', () => {
  const placements = ref<PatternPlacement[]>([])
  const selectedPlacementId = ref<string | null>(null)

  const selectedPlacement = computed(() => placements.value.find((item) => item.id === selectedPlacementId.value) ?? null)

  function getPattern(patternId: string): PatternDefinition {
    const pattern = patternCatalog.find((item) => item.id === patternId)
    if (!pattern) throw new Error(`Unknown pattern: ${patternId}`)
    return pattern
  }

  function addPattern(patternId: string): void {
    const pattern = getPattern(patternId)
    if (!canPlacePattern(pattern, embroideryArea)) return

    const placement = clampPlacement(
      { id: placementId(), patternId, xRatio: 0.5 - pattern.width / embroideryArea.width / 2, yRatio: 0.5 - pattern.height / embroideryArea.height / 2 },
      pattern,
      embroideryArea,
    )
    placements.value.push(placement)
    selectedPlacementId.value = placement.id
  }

  function updatePlacement(nextPlacement: PatternPlacement): void {
    const pattern = getPattern(nextPlacement.patternId)
    placements.value = placements.value.map((item) => (item.id === nextPlacement.id ? clampPlacement(nextPlacement, pattern, embroideryArea) : item))
  }

  function selectPlacement(id: string): void {
    selectedPlacementId.value = id
  }

  function deleteSelected(): void {
    if (!selectedPlacementId.value) return
    placements.value = placements.value.filter((item) => item.id !== selectedPlacementId.value)
    selectedPlacementId.value = null
  }

  function replaceSelected(patternId: string): void {
    if (!selectedPlacement.value) {
      addPattern(patternId)
      return
    }
    const pattern = getPattern(patternId)
    if (!canPlacePattern(pattern, embroideryArea)) return
    updatePlacement({ ...selectedPlacement.value, patternId })
  }

  return {
    embroideryArea,
    patternCatalog,
    placements,
    selectedPlacementId,
    selectedPlacement,
    getPattern,
    addPattern,
    updatePlacement,
    selectPlacement,
    deleteSelected,
    replaceSelected,
  }
})

