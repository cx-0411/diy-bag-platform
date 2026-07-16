<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { onReady } from '@dcloudio/uni-app'

import { patternPixelSize, placementPixelPoint, pixelPointToPlacement } from '../../features/editor/domain/geometry'
import type { PatternPlacement, PixelSize } from '../../features/editor/domain/types'
import { useEditorStore } from '../../features/editor/stores/editor'

interface ZoneRect extends PixelSize {
  left: number
  top: number
}

interface TouchLikeEvent {
  touches: { length: number; [index: number]: { clientX: number; clientY: number } }
}

const editor = useEditorStore()
const zoneRect = ref<ZoneRect | null>(null)
const dragging = ref<{ placementId: string; offsetX: number; offsetY: number } | null>(null)

const selectedPattern = computed(() => {
  if (!editor.selectedPlacement) return null
  return editor.getPattern(editor.selectedPlacement.patternId)
})

const designSummary = computed(() =>
  editor.placements.map((placement) => ({
    id: placement.id,
    name: editor.getPattern(placement.patternId).name,
    xRatio: placement.xRatio.toFixed(4),
    yRatio: placement.yRatio.toFixed(4),
  })),
)

function measureZone(): void {
  nextTick(() => {
    uni
      .createSelectorQuery()
      .select('.embroidery-zone')
      .boundingClientRect((rect) => {
        if (!rect) return
        const box = rect as ZoneRect
        zoneRect.value = { left: box.left, top: box.top, width: box.width, height: box.height }
      })
      .exec()
  })
}

function styleForPlacement(placement: PatternPlacement): Record<string, string> {
  if (!zoneRect.value) return { visibility: 'hidden' }
  const pattern = editor.getPattern(placement.patternId)
  const point = placementPixelPoint(placement, zoneRect.value)
  const size = patternPixelSize(pattern, editor.embroideryArea, zoneRect.value)

  return {
    width: `${size.width}px`,
    height: `${size.height}px`,
    transform: `translate3d(${point.x}px, ${point.y}px, 0)`,
    backgroundColor: pattern.color,
  }
}

function choosePattern(patternId: string): void {
  if (editor.selectedPlacement) {
    editor.replaceSelected(patternId)
  } else {
    editor.addPattern(patternId)
  }
}

function selectCanvas(): void {
  editor.selectedPlacementId = null
}

function touchStart(placement: PatternPlacement, event: TouchLikeEvent): void {
  if (!zoneRect.value) return
  const touch = event.touches[0]
  if (!touch) return
  editor.selectPlacement(placement.id)
  const point = placementPixelPoint(placement, zoneRect.value)
  dragging.value = {
    placementId: placement.id,
    offsetX: touch.clientX - zoneRect.value.left - point.x,
    offsetY: touch.clientY - zoneRect.value.top - point.y,
  }
}

function touchMove(event: TouchLikeEvent): void {
  if (!dragging.value || !zoneRect.value) return
  const touch = event.touches[0]
  const placement = editor.placements.find((item) => item.id === dragging.value?.placementId)
  if (!touch || !placement) return
  const pattern = editor.getPattern(placement.patternId)
  editor.updatePlacement(
    pixelPointToPlacement(
      {
        x: touch.clientX - zoneRect.value.left - dragging.value.offsetX,
        y: touch.clientY - zoneRect.value.top - dragging.value.offsetY,
      },
      placement,
      pattern,
      editor.embroideryArea,
      zoneRect.value,
    ),
  )
}

function touchEnd(): void {
  dragging.value = null
}

onReady(measureZone)
</script>

<template>
  <view class="page">
    <view class="intro">
      <text class="eyebrow">第 2 阶段 · 技术验证</text>
      <text class="title">DIY 刺绣编辑器</text>
      <text class="subtitle">图案尺寸固定，以毫米换算显示；拖动时始终完整保留在刺绣区域内。</text>
    </view>

    <view class="bag-stage">
      <view class="bag-handle" />
      <view class="bag-body">
        <view
          class="embroidery-zone"
          @tap="selectCanvas"
          @touchmove.stop.prevent="touchMove"
          @touchend="touchEnd"
          @touchcancel="touchEnd"
        >
          <text class="zone-label">可刺绣区域 · 180 × 120 mm</text>
          <view
            v-for="placement in editor.placements"
            :key="placement.id"
            class="placed-pattern"
            :class="{ selected: placement.id === editor.selectedPlacementId }"
            :style="styleForPlacement(placement)"
            @tap.stop="editor.selectPlacement(placement.id)"
            @touchstart.stop="touchStart(placement, $event)"
          >
            <text class="pattern-symbol">{{ editor.getPattern(placement.patternId).symbol }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="panel">
      <view class="section-heading">
        <text class="section-title">选择图案</text>
        <text class="hint">{{ editor.selectedPlacement ? '点击图案将替换当前选中项' : '点击图案将添加到区域中心' }}</text>
      </view>
      <view class="pattern-list">
        <button v-for="pattern in editor.patternCatalog" :key="pattern.id" class="pattern-card" @tap="choosePattern(pattern.id)">
          <text class="catalog-symbol" :style="{ color: pattern.color }">{{ pattern.symbol }}</text>
          <text class="catalog-name">{{ pattern.name }}</text>
          <text class="catalog-meta">{{ pattern.width }} × {{ pattern.height }} mm · ¥{{ (pattern.priceCents / 100).toFixed(2) }}</text>
        </button>
      </view>
    </view>

    <view v-if="selectedPattern" class="selected-bar">
      <view>
        <text class="selected-title">已选：{{ selectedPattern.name }}</text>
        <text class="selected-meta">固定尺寸 {{ selectedPattern.width }} × {{ selectedPattern.height }} mm</text>
      </view>
      <button class="delete-button" @tap="editor.deleteSelected">删除</button>
    </view>

    <view class="debug-card">
      <text class="debug-title">设计数据预览（比例坐标）</text>
      <text v-if="designSummary.length === 0" class="debug-empty">尚未添加图案</text>
      <text v-for="item in designSummary" :key="item.id" class="debug-line">{{ item.name }} · x: {{ item.xRatio }}, y: {{ item.yRatio }}</text>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 32rpx 28rpx 72rpx; background: #f8f2eb; }
.intro { display: flex; flex-direction: column; gap: 12rpx; margin-bottom: 28rpx; }
.eyebrow { color: #9c624b; font-size: 23rpx; letter-spacing: 2rpx; }
.title { color: #2d2522; font-size: 48rpx; font-weight: 700; }
.subtitle { color: #776963; font-size: 26rpx; line-height: 1.6; }
.bag-stage { position: relative; display: flex; justify-content: center; padding-top: 52rpx; margin-bottom: 32rpx; }
.bag-handle { position: absolute; top: 0; width: 252rpx; height: 128rpx; border: 20rpx solid #a86d4a; border-bottom: 0; border-radius: 136rpx 136rpx 0 0; }
.bag-body { position: relative; z-index: 1; width: 670rpx; height: 540rpx; padding: 104rpx 70rpx; border: 2rpx solid #b47f5d; border-radius: 28rpx 28rpx 88rpx 88rpx; background: linear-gradient(135deg, #e5c2a4, #c98762); box-shadow: 0 18rpx 34rpx rgba(85, 49, 31, .18); }
.embroidery-zone { position: relative; width: 530rpx; height: 332rpx; overflow: hidden; border: 3rpx dashed rgba(102, 61, 43, .75); background: rgba(255, 250, 242, .32); touch-action: none; }
.zone-label { position: absolute; right: 10rpx; bottom: 8rpx; color: rgba(79, 45, 32, .65); font-size: 19rpx; pointer-events: none; }
.placed-pattern { position: absolute; left: 0; top: 0; display: flex; align-items: center; justify-content: center; border: 2rpx solid rgba(255,255,255,.58); border-radius: 14rpx; box-shadow: 0 4rpx 8rpx rgba(60, 30, 20, .18); touch-action: none; }
.placed-pattern.selected { outline: 4rpx solid #fff; outline-offset: 3rpx; }
.pattern-symbol { color: #fff; font-size: 40rpx; font-weight: 700; line-height: 1; }
.panel, .debug-card { padding: 28rpx; border-radius: 24rpx; background: #fff; box-shadow: 0 8rpx 26rpx rgba(81, 48, 31, .08); }
.section-heading { display: flex; flex-direction: column; gap: 7rpx; margin-bottom: 20rpx; }
.section-title, .debug-title { color: #332824; font-size: 30rpx; font-weight: 700; }
.hint, .selected-meta, .debug-empty, .debug-line { color: #81736c; font-size: 23rpx; }
.pattern-list { display: flex; gap: 16rpx; }
.pattern-card { flex: 1; padding: 18rpx 10rpx; border: 2rpx solid #eee2d8; border-radius: 16rpx; background: #fffaf6; line-height: 1.35; }
.catalog-symbol, .catalog-name, .catalog-meta { display: block; }
.catalog-symbol { margin-bottom: 6rpx; font-size: 42rpx; font-weight: 700; }
.catalog-name { color: #443630; font-size: 26rpx; font-weight: 700; }
.catalog-meta { color: #937e71; font-size: 19rpx; }
.selected-bar { display: flex; align-items: center; justify-content: space-between; margin-top: 24rpx; padding: 22rpx 26rpx; border-radius: 20rpx; background: #fff4e8; }
.selected-title { display: block; color: #50372c; font-size: 27rpx; font-weight: 700; }
.delete-button { margin: 0; padding: 0 20rpx; border: 1rpx solid #d97867; border-radius: 12rpx; background: #fff; color: #ba493d; font-size: 24rpx; }
.debug-card { display: flex; flex-direction: column; gap: 10rpx; margin-top: 24rpx; background: #342b27; }
.debug-title { color: #fff2e6; }
.debug-empty, .debug-line { color: #dccbbe; font-family: Consolas, monospace; font-size: 21rpx; }
</style>
