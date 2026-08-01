<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useEditorStore } from '../../features/editor/stores/editor'
import { catalogApi, type ApiCartItem } from '../../services/catalog-api'
const editor = useEditorStore(); const items = ref<ApiCartItem[]>([]); const loading = ref(false); const creating = ref<string | null>(null)
const price = (cents: number) => `¥${(cents / 100).toFixed(2)}`
const total = computed(() => items.value.reduce((sum, item) => sum + item.total_price_cents, 0))
async function load(): Promise<void> { loading.value = true; try { items.value = await catalogApi.cartItems(editor.clientKey()) } catch (e) { uni.showToast({ title: e instanceof Error ? e.message : '购物车加载失败', icon: 'none' }) } finally { loading.value = false } }
async function remove(item: ApiCartItem): Promise<void> { try { await catalogApi.deleteCartItem(item.id, editor.clientKey()); await load() } catch (e) { uni.showToast({ title: e instanceof Error ? e.message : '删除失败', icon: 'none' }) } }
async function checkout(item: ApiCartItem): Promise<void> { creating.value = item.id; try { await catalogApi.createOrder(item.design_id, editor.clientKey()); await catalogApi.deleteCartItem(item.id, editor.clientKey()); uni.showToast({ title: '模拟订单已创建', icon: 'success' }); uni.redirectTo({ url: '/pages/orders/index' }) } catch (e) { uni.showToast({ title: e instanceof Error ? e.message : '结算失败', icon: 'none' }) } finally { creating.value = null } }
onShow(() => { void load() })
</script>
<template><view class="page"><text class="title">购物车</text><view v-if="loading" class="state">加载中…</view><view v-else-if="!items.length" class="state">购物车还是空的</view><template v-else><view v-for="item in items" :key="item.id" class="card"><text>DIY 设计 {{ item.design_id.slice(0, 6) }}</text><text class="price">{{ price(item.total_price_cents) }}</text><view class="actions"><button @tap="remove(item)">删除</button><button class="primary" :loading="creating === item.id" @tap="checkout(item)">创建订单</button></view></view><view class="total">合计 <text>{{ price(total) }}</text></view></template></view></template>
<style scoped>.page{min-height:100vh;padding:28rpx;background:#f6f4f1}.title{display:block;font-size:42rpx;font-weight:700}.state{padding:80rpx;text-align:center;color:#8a7770}.card{display:flex;flex-direction:column;gap:15rpx;margin-top:18rpx;padding:22rpx;border-radius:18rpx;background:#fff}.price,.total text{color:#d75a49;font-weight:700}.actions{display:flex;gap:14rpx}.actions button{flex:1}.primary{color:#fff;background:#fa7770}.total{margin-top:20rpx;padding:20rpx;background:#fff;border-radius:16rpx;text-align:right}</style>
