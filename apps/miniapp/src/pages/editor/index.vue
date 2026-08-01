<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { onReady, onShow } from '@dcloudio/uni-app'
import { patternPixelSize, placementPixelPoint, pixelPointToPlacement } from '../../features/editor/domain/geometry'
import { advanceRotation, pointerAngleDegrees, type RotationSession } from '../../features/editor/domain/rotation'
import { nextViewportZoom } from '../../features/editor/domain/viewport'
import type { PatternPlacement, PixelSize } from '../../features/editor/domain/types'
import { useEditorStore } from '../../features/editor/stores/editor'

interface ZoneRect extends PixelSize { left: number; top: number }
interface TouchLikeEvent { touches: { length: number; [index: number]: { clientX: number; clientY: number } } }

const editor = useEditorStore()
const zoneRect = ref<ZoneRect | null>(null)
const dragging = ref<{ id: string; offsetX: number; offsetY: number } | null>(null)
const rotating = ref<({ id: string } & RotationSession) | null>(null)
const saving = ref(false)
const panelOpen = ref(false)
const canvasZoom = ref(1)
let rotateFrame: number | null = null
let pendingRotation: { x: number; y: number } | null = null

const price = (cents: number) => `¥${(cents / 100).toFixed(2)}`
const selectedPattern = computed(() => editor.selectedPlacement ? editor.getPattern(editor.selectedPlacement.patternId) : null)
const visibleCategories = computed(() => editor.categories.filter((category) => category.name.trim() !== '1'))
const activeCategory = computed(() => visibleCategories.value.find((item) => item.id === editor.activeCategoryId))

function measure(): void {
  nextTick(() => uni.createSelectorQuery().select('.embroidery-zone').boundingClientRect((rect) => {
    if (!rect) return
    const box = rect as ZoneRect
    zoneRect.value = { left: box.left, top: box.top, width: box.width, height: box.height }
  }).exec())
}

function placementStyle(placement: PatternPlacement): Record<string, string> {
  if (!zoneRect.value) return { visibility: 'hidden' }
  const pattern = editor.getPattern(placement.patternId)
  const point = placementPixelPoint(placement, pattern, editor.bag.embroideryArea, zoneRect.value)
  const size = patternPixelSize(pattern, editor.bag.embroideryArea, zoneRect.value)
  return {
    width: `${size.width}px`, height: `${size.height}px`, zIndex: `${placement.zIndex}`,
    transform: `translate3d(${point.x}px,${point.y}px,0) rotate(${placement.rotationDegrees}deg)`,
  }
}

function choose(patternId: string): void { editor.addPattern(patternId); panelOpen.value = false }
function selectCategory(id: string): void { editor.activeCategoryId = id; panelOpen.value = true }
function selectBag(id: string): void { if (id !== editor.bag.id) void switchBag(id) }
function updateCanvasZoom(delta: number): void { canvasZoom.value = nextViewportZoom(canvasZoom.value, delta) }

function start(placement: PatternPlacement, event: TouchLikeEvent): void {
  if (!zoneRect.value || !event.touches[0]) return
  editor.selectPlacement(placement.id); editor.beginGesture()
  const point = placementPixelPoint(placement, editor.getPattern(placement.patternId), editor.bag.embroideryArea, zoneRect.value)
  dragging.value = { id: placement.id, offsetX: event.touches[0].clientX - zoneRect.value.left - point.x, offsetY: event.touches[0].clientY - zoneRect.value.top - point.y }
}

function startMouse(placement: PatternPlacement, event: MouseEvent): void {
  if (!zoneRect.value) return
  editor.selectPlacement(placement.id); editor.beginGesture()
  const point = placementPixelPoint(placement, editor.getPattern(placement.patternId), editor.bag.embroideryArea, zoneRect.value)
  dragging.value = { id: placement.id, offsetX: event.clientX - zoneRect.value.left - point.x, offsetY: event.clientY - zoneRect.value.top - point.y }
}

function applyPendingRotation(): void {
  if (!zoneRect.value || !rotating.value || !pendingRotation) return
  const pointer = pendingRotation; pendingRotation = null
  const item = editor.placements.find((placement) => placement.id === rotating.value?.id)
  if (!item) return
  const centerX = zoneRect.value.left + item.centerXRatio * zoneRect.value.width
  const centerY = zoneRect.value.top + item.centerYRatio * zoneRect.value.height
  const next = advanceRotation(rotating.value, pointerAngleDegrees(pointer.x, pointer.y, centerX, centerY))
  rotating.value = { id: item.id, ...next }
  // Updating at most once per animation frame keeps the rotation handle responsive.
  editor.updatePlacement({ ...item, rotationDegrees: Math.round(next.rotationDegrees * 10) / 10 })
}

function queueRotation(x: number, y: number): void {
  pendingRotation = { x, y }
  if (rotateFrame !== null) return
  rotateFrame = requestAnimationFrame(() => { rotateFrame = null; applyPendingRotation() })
}

function movePlacement(x: number, y: number): void {
  if (!zoneRect.value) return
  if (rotating.value) { queueRotation(x, y); return }
  if (!dragging.value) return
  const item = editor.placements.find((placement) => placement.id === dragging.value?.id)
  if (!item) return
  editor.updatePlacement(pixelPointToPlacement({ x: x - zoneRect.value.left - dragging.value.offsetX, y: y - zoneRect.value.top - dragging.value.offsetY }, item, editor.getPattern(item.patternId), editor.bag.embroideryArea, zoneRect.value))
}

function move(event: TouchLikeEvent): void { if (event.touches[0]) movePlacement(event.touches[0].clientX, event.touches[0].clientY) }
function moveMouse(event: MouseEvent): void { movePlacement(event.clientX, event.clientY) }

function beginRotate(placement: PatternPlacement, x: number, y: number): void {
  if (!zoneRect.value) return
  editor.selectPlacement(placement.id); editor.beginGesture()
  const centerX = zoneRect.value.left + placement.centerXRatio * zoneRect.value.width
  const centerY = zoneRect.value.top + placement.centerYRatio * zoneRect.value.height
  rotating.value = { id: placement.id, lastPointerAngle: pointerAngleDegrees(x, y, centerX, centerY), rotationDegrees: placement.rotationDegrees }
}

function beginRotateTouch(placement: PatternPlacement, event: TouchLikeEvent): void {
  if (event.touches[0]) beginRotate(placement, event.touches[0].clientX, event.touches[0].clientY)
}

function stopGesture(): void {
  if (rotateFrame !== null) { cancelAnimationFrame(rotateFrame); rotateFrame = null; applyPendingRotation() }
  dragging.value = null; rotating.value = null; pendingRotation = null
}

async function save(): Promise<void> {
  saving.value = true
  try { await editor.saveDesign(); uni.navigateTo({ url: '/pages/confirmation/index' }) }
  catch (error) { uni.showToast({ title: error instanceof Error ? error.message : '保存失败', icon: 'none' }) }
  finally { saving.value = false }
}

async function restore(design: { id: string; totalPriceCents: number; bagId: string; placements: PatternPlacement[] }): Promise<void> {
  try { await editor.restoreDesign(design); measure(); uni.showToast({ title: '设计已恢复到画布', icon: 'success' }) }
  catch { uni.showToast({ title: '恢复失败，请检查商品是否仍上架', icon: 'none' }) }
}

async function remove(design: { id: string; totalPriceCents: number; bagId: string; placements: PatternPlacement[] }): Promise<void> {
  try { await editor.removeSavedDesign(design); uni.showToast({ title: '设计已删除', icon: 'success' }) }
  catch (error) { uni.showToast({ title: error instanceof Error ? error.message : '删除失败', icon: 'none' }) }
}

async function switchBag(id: string): Promise<void> { await editor.loadCatalog(id); editor.clearDraft(); measure() }

onReady(measure)
onShow(() => { if (!editor.loadingCatalog) void (async () => { if (!editor.catalogLoaded) await editor.loadCatalog(); await editor.loadSavedDesigns(); measure() })() })
watch(() => editor.catalogLoaded, (ready) => { if (ready) measure() })
watch(canvasZoom, measure)
</script>

<template>
  <view class="page">
    <view v-if="editor.loadingCatalog" class="state">正在准备你的创作桌…</view>
    <view v-else-if="!editor.catalogLoaded" class="state error">{{ editor.catalogError || '暂时不能进入编辑器' }}</view>
    <template v-else>
      <view class="page-heading"><text>我的 DIY 工作台</text><text>选择包包，开始拼贴</text></view>

      <scroll-view class="bag-strip" scroll-x :show-scrollbar="false">
        <view class="bag-chip" v-for="choice in editor.availableBags" :key="choice.id" :class="{ active: choice.id === editor.bag.id }" @tap="selectBag(choice.id)">
          <image :src="choice.imageUrl" mode="aspectFit"/><view><text class="bag-name">{{ choice.name }}</text><text class="bag-price">{{ price(choice.basePriceCents) }}</text></view>
        </view>
      </scroll-view>

      <view class="editor-card">
        <view class="canvas-head"><view><text class="canvas-label">刺绣画布</text><text class="canvas-size">{{ editor.bag.embroideryArea.width }} × {{ editor.bag.embroideryArea.height }} mm</text></view><text class="zoom-value">{{ Math.round(canvasZoom * 100) }}%</text></view>
        <view class="canvas-viewport">
          <view class="canvas-scene" :style="{ transform: `scale(${canvasZoom})` }">
            <view class="stage" :style="{ aspectRatio: `${editor.bag.width}/${editor.bag.height}` }">
              <image class="bag" :src="editor.bag.imageUrl" mode="aspectFill"/>
              <view class="embroidery-zone" :style="{ left: `${editor.bag.embroideryArea.relativeX * 100}%`, top: `${editor.bag.embroideryArea.relativeY * 100}%`, width: `${editor.bag.embroideryArea.relativeWidth * 100}%`, height: `${editor.bag.embroideryArea.relativeHeight * 100}%` }" @tap="editor.selectPlacement(null)" @touchmove.stop.prevent="move" @touchend="stopGesture" @touchcancel="stopGesture" @mousemove.stop="moveMouse" @mouseup="stopGesture" @mouseleave="stopGesture">
                <view v-for="placement in editor.placements" :key="placement.id" class="placed" :class="{ selected: placement.id === editor.selectedPlacementId }" :style="placementStyle(placement)" @tap.stop="editor.selectPlacement(placement.id)" @touchstart.stop="start(placement, $event)" @mousedown.stop="startMouse(placement, $event)">
                  <image :src="editor.getPattern(placement.patternId).imageUrl" mode="aspectFit"/>
                  <view v-if="placement.id === editor.selectedPlacementId" class="rotate-handle" @touchstart.stop.prevent="beginRotateTouch(placement, $event)" @mousedown.stop="beginRotate(placement, $event.clientX, $event.clientY)">↻</view>
                </view>
                <text v-if="!editor.placements.length" class="canvas-empty">从下方分类中添加图案</text>
              </view>
            </view>
          </view>
        </view>
        <view class="category-section"><text class="section-title">选择图案</text><scroll-view class="category-strip" scroll-x :show-scrollbar="false"><view v-for="category in visibleCategories" :key="category.id" class="category-button" :class="{ active: category.id === editor.activeCategoryId }" @tap="selectCategory(category.id)"><text class="icon">{{ category.icon || '✦' }}</text><text>{{ category.name }}</text></view></scroll-view></view>
        <view class="canvas-tools"><button @tap="updateCanvasZoom(-.1)">−</button><button @tap="updateCanvasZoom(.1)">+</button><view class="tool-divider"/><button :disabled="!editor.selectedPlacement" @tap="editor.undo">撤销</button><button :disabled="!editor.selectedPlacement" @tap="editor.redo">重做</button><button class="danger" :disabled="!editor.selectedPlacement" @tap="editor.deleteSelected">删除</button></view>
      </view>

      <view v-if="panelOpen" class="catalog-mask" @tap="panelOpen = false"><view class="catalog-panel" @tap.stop><view class="panel-head"><view><text>{{ activeCategory?.icon || '✦' }} {{ activeCategory?.name || '图案' }}</text><text>选择后直接放到画布中央</text></view><text class="close" @tap="panelOpen = false">关闭</text></view><scroll-view class="catalog" scroll-y><view v-for="pattern in editor.activePatterns" :key="pattern.id" class="pattern-card" @tap="choose(pattern.id)"><image :src="pattern.imageUrl" mode="aspectFit"/><text>{{ pattern.name }}</text><text>{{ pattern.width }} × {{ pattern.height }} mm</text><text>{{ price(pattern.priceCents) }}</text></view><view v-if="!editor.activePatterns.length" class="empty">该分类暂未上架图案</view></scroll-view></view></view>

      <view class="selection-tip" v-if="selectedPattern">已选「{{ selectedPattern.name }}」：单指拖动，拖动蓝色手柄旋转；图案尺寸固定。</view>
      <view class="action-dock"><view class="price-row"><view><text>包包 {{ price(editor.bag.basePriceCents) }}</text><text>图案 {{ price(editor.patternPriceCents) }}</text></view><view class="total"><text>合计</text><text>{{ price(editor.totalPriceCents) }}</text></view></view><view class="bottom-actions"><button @tap="editor.clearDraft">清空</button><button class="primary" :loading="saving" @tap="save">保存设计</button></view></view>

      <view v-if="editor.savedDesigns.length" class="draft-list"><text class="draft-title">已保存设计 {{ editor.savedDesigns.length }}/{{ editor.maxDrafts }}</text><view v-for="design in editor.savedDesigns" :key="design.id" class="draft-row"><text>设计 {{ design.id.slice(0, 6) }} · {{ price(design.totalPriceCents) }}</text><view><button @tap.stop="restore(design)">恢复</button><button class="danger" @tap.stop="remove(design)">删除</button></view></view></view>
    </template>
  </view>
</template>

<style scoped>
.page{min-height:100vh;box-sizing:border-box;padding:20rpx 20rpx 36rpx;background:#f7f3ef;color:#352b29}.state{padding:120rpx 32rpx;text-align:center;color:#806a60}.error{color:#bd4e48}.page-heading{display:flex;align-items:baseline;justify-content:space-between;padding:4rpx 4rpx 16rpx}.page-heading text:first-child{font-size:31rpx;font-weight:800}.page-heading text:last-child{color:#9a8377;font-size:21rpx}
.bag-strip{height:112rpx;white-space:nowrap;margin-bottom:16rpx}.bag-chip{display:inline-flex;width:206rpx;height:112rpx;box-sizing:border-box;vertical-align:top;align-items:center;gap:11rpx;margin-right:12rpx;padding:12rpx;border:2rpx solid transparent;border-radius:18rpx;background:#fff;box-shadow:0 6rpx 18rpx rgba(101,73,54,.07)}.bag-chip.active{border-color:#ec8479;background:#fffafa;box-shadow:0 6rpx 18rpx rgba(216,110,98,.17)}.bag-chip image{width:78rpx;height:78rpx;flex:none}.bag-chip view{min-width:0;display:flex;flex-direction:column;gap:5rpx}.bag-name{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-size:23rpx;font-weight:700}.bag-price{color:#ae6547;font-size:20rpx}
.editor-card{padding:17rpx 15rpx 16rpx;border:1rpx solid rgba(255,255,255,.85);border-radius:28rpx;background:#fff;box-shadow:0 10rpx 28rpx rgba(108,75,53,.08)}.canvas-head{display:flex;justify-content:space-between;align-items:center;padding:0 8rpx 13rpx}.canvas-head view{display:flex;flex-direction:column;gap:4rpx}.canvas-label,.section-title{font-weight:800;font-size:24rpx}.canvas-size{color:#9d8476;font-size:18rpx}.zoom-value{padding:5rpx 12rpx;border-radius:20rpx;background:#f6ebe4;color:#a56447;font-size:19rpx}.canvas-viewport{position:relative;height:514rpx;overflow:hidden;border-radius:20rpx;background:radial-gradient(circle at 50% 42%,#fff 0%,#f8f1ea 75%)}.canvas-scene{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;transform-origin:center;will-change:transform}.stage{position:relative;width:92%;overflow:hidden;border-radius:14rpx;background:#fff;box-shadow:0 8rpx 19rpx rgba(81,53,38,.12)}.bag{position:absolute;inset:0;width:100%;height:100%}.embroidery-zone{position:absolute;overflow:hidden;border:2rpx dashed #9d6043;touch-action:none}.canvas-empty{position:absolute;left:50%;top:50%;padding:9rpx 14rpx;transform:translate(-50%,-50%);border-radius:20rpx;background:rgba(255,255,255,.8);color:#9b7562;font-size:19rpx;white-space:nowrap}.placed{position:absolute;left:0;top:0;touch-action:none;will-change:transform}.placed image{width:100%;height:100%}.selected{outline:2rpx solid #f06e6a;outline-offset:3rpx}.rotate-handle{position:absolute;left:50%;top:-38rpx;width:36rpx;height:36rpx;transform:translateX(-50%);border-radius:50%;display:flex;align-items:center;justify-content:center;background:#4b85ec;color:#fff;font-size:25rpx;box-shadow:0 3rpx 8rpx rgba(46,101,192,.28)}
.category-section{margin-top:17rpx}.section-title{display:block;margin:0 8rpx 9rpx}.category-strip{height:76rpx;white-space:nowrap}.category-button{display:inline-flex;min-width:112rpx;height:68rpx;box-sizing:border-box;vertical-align:top;align-items:center;justify-content:center;gap:7rpx;margin-right:10rpx;padding:0 14rpx;border:1rpx solid #f0e4dc;border-radius:16rpx;background:#fcf8f5;color:#6b5145;font-size:20rpx}.category-button.active{border-color:#ec8479;background:#fff0ed;color:#a65645;box-shadow:inset 0 0 0 1rpx #ec8479}.icon{font-size:25rpx}.canvas-tools{display:flex;align-items:center;gap:8rpx;margin-top:11rpx;padding-top:14rpx;border-top:1rpx solid #f2ece7}.canvas-tools button{min-width:57rpx;margin:0;padding:0 13rpx;border:1rpx solid #eaded5;border-radius:13rpx;background:#fff;color:#5d4640;font-size:20rpx;line-height:58rpx}.canvas-tools button[disabled]{opacity:.38}.canvas-tools .danger{color:#c85a50}.tool-divider{width:1rpx;height:34rpx;background:#eee4de;margin:0 2rpx}
.catalog-mask{position:fixed;z-index:20;inset:0;display:flex;align-items:flex-end;background:rgba(44,31,25,.36)}.catalog-panel{width:100%;max-height:64vh;box-sizing:border-box;padding:26rpx 22rpx 28rpx;border-radius:30rpx 30rpx 0 0;background:#fff;box-shadow:0 -10rpx 30rpx rgba(50,28,18,.13)}.panel-head{display:flex;justify-content:space-between;align-items:flex-start;margin:0 6rpx 18rpx}.panel-head view{display:flex;flex-direction:column;gap:7rpx}.panel-head text:first-child{font-size:29rpx;font-weight:800}.panel-head text:nth-child(2){color:#9b867b;font-size:19rpx}.panel-head .close{padding:8rpx 14rpx;border-radius:14rpx;background:#f8f2ee;color:#8c6553;font-size:20rpx}.catalog{max-height:46vh;display:grid;grid-template-columns:repeat(3,1fr);gap:13rpx}.pattern-card{min-height:184rpx;box-sizing:border-box;padding:11rpx 8rpx;border:1rpx solid #f0e5de;border-radius:16rpx;background:#fffdfc;text-align:center;font-size:18rpx}.pattern-card image{width:80rpx;height:80rpx}.pattern-card text{display:block;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;line-height:1.5}.pattern-card text:nth-last-child(-n+2){color:#967d70}.empty{grid-column:span 3;padding:38rpx;text-align:center;color:#968177}
.selection-tip{margin-top:14rpx;padding:14rpx 18rpx;border-radius:15rpx;background:#fff0e4;color:#8b5e49;font-size:20rpx;line-height:1.45}.action-dock{position:sticky;z-index:5;bottom:0;margin-top:15rpx;padding:15rpx;border:1rpx solid rgba(255,255,255,.9);border-radius:21rpx;background:rgba(255,255,255,.96);box-shadow:0 -4rpx 15rpx rgba(89,60,40,.06)}.price-row{display:flex;align-items:center;justify-content:space-between}.price-row view{display:flex;gap:13rpx;color:#806c62;font-size:20rpx}.price-row .total{display:flex;flex-direction:column;align-items:flex-end;gap:1rpx;color:#bb5947;font-size:18rpx}.total text:last-child{font-size:29rpx;font-weight:800}.bottom-actions{display:flex;gap:12rpx;margin-top:13rpx}.bottom-actions button,.draft-row button{margin:0;padding:0;border-radius:13rpx;font-size:22rpx;line-height:66rpx}.bottom-actions button:first-child{width:31%;border:1rpx solid #eaded5;background:#fff;color:#7c6256}.bottom-actions .primary{flex:1;border:1rpx solid #b46b4a;background:#b46b4a;color:#fff;font-weight:700}.draft-list{margin-top:15rpx;padding:18rpx;border-radius:20rpx;background:#fff}.draft-title{display:block;font-size:22rpx;font-weight:800}.draft-row{display:flex;align-items:center;justify-content:space-between;margin-top:12rpx;padding-top:12rpx;border-top:1rpx solid #f3ece7;font-size:19rpx}.draft-row view{display:flex;gap:8rpx}.draft-row button{padding:0 14rpx;border:1rpx solid #eaded5;background:#fff;line-height:52rpx}.draft-row .danger{color:#c85a50}
</style>
