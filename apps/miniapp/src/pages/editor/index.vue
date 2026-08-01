<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { onReady, onShow } from '@dcloudio/uni-app'
import { patternPixelSize, placementPixelPoint, pixelPointToPlacement } from '../../features/editor/domain/geometry'
import type { PatternPlacement, PixelSize } from '../../features/editor/domain/types'
import { useEditorStore } from '../../features/editor/stores/editor'

interface ZoneRect extends PixelSize { left: number; top: number }
interface TouchLikeEvent { touches: { length: number; [index: number]: { clientX: number; clientY: number } } }
const editor = useEditorStore()
const zoneRect = ref<ZoneRect | null>(null)
const dragging = ref<{ id: string; offsetX: number; offsetY: number } | null>(null)
const rotating = ref<{ id: string; pointerAngle: number; rotation: number } | null>(null)
const saving = ref(false)
const panelOpen = ref(false)
const canvasZoom = ref(1)
const price = (cents: number) => `¥${(cents / 100).toFixed(2)}`
const selectedPattern = computed(() => editor.selectedPlacement ? editor.getPattern(editor.selectedPlacement.patternId) : null)

function measure(): void { nextTick(() => uni.createSelectorQuery().select('.embroidery-zone').boundingClientRect((rect) => { if (rect) { const box = rect as ZoneRect; zoneRect.value = { left: box.left, top: box.top, width: box.width, height: box.height } } }).exec()) }
function placementStyle(placement: PatternPlacement): Record<string, string> {
  if (!zoneRect.value) return { visibility: 'hidden' }
  const pattern = editor.getPattern(placement.patternId)
  const point = placementPixelPoint(placement, pattern, editor.bag.embroideryArea, zoneRect.value)
  const size = patternPixelSize(pattern, editor.bag.embroideryArea, zoneRect.value)
  return { width: `${size.width}px`, height: `${size.height}px`, zIndex: `${placement.zIndex}`, transform: `translate3d(${point.x}px,${point.y}px,0) rotate(${placement.rotationDegrees}deg)` }
}
function choose(patternId: string): void { editor.addPattern(patternId); panelOpen.value = false }
function start(placement: PatternPlacement, event: TouchLikeEvent): void {
  if (!zoneRect.value || !event.touches[0]) return
  editor.selectPlacement(placement.id)
  const point = placementPixelPoint(placement, editor.getPattern(placement.patternId), editor.bag.embroideryArea, zoneRect.value)
  dragging.value = { id: placement.id, offsetX: event.touches[0].clientX - zoneRect.value.left - point.x, offsetY: event.touches[0].clientY - zoneRect.value.top - point.y }
}
function startMouse(placement: PatternPlacement, event: MouseEvent): void {
  if (!zoneRect.value) return
  editor.selectPlacement(placement.id)
  const point = placementPixelPoint(placement, editor.getPattern(placement.patternId), editor.bag.embroideryArea, zoneRect.value)
  dragging.value = { id: placement.id, offsetX: event.clientX - zoneRect.value.left - point.x, offsetY: event.clientY - zoneRect.value.top - point.y }
}
function rotateFromPointer(placement: PatternPlacement, x: number, y: number): void {
  if (!zoneRect.value || !rotating.value) return
  const centerX = zoneRect.value.left + placement.centerXRatio * zoneRect.value.width
  const centerY = zoneRect.value.top + placement.centerYRatio * zoneRect.value.height
  const angle = Math.atan2(y - centerY, x - centerX) * 180 / Math.PI
  editor.updatePlacement({ ...placement, rotationDegrees: Math.round(rotating.value.rotation + angle - rotating.value.pointerAngle) })
}
function move(event: TouchLikeEvent): void {
  if (!zoneRect.value || !event.touches[0]) return
  const item = editor.placements.find((placement) => placement.id === (rotating.value?.id ?? dragging.value?.id))
  if (!item) return
  if (rotating.value) { rotateFromPointer(item, event.touches[0].clientX, event.touches[0].clientY); return }
  if (!dragging.value) return
  editor.updatePlacement(pixelPointToPlacement({ x: event.touches[0].clientX - zoneRect.value.left - dragging.value.offsetX, y: event.touches[0].clientY - zoneRect.value.top - dragging.value.offsetY }, item, editor.getPattern(item.patternId), editor.bag.embroideryArea, zoneRect.value))
}
function moveMouse(event: MouseEvent): void {
  if (!zoneRect.value) return
  const item = editor.placements.find((placement) => placement.id === (rotating.value?.id ?? dragging.value?.id))
  if (!item) return
  if (rotating.value) { rotateFromPointer(item, event.clientX, event.clientY); return }
  if (!dragging.value) return
  editor.updatePlacement(pixelPointToPlacement({ x: event.clientX - zoneRect.value.left - dragging.value.offsetX, y: event.clientY - zoneRect.value.top - dragging.value.offsetY }, item, editor.getPattern(item.patternId), editor.bag.embroideryArea, zoneRect.value))
}
function beginRotate(placement: PatternPlacement, x: number, y: number): void {
  if (!zoneRect.value) return
  editor.selectPlacement(placement.id)
  const centerX = zoneRect.value.left + placement.centerXRatio * zoneRect.value.width
  const centerY = zoneRect.value.top + placement.centerYRatio * zoneRect.value.height
  rotating.value = { id: placement.id, pointerAngle: Math.atan2(y - centerY, x - centerX) * 180 / Math.PI, rotation: placement.rotationDegrees }
}
function beginRotateTouch(placement: PatternPlacement, event: TouchLikeEvent): void { if (event.touches[0]) beginRotate(placement, event.touches[0].clientX, event.touches[0].clientY) }
function stopGesture(): void { dragging.value = null; rotating.value = null }
async function save(): Promise<void> { saving.value = true; try { await editor.saveDesign(); uni.navigateTo({ url: '/pages/confirmation/index' }) } catch (error) { uni.showToast({ title: error instanceof Error ? error.message : '保存失败', icon: 'none' }) } finally { saving.value = false } }
async function restore(design: { id: string; totalPriceCents: number; bagId: string; placements: PatternPlacement[] }): Promise<void> { try { await editor.restoreDesign(design); measure(); uni.showToast({ title: '设计已恢复到画布', icon: 'success' }) } catch { uni.showToast({ title: '恢复失败，请检查商品是否仍上架', icon: 'none' }) } }
async function remove(design: { id: string; totalPriceCents: number; bagId: string; placements: PatternPlacement[] }): Promise<void> { try { await editor.removeSavedDesign(design); uni.showToast({ title: '设计已删除', icon: 'success' }) } catch (error) { uni.showToast({ title: error instanceof Error ? error.message : '删除失败', icon: 'none' }) } }
async function switchBag(id: string): Promise<void> { await editor.loadCatalog(id); editor.clearDraft(); measure() }
function selectCategory(id: string): void { editor.activeCategoryId = id; panelOpen.value = true }
onReady(measure)
onShow(() => { if (!editor.loadingCatalog) void (async () => { if (!editor.catalogLoaded) await editor.loadCatalog(); await editor.loadSavedDesigns(); measure() })() })
watch(() => editor.catalogLoaded, (ready) => { if (ready) measure() })
</script>

<template>
  <view class="page">
    <view v-if="editor.loadingCatalog" class="state">正在加载商品数据…</view>
    <view v-else-if="!editor.catalogLoaded" class="state error">{{ editor.catalogError || '暂时不能进入编辑器' }}</view>
    <template v-else>
      <scroll-view class="bag-strip" scroll-x>
        <view class="bag-chip" v-for="choice in editor.availableBags" :key="choice.id" :class="{ active: choice.id === editor.bag.id }" @tap="switchBag(choice.id)">
          <image :src="choice.imageUrl" mode="aspectFit"/><text>{{ choice.name }}</text>
        </view>
      </scroll-view>
      <view class="workbench">
        <view class="category-rail">
          <view v-for="category in editor.categories" :key="category.id" class="category-button" :class="{ active: category.id === editor.activeCategoryId }" @tap="selectCategory(category.id)">
            <text class="icon">{{ category.icon || '✦' }}</text><text>{{ category.name }}</text>
          </view>
        </view>
        <view class="canvas-column">
          <view class="canvas-wrap" :style="{ transform: `scale(${canvasZoom})` }">
            <view class="stage" :style="{ aspectRatio: `${editor.bag.width}/${editor.bag.height}` }">
              <image class="bag" :src="editor.bag.imageUrl" mode="aspectFill"/>
              <view class="embroidery-zone" :style="{ left: `${editor.bag.embroideryArea.relativeX * 100}%`, top: `${editor.bag.embroideryArea.relativeY * 100}%`, width: `${editor.bag.embroideryArea.relativeWidth * 100}%`, height: `${editor.bag.embroideryArea.relativeHeight * 100}%` }" @tap="editor.selectPlacement(null)" @touchmove.stop.prevent="move" @touchend="stopGesture" @mousemove.stop="moveMouse" @mouseup="stopGesture" @mouseleave="stopGesture">
                <view v-for="placement in editor.placements" :key="placement.id" class="placed" :class="{ selected: placement.id === editor.selectedPlacementId }" :style="placementStyle(placement)" @tap.stop="editor.selectPlacement(placement.id)" @touchstart.stop="start(placement, $event)" @mousedown.stop="startMouse(placement, $event)">
                  <image :src="editor.getPattern(placement.patternId).imageUrl" mode="aspectFit"/>
                  <view v-if="placement.id === editor.selectedPlacementId" class="rotate-handle" @touchstart.stop.prevent="beginRotateTouch(placement, $event)" @mousedown.stop="beginRotate(placement, $event.clientX, $event.clientY)">↻</view>
                </view>
              </view>
            </view>
          </view>
          <view class="canvas-tools"><button @tap="canvasZoom = Math.max(.8, canvasZoom - .1)">−</button><button @tap="canvasZoom = Math.min(1.2, canvasZoom + .1)">+</button><button @tap="editor.rotateSelected(-15)">↺</button><button @tap="editor.rotateSelected(15)">↻</button><button class="danger" @tap="editor.deleteSelected">删除</button></view>
        </view>
      </view>
      <view v-if="panelOpen" class="catalog-mask" @tap="panelOpen = false"><view class="catalog-panel" @tap.stop><view class="panel-head"><text>{{ editor.categories.find((item) => item.id === editor.activeCategoryId)?.name }}</text><text @tap="panelOpen = false">关闭</text></view><view class="catalog"><view v-for="pattern in editor.activePatterns" :key="pattern.id" class="pattern-card" @tap="choose(pattern.id)"><image :src="pattern.imageUrl" mode="aspectFit"/><text>{{ pattern.name }}</text><text>{{ pattern.width }}×{{ pattern.height }}mm</text><text>{{ price(pattern.priceCents) }}</text></view><view v-if="!editor.activePatterns.length" class="empty">该分类暂未上架图案</view></view></view></view>
      <view class="price-card"><view><text>包包</text><text>{{ price(editor.bag.basePriceCents) }}</text></view><view><text>图案</text><text>{{ price(editor.patternPriceCents) }}</text></view><view class="total"><text>总计</text><text>{{ price(editor.totalPriceCents) }}</text></view></view>
      <view v-if="selectedPattern" class="selection-tip">已选 {{ selectedPattern.name }}，可单指拖动；点蓝色旋转手柄手动旋转。图案尺寸固定，不能缩放。</view>
      <view class="bottom-actions"><button @tap="editor.clearDraft">清空</button><button class="primary" :loading="saving" @tap="save">保存设计并确认</button></view>
      <view v-if="editor.savedDesigns.length" class="draft-list"><text class="draft-title">已保存设计（{{ editor.savedDesigns.length }}/{{ editor.maxDrafts }}）</text><view v-for="design in editor.savedDesigns" :key="design.id" class="draft-row"><text>设计 {{ design.id.slice(0, 6) }} · {{ price(design.totalPriceCents) }}</text><view><button @tap.stop="restore(design)">恢复</button><button class="danger" @tap.stop="remove(design)">删除</button></view></view></view>
    </template>
  </view>
</template>

<style scoped>
.page{min-height:100vh;padding:18rpx;background:#f6f4f1;color:#2f2928}.state{padding:80rpx 30rpx;text-align:center}.error{color:#bd4e48}.bag-strip{white-space:nowrap;padding:8rpx 0 20rpx}.bag-chip{display:inline-flex;vertical-align:top;width:150rpx;min-height:142rpx;margin-right:14rpx;padding:10rpx;box-sizing:border-box;flex-direction:column;align-items:center;gap:4rpx;border-radius:16rpx;background:#fff;box-shadow:0 4rpx 14rpx #3331;font-size:21rpx}.bag-chip.active{outline:4rpx solid #fa7770}.bag-chip image{width:90rpx;height:88rpx}.workbench{display:flex;gap:14rpx}.category-rail{width:128rpx;flex:none;display:flex;flex-direction:column;gap:12rpx}.category-button{min-height:94rpx;padding:8rpx 4rpx;box-sizing:border-box;border-radius:16rpx;background:#dfeaff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-size:18rpx;line-height:1.25}.category-button:nth-child(2n){background:#dff4d7}.category-button:nth-child(3n){background:#fff2ba}.category-button.active{box-shadow:inset 0 0 0 4rpx #fb7770}.icon{font-size:31rpx}.canvas-column{min-width:0;flex:1;overflow:hidden}.canvas-wrap{transform-origin:top center}.stage{position:relative;width:100%;overflow:hidden;border-radius:18rpx;background:#fff;box-shadow:0 6rpx 18rpx #4b33261a}.bag{position:absolute;inset:0;width:100%;height:100%}.embroidery-zone{position:absolute;overflow:hidden;border:2rpx dashed #9d6043;touch-action:none}.placed{position:absolute;left:0;top:0;touch-action:none}.placed image{width:100%;height:100%}.selected{outline:2rpx solid #fa6f6a;outline-offset:3rpx}.rotate-handle{position:absolute;left:50%;top:-34rpx;width:34rpx;height:34rpx;transform:translateX(-50%);border-radius:50%;display:flex;align-items:center;justify-content:center;background:#4385f4;color:#fff;font-size:25rpx}.canvas-tools{display:flex;gap:8rpx;justify-content:center;margin-top:14rpx}.canvas-tools button,.bottom-actions button,.draft-row button{margin:0;padding:0 17rpx;background:#fff;border:1rpx solid #ddd;font-size:22rpx;line-height:60rpx}.danger{color:#c54a45}.price-card{display:flex;justify-content:space-between;margin-top:22rpx;padding:20rpx;border-radius:18rpx;background:#fff}.price-card view{display:flex;flex-direction:column;gap:5rpx;font-size:23rpx}.total{color:#d75a49;font-weight:700}.selection-tip{margin-top:16rpx;padding:16rpx;border-radius:14rpx;background:#fff2e7;font-size:21rpx;color:#80513d}.bottom-actions{display:flex;gap:14rpx;margin-top:18rpx}.bottom-actions button{flex:1}.bottom-actions .primary{color:#fff;background:#fa7770;border-color:#fa7770}.catalog-mask{position:fixed;inset:0;z-index:10;background:#0005}.catalog-panel{position:absolute;left:142rpx;right:18rpx;top:200rpx;max-height:70vh;padding:22rpx;overflow:auto;border-radius:20rpx;background:#fff;box-shadow:0 12rpx 50rpx #0004}.panel-head{display:flex;justify-content:space-between;margin-bottom:18rpx;font-size:28rpx;font-weight:700}.panel-head text:last-child{font-size:22rpx;color:#777}.catalog{display:grid;grid-template-columns:repeat(3,1fr);gap:14rpx}.pattern-card{min-height:170rpx;padding:10rpx;box-sizing:border-box;border:1rpx solid #eee;border-radius:14rpx;text-align:center;font-size:19rpx}.pattern-card image{width:78rpx;height:78rpx}.pattern-card text{display:block}.pattern-card text:nth-last-child(-n+2){color:#8b7770}.empty{grid-column:span 3;padding:36rpx;text-align:center;color:#888}.draft-list{margin-top:18rpx;padding:20rpx;border-radius:18rpx;background:#fff}.draft-title{display:block;font-weight:700}.draft-row{display:flex;align-items:center;justify-content:space-between;margin-top:14rpx;font-size:21rpx}.draft-row view{display:flex;gap:8rpx}.draft-row button{line-height:52rpx}
</style>
