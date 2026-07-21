<script setup lang="ts">function start(): void { uni.navigateTo({ url: '/pages/bags/index' }) }</script>
<template><view class="page"><text class="title">包包刺绣 DIY 商城</text><text>选择已上架包包，添加固定尺寸图案并保存设计。</text><button @tap="start">开始 DIY</button></view></template>
<style scoped>.page{padding:48rpx;display:flex;flex-direction:column;gap:24rpx}.title{font-size:44rpx;font-weight:700}button{color:#fff;background:#a86849}</style>
