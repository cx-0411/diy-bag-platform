import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { canPlacePattern, clampPlacement } from '../domain/geometry'
import type { BagDefinition, PatternCategory, PatternDefinition, PatternPlacement } from '../domain/types'

const DRAFT_KEY = 'diy-bag-editor-draft-v1'
export const mockBag: BagDefinition = { id: 'classic-tote', name: '焦糖托特包', imageUrl: '/static/editor/bag-tote.svg', width: 280, height: 220, basePriceCents: 15900, embroideryArea: { width: 180, height: 120, relativeX: 0.2, relativeY: 0.28 } }
export const patternCategories: PatternCategory[] = [{ id: 'floral', name: '花植' }, { id: 'symbol', name: '符号' }, { id: 'animal', name: '动物' }]
export const patternCatalog: PatternDefinition[] = [
  { id: 'flower', categoryId: 'floral', name: '玫瑰花', imageUrl: '/static/editor/pattern-flower.svg', width: 42, height: 42, priceCents: 1200 },
  { id: 'leaf', categoryId: 'floral', name: '绿叶', imageUrl: '/static/editor/pattern-leaf.svg', width: 50, height: 34, priceCents: 1000 },
  { id: 'heart', categoryId: 'symbol', name: '爱心', imageUrl: '/static/editor/pattern-heart.svg', width: 38, height: 34, priceCents: 1000 },
  { id: 'star', categoryId: 'symbol', name: '星星', imageUrl: '/static/editor/pattern-star.svg', width: 36, height: 36, priceCents: 900 },
  { id: 'cat', categoryId: 'animal', name: '小猫', imageUrl: '/static/editor/pattern-cat.svg', width: 46, height: 42, priceCents: 1500 },
  { id: 'cherry', categoryId: 'floral', name: '樱桃', imageUrl: '/static/editor/pattern-cherry.svg', width: 44, height: 40, priceCents: 1300 },
]
function placementId(): string { return `placement-${Date.now()}-${Math.random().toString(16).slice(2)}` }

export const useEditorStore = defineStore('editor', () => {
  const placements = ref<PatternPlacement[]>(readDraft())
  const selectedPlacementId = ref<string | null>(null)
  const activeCategoryId = ref(patternCategories[0].id)
  const selectedPlacement = computed(() => placements.value.find((item) => item.id === selectedPlacementId.value) ?? null)
  const activePatterns = computed(() => patternCatalog.filter((item) => item.categoryId === activeCategoryId.value))
  const patternPriceCents = computed(() => placements.value.reduce((total, item) => total + getPattern(item.patternId).priceCents, 0))
  const totalPriceCents = computed(() => mockBag.basePriceCents + patternPriceCents.value)
  function getPattern(patternId: string): PatternDefinition { const item = patternCatalog.find((pattern) => pattern.id === patternId); if (!item) throw new Error(`Unknown pattern: ${patternId}`); return item }
  function addPattern(patternId: string): void { const pattern = getPattern(patternId); if (!canPlacePattern(pattern, mockBag.embroideryArea)) return; const item = { id: placementId(), patternId, centerXRatio: 0.5, centerYRatio: 0.5 }; placements.value.push(clampPlacement(item, pattern, mockBag.embroideryArea)); selectedPlacementId.value = item.id }
  function updatePlacement(next: PatternPlacement): void { const pattern = getPattern(next.patternId); placements.value = placements.value.map((item) => item.id === next.id ? clampPlacement(next, pattern, mockBag.embroideryArea) : item) }
  function selectPlacement(id: string | null): void { selectedPlacementId.value = id }
  function deleteSelected(): void { placements.value = placements.value.filter((item) => item.id !== selectedPlacementId.value); selectedPlacementId.value = null }
  function replaceSelected(patternId: string): void { if (!selectedPlacement.value) return addPattern(patternId); updatePlacement({ ...selectedPlacement.value, patternId }) }
  function clearDraft(): void { placements.value = []; selectedPlacementId.value = null; uni.removeStorageSync(DRAFT_KEY) }
  watch(placements, (value) => uni.setStorageSync(DRAFT_KEY, value), { deep: true })
  return { bag: mockBag, categories: patternCategories, activeCategoryId, activePatterns, placements, selectedPlacementId, selectedPlacement, patternPriceCents, totalPriceCents, getPattern, addPattern, updatePlacement, selectPlacement, deleteSelected, replaceSelected, clearDraft }
})
function readDraft(): PatternPlacement[] { try { const value = uni.getStorageSync(DRAFT_KEY); return Array.isArray(value) ? value.filter(isPlacement) : [] } catch { return [] } }
function isPlacement(value: unknown): value is PatternPlacement { return Boolean(value && typeof value === 'object' && typeof (value as PatternPlacement).id === 'string' && typeof (value as PatternPlacement).patternId === 'string' && typeof (value as PatternPlacement).centerXRatio === 'number' && typeof (value as PatternPlacement).centerYRatio === 'number') }
