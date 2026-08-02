<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { playSaveCelebration } from '../../features/editor/services/save-celebration'
import { useEditorStore } from '../../features/editor/stores/editor'
import { catalogApi } from '../../services/catalog-api'

const editor = useEditorStore()
const loading = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)
const fireworksVisible = ref(false)
const celebratedPreviewUrl = ref('')
let fireworksTimer: ReturnType<typeof setTimeout> | undefined

const price = (cents: number) => `¥${(cents / 100).toFixed(2)}`
const serverTotal = computed(() => editor.savedDesign?.totalPriceCents ?? editor.totalPriceCents)
const fireworkParticles = Array.from({ length: 32 }, (_, index) => {
  const burst = index % 2
  const angle = (index * 137.5) * Math.PI / 180
  const distance = 78 + (index % 5) * 19
  return {
    id: index,
    originX: burst ? 72 : 28,
    originY: burst ? 34 : 56,
    deltaX: Math.round(Math.cos(angle) * distance),
    deltaY: Math.round(Math.sin(angle) * distance),
    delay: (index % 8) * 25,
    color: ['#ffd166', '#ff8fab', '#8ee3ef', '#ffffff'][index % 4],
  }
})

function absoluteAssetUrl(url: string): string { return url.startsWith('http') ? url : `http://localhost:8000${url}` }

async function loadPreview(): Promise<void> {
  if (!editor.savedDesign || previewLoading.value) return
  previewLoading.value = true
  try { previewUrl.value = absoluteAssetUrl((await catalogApi.previewDesign(editor.savedDesign.id, editor.clientKey())).url) }
  catch (error) { uni.showToast({ title: error instanceof Error ? error.message : '预览图生成失败', icon: 'none' }) }
  finally { previewLoading.value = false }
}

function onPreviewLoaded(): void {
  if (!previewUrl.value || celebratedPreviewUrl.value === previewUrl.value) return
  celebratedPreviewUrl.value = previewUrl.value
  fireworksVisible.value = true
  playSaveCelebration()
  if (fireworksTimer) clearTimeout(fireworksTimer)
  fireworksTimer = setTimeout(() => { fireworksVisible.value = false }, 1250)
}

function back(): void { uni.navigateBack({ fail: () => uni.redirectTo({ url: '/pages/editor/index' }) }) }
async function addCart(): Promise<void> {
  if (!editor.savedDesign) return
  loading.value = true
  try { await catalogApi.addCartItem(editor.savedDesign.id, editor.clientKey()); uni.showToast({ title: '已加入购物车', icon: 'success' }); uni.navigateTo({ url: '/pages/cart/index' }) }
  catch (error) { uni.showToast({ title: error instanceof Error ? error.message : '加入购物车失败', icon: 'none' }) }
  finally { loading.value = false }
}
async function createOrder(): Promise<void> {
  if (!editor.savedDesign) return
  loading.value = true
  try { await catalogApi.createOrder(editor.savedDesign.id, editor.clientKey()); uni.showToast({ title: '模拟订单已创建', icon: 'success' }); uni.redirectTo({ url: '/pages/orders/index' }) }
  catch (error) { uni.showToast({ title: error instanceof Error ? error.message : '创建订单失败', icon: 'none' }) }
  finally { loading.value = false }
}

onShow(() => { void loadPreview() })
onBeforeUnmount(() => { if (fireworksTimer) clearTimeout(fireworksTimer) })
</script>

<template>
  <view class="page">
    <text class="title">设计确认</text>
    <view v-if="!editor.catalogLoaded || !editor.savedDesign" class="empty"><text>没有可确认的已保存设计。</text><button @tap="back">返回编辑器</button></view>
    <template v-else>
      <view class="ok">设计已保存，后端已重新计算价格。</view>
      <view class="card preview-card">
        <view class="preview-head"><text class="sub">DIY 预览图</text><text>仅供确认 · 含水印</text></view>
        <view class="preview-stage">
          <image v-if="previewUrl" class="preview-image" :src="previewUrl" mode="aspectFit" @load="onPreviewLoaded" />
          <view v-if="fireworksVisible" class="fireworks" aria-hidden="true">
            <view v-for="particle in fireworkParticles" :key="particle.id" class="firework-particle" :style="{ left: `${particle.originX}%`, top: `${particle.originY}%`, background: particle.color, '--x': `${particle.deltaX}rpx`, '--y': `${particle.deltaY}rpx`, '--delay': `${particle.delay}ms` }" />
          </view>
          <view v-if="!previewUrl" class="preview-loading">{{ previewLoading ? '正在生成预览图…' : '预览图暂不可用' }}</view>
        </view>
      </view>
      <view class="card bag-card"><image :src="editor.bag.imageUrl" mode="aspectFit"/><text>{{ editor.bag.name }} · 基础价格 {{ price(editor.bag.basePriceCents) }}</text></view>
      <view class="card"><text class="sub">图案清单</text><view v-for="item in editor.placements" :key="item.id" class="line"><text>{{ editor.getPattern(item.patternId).name }}（固定 {{ editor.getPattern(item.patternId).width }} × {{ editor.getPattern(item.patternId).height }} mm，{{ item.rotationDegrees }}°）</text><text>{{ price(editor.getPattern(item.patternId).priceCents) }}</text></view><view class="line total"><text>后端确认总价</text><text>{{ price(serverTotal) }}</text></view></view>
      <view class="actions"><button @tap="back">继续编辑</button><button :loading="loading" @tap="addCart">加入购物车</button><button class="primary" :loading="loading" @tap="createOrder">立即创建订单</button></view>
    </template>
  </view>
</template>

<style scoped>
.page{min-height:100vh;padding:28rpx;background:#f6f4f1}.title{display:block;font-size:42rpx;font-weight:700}.empty{display:flex;min-height:50vh;align-items:center;justify-content:center;flex-direction:column;gap:20rpx}.ok{margin-top:18rpx;padding:18rpx;color:#4b852f;background:#f0f9eb;border-radius:14rpx}.card{margin-top:18rpx;padding:20rpx;background:#fff;border-radius:18rpx;display:flex;gap:16rpx;flex-direction:column}.bag-card image{width:220rpx;height:170rpx}.preview-head{display:flex;justify-content:space-between;align-items:center}.preview-head text:last-child{padding:5rpx 10rpx;border-radius:12rpx;background:#fff0e7;color:#a55d43;font-size:19rpx}.preview-stage{position:relative;width:100%;height:420rpx;overflow:hidden;border-radius:14rpx;background:#f7f3ef}.preview-image{width:100%;height:420rpx}.preview-loading{height:420rpx;display:flex;align-items:center;justify-content:center;color:#8a7770;font-size:23rpx}.fireworks{position:absolute;inset:0;overflow:hidden;pointer-events:none}.firework-particle{position:absolute;width:14rpx;height:14rpx;margin:-7rpx;border-radius:50%;opacity:0;box-shadow:0 0 12rpx currentColor;animation:firework-burst 980ms cubic-bezier(.15,.7,.25,1) var(--delay) forwards}@keyframes firework-burst{0%{opacity:0;transform:translate(0,0) scale(.15)}13%{opacity:1;transform:translate(0,0) scale(1.25)}100%{opacity:0;transform:translate(var(--x),var(--y)) scale(.08)}}.line{display:flex;justify-content:space-between;gap:14rpx;font-size:23rpx}.sub{font-weight:700}.total{padding-top:16rpx;color:#d75a49;font-size:28rpx;font-weight:700}.actions{display:flex;gap:12rpx;margin-top:22rpx}.actions button{flex:1;font-size:21rpx}.primary{color:#fff;background:#fa7770}
</style>
