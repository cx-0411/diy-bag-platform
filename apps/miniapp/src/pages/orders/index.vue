<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useEditorStore } from '../../features/editor/stores/editor'
import { catalogApi, type ApiOrder } from '../../services/catalog-api'
const editor = useEditorStore(); const orders = ref<ApiOrder[]>([]); const loading = ref(false); const price = (cents: number) => `¥${(cents / 100).toFixed(2)}`
const labels: Record<string, string> = { PENDING_PAYMENT: '待付款', PAID: '已付款', TO_PRODUCE: '待制作', PRODUCING: '制作中', SHIPPED: '已发货', COMPLETED: '已完成', CANCELLED: '已取消' }
async function load(): Promise<void> { loading.value = true; try { orders.value = await catalogApi.orders(editor.clientKey()) } catch (e) { uni.showToast({ title: e instanceof Error ? e.message : '订单加载失败', icon: 'none' }) } finally { loading.value = false } }
async function pay(order: ApiOrder): Promise<void> { try { await catalogApi.mockPay(order.id, editor.clientKey()); uni.showToast({ title: '模拟付款成功', icon: 'success' }); await load() } catch (e) { uni.showToast({ title: e instanceof Error ? e.message : '付款失败', icon: 'none' }) } }
onShow(() => { void load() })
</script>
<template><view class="page"><text class="title">我的模拟订单</text><view v-if="loading" class="state">加载中…</view><view v-else-if="!orders.length" class="state">还没有订单</view><view v-else v-for="order in orders" :key="order.id" class="card"><text class="number">{{ order.order_no }}</text><view class="line"><text>{{ labels[order.status] }}</text><text>{{ price(order.total_price_cents) }}</text></view><button v-if="order.status === 'PENDING_PAYMENT'" class="pay" @tap="pay(order)">模拟付款</button></view></view></template>
<style scoped>.page{min-height:100vh;padding:28rpx;background:#f6f4f1}.title{display:block;font-size:42rpx;font-weight:700}.state{padding:80rpx;text-align:center;color:#8a7770}.card{margin-top:18rpx;padding:22rpx;border-radius:18rpx;background:#fff}.number{font-weight:700}.line{display:flex;justify-content:space-between;margin-top:16rpx}.pay{margin-top:18rpx;color:#fff;background:#fa7770}</style>
