import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { canPlacePattern, clampPlacement } from '../domain/geometry'
import type { BagDefinition, PatternCategory, PatternDefinition, PatternPlacement } from '../domain/types'
import { catalogApi, type ApiBag, type ApiDesign } from '../../../services/catalog-api'

const DRAFT_KEY = 'diy-bag-editor-draft-v3'
const CLIENT_KEY = 'diy-bag-client-key'
const SAVED_DRAFTS_KEY = 'diy-bag-saved-designs-v2'
const emptyBag: BagDefinition = {
  id: '', name: '', imageUrl: '', width: 0, height: 0, basePriceCents: 0,
  embroideryArea: { width: 1, height: 1, relativeX: 0, relativeY: 0, relativeWidth: 1, relativeHeight: 1 },
}

interface StoredDesign { id: string; totalPriceCents: number; bagId: string; placements: PatternPlacement[] }
function placementId(): string { return `placement-${Date.now()}-${Math.random().toString(16).slice(2)}` }
function readSavedDesigns(): StoredDesign[] {
  try {
    const value = uni.getStorageSync(SAVED_DRAFTS_KEY)
    return Array.isArray(value) ? (value as StoredDesign[]).map((design) => ({ ...design, placements: design.placements.map((item) => ({ ...item, rotationDegrees: item.rotationDegrees ?? 0, zIndex: item.zIndex ?? 0 })) })) : []
  } catch { return [] }
}
function readDraft(): PatternPlacement[] {
  try {
    const value = uni.getStorageSync(DRAFT_KEY)
    return Array.isArray(value) ? value.filter((item) => Boolean(item && typeof item.id === 'string' && typeof item.patternId === 'string')).map((item) => ({ ...item, rotationDegrees: item.rotationDegrees ?? 0, zIndex: item.zIndex ?? 0 })) : []
  } catch { return [] }
}
function clientKey(): string { let value = uni.getStorageSync(CLIENT_KEY) as string; if (!value) { value = `client-${Date.now()}-${Math.random().toString(36).slice(2)}`; uni.setStorageSync(CLIENT_KEY, value) }; return value }

export const useEditorStore = defineStore('editor', () => {
  const placements = ref<PatternPlacement[]>(readDraft())
  const selectedPlacementId = ref<string | null>(null)
  const bag = ref<BagDefinition>(emptyBag)
  const availableBags = ref<BagDefinition[]>([])
  const categories = ref<PatternCategory[]>([])
  const catalog = ref<PatternDefinition[]>([])
  const activeCategoryId = ref('')
  const catalogError = ref('')
  const loadingCatalog = ref(false)
  const catalogLoaded = ref(false)
  const savedDesign = ref<{ id: string; totalPriceCents: number } | null>(null)
  const savedDesigns = ref<StoredDesign[]>(readSavedDesigns())
  const maxDrafts = ref(3)

  const selectedPlacement = computed(() => placements.value.find((item) => item.id === selectedPlacementId.value) ?? null)
  const activePatterns = computed(() => catalog.value.filter((item) => item.categoryId === activeCategoryId.value))
  const patternPriceCents = computed(() => placements.value.reduce((total, item) => total + getPattern(item.patternId).priceCents, 0))
  const totalPriceCents = computed(() => bag.value.basePriceCents + patternPriceCents.value)

  function getPattern(patternId: string): PatternDefinition {
    const item = catalog.value.find((pattern) => pattern.id === patternId)
    if (!item) throw new Error(`Unknown pattern: ${patternId}`)
    return item
  }
  function addPattern(patternId: string): void {
    const pattern = getPattern(patternId)
    if (!canPlacePattern(pattern, bag.value.embroideryArea)) return
    const item: PatternPlacement = { id: placementId(), patternId, centerXRatio: .5, centerYRatio: .5, rotationDegrees: 0, zIndex: Math.max(-1, ...placements.value.map((value) => value.zIndex)) + 1 }
    placements.value.push(clampPlacement(item, pattern, bag.value.embroideryArea)); selectedPlacementId.value = item.id
  }
  function updatePlacement(next: PatternPlacement): void {
    const pattern = getPattern(next.patternId)
    placements.value = placements.value.map((item) => item.id === next.id ? clampPlacement(next, pattern, bag.value.embroideryArea) : item)
  }
  function selectPlacement(id: string | null): void { selectedPlacementId.value = id }
  function deleteSelected(): void { placements.value = placements.value.filter((item) => item.id !== selectedPlacementId.value); selectedPlacementId.value = null }
  function replaceSelected(patternId: string): void { if (!selectedPlacement.value) addPattern(patternId); else updatePlacement({ ...selectedPlacement.value, patternId }) }
  function rotateSelected(deltaDegrees: number): void { if (selectedPlacement.value) updatePlacement({ ...selectedPlacement.value, rotationDegrees: selectedPlacement.value.rotationDegrees + deltaDegrees }) }
  function clearDraft(): void { placements.value = []; selectedPlacementId.value = null; uni.removeStorageSync(DRAFT_KEY) }
  function toBag(item: ApiBag): BagDefinition {
    return { id: item.id, name: item.name, imageUrl: `http://localhost:8000${item.image_url}`, width: item.width_mm, height: item.height_mm, basePriceCents: item.base_price_cents, embroideryArea: { width: item.embroidery_area.width_mm, height: item.embroidery_area.height_mm, relativeX: item.embroidery_area.relative_x, relativeY: item.embroidery_area.relative_y, relativeWidth: item.embroidery_area.relative_width, relativeHeight: item.embroidery_area.relative_height } }
  }
  async function loadCatalog(bagId?: string): Promise<BagDefinition[]> {
    loadingCatalog.value = true; catalogError.value = ''
    try {
      const [bags, apiCategories, apiPatterns, limit] = await Promise.all([catalogApi.bags(), catalogApi.categories(), catalogApi.patterns(), catalogApi.limit()])
      maxDrafts.value = limit.max_drafts
      const choices = bags.map(toBag); if (!choices.length) throw new Error('暂无已上架且已配置刺绣区域的包包'); availableBags.value = choices
      categories.value = apiCategories.map((item) => ({ id: item.id, name: item.name, icon: item.icon, description: item.description }))
      catalog.value = apiPatterns.map((item) => ({ id: item.id, categoryId: item.category_id, name: item.name, imageUrl: `http://localhost:8000${item.image_url}`, width: item.width_mm, height: item.height_mm, priceCents: item.price_cents, patternVersionId: item.pattern_version_id }))
      bag.value = choices.find((item) => item.id === bagId) ?? choices[0]
      activeCategoryId.value = categories.value[0]?.id ?? ''
      placements.value = placements.value.filter((placement) => catalog.value.some((pattern) => pattern.id === placement.patternId))
      catalogLoaded.value = true
      return choices
    } catch (error) { catalogError.value = error instanceof Error ? error.message : '加载商品数据失败'; return [] } finally { loadingCatalog.value = false }
  }
  function fromApiDesign(design: ApiDesign): StoredDesign {
    const byVersion = new Map(catalog.value.map((pattern) => [pattern.patternVersionId, pattern.id]))
    return { id: design.id, bagId: design.bag_id, totalPriceCents: design.total_price_cents, placements: design.items.map((item) => ({ id: item.id, patternId: byVersion.get(item.pattern_version_id) ?? '', centerXRatio: item.center_x_ratio, centerYRatio: item.center_y_ratio, rotationDegrees: item.rotation_degrees, zIndex: item.z_index })).filter((item) => item.patternId) }
  }
  async function loadSavedDesigns(): Promise<void> { savedDesigns.value = (await catalogApi.designs(clientKey())).map(fromApiDesign) }
  async function saveDesign(): Promise<void> {
    if (savedDesigns.value.length >= maxDrafts.value) throw new Error(`最多保存 ${maxDrafts.value} 个设计，请先删除一个`)
    const items = placements.value.map((item) => { const pattern = getPattern(item.patternId); if (!pattern.patternVersionId) throw new Error('当前图案不是正式版本，无法保存'); return { pattern_version_id: pattern.patternVersionId, center_x_ratio: item.centerXRatio, center_y_ratio: item.centerYRatio, rotation_degrees: item.rotationDegrees, z_index: item.zIndex } })
    const design = await catalogApi.saveDesign({ bag_id: bag.value.id, client_key: clientKey(), items })
    savedDesign.value = { id: design.id, totalPriceCents: design.total_price_cents }
    savedDesigns.value.unshift({ ...savedDesign.value, bagId: bag.value.id, placements: JSON.parse(JSON.stringify(placements.value)) })
  }
  async function restoreDesign(design: StoredDesign): Promise<void> { await loadCatalog(design.bagId); placements.value = JSON.parse(JSON.stringify(design.placements)); selectedPlacementId.value = null; savedDesign.value = { id: design.id, totalPriceCents: design.totalPriceCents } }
  async function removeSavedDesign(design: StoredDesign): Promise<void> { await catalogApi.deleteDesign(design.id, clientKey()); savedDesigns.value = savedDesigns.value.filter((item) => item.id !== design.id); if (savedDesign.value?.id === design.id) savedDesign.value = null }

  watch(placements, (value) => uni.setStorageSync(DRAFT_KEY, value), { deep: true })
  watch(savedDesigns, (value) => uni.setStorageSync(SAVED_DRAFTS_KEY, value), { deep: true })
  return { bag, availableBags, categories, activeCategoryId, activePatterns, placements, selectedPlacementId, selectedPlacement, patternPriceCents, totalPriceCents, catalogError, loadingCatalog, catalogLoaded, savedDesign, savedDesigns, maxDrafts, getPattern, addPattern, updatePlacement, selectPlacement, deleteSelected, replaceSelected, rotateSelected, clearDraft, loadCatalog, loadSavedDesigns, saveDesign, restoreDesign, removeSavedDesign }
})
