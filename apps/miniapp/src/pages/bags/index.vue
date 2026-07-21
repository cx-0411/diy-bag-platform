<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import type { BagDefinition } from '../../features/editor/domain/types'
import { useEditorStore } from '../../features/editor/stores/editor'

const editor = useEditorStore()
const bags = ref<BagDefinition[]>([])
async function load(): Promise<void> { bags.value = await editor.loadCatalog() }
async function choose(bag: BagDefinition): Promise<void> { await editor.loadCatalog(bag.id); uni.navigateTo({ url: '/pages/editor/index' }) }
onShow(() => { void load() })
</script>
<template>
  <view class="page"><text class="title">选择包包</text><text class="subtitle">仅显示已上架且已配置刺绣区域的包包</text><view v-if="editor.loadingCatalog" class="state">正在加载…</view><view v-else-if="editor.catalogError" class="state error">{{ editor.catalogError }}。请先在后台完成图片、区域配置并上架。</view><view v-else class="list"><view v-for="bag in bags" :key="bag.id" class="card" @tap="choose(bag)"><image :src="bag.imageUrl" mode="aspectFit"/><view><text class="name">{{ bag.name }}</text><text>真实尺寸 {{ bag.width }} × {{ bag.height }} mm</text><text>基础价格 ¥{{ (bag.basePriceCents / 100).toFixed(2) }}</text><text>刺绣区域 {{ bag.embroideryArea.width }} × {{ bag.embroideryArea.height }} mm</text></view></view></view><button @tap="load">刷新列表</button></view>
</template>
<style scoped>.page{min-height:100vh;padding:32rpx;background:#f8f2eb}.title{display:block;font-size:42rpx;font-weight:700}.subtitle,.state{display:block;margin:12rpx 0 24rpx;color:#75665f;font-size:24rpx}.error{color:#c45656}.list{display:flex;flex-direction:column;gap:18rpx}.card{display:flex;gap:20rpx;padding:20rpx;background:#fff;border-radius:20rpx;box-shadow:0 6rpx 20rpx #754f3220}.card image{width:210rpx;height:180rpx}.card view{display:flex;flex:1;flex-direction:column;gap:10rpx;font-size:23rpx;color:#75665f}.card .name{font-size:31rpx;font-weight:700;color:#392b26}button{margin-top:28rpx;color:#fff;background:#a86849}</style>
