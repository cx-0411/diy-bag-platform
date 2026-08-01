<script setup lang="ts">
function start(): void {
  uni.navigateTo({ url: '/pages/editor/index' })
}
</script>

<template>
  <view class="page">
    <view class="hero-card">
      <view class="art" aria-hidden="true">
        <view class="handle" />
        <view class="bag-shape"><view class="stitch" /><view class="flower">✿</view></view>
        <view class="dot dot-a" /><view class="dot dot-b" />
      </view>
      <text class="title">把喜欢，绣在包包上</text>
      <text class="subtitle">选择包包、拼贴图案，亲手完成一款只属于你的日常作品。</text>
      <button class="start-button" @tap="start">点击设计你的第一款包包 <text>→</text></button>
    </view>
  </view>
</template>

<style scoped>
.page{min-height:100vh;box-sizing:border-box;padding:78rpx 34rpx 44rpx;background:linear-gradient(160deg,#fffaf6 0%,#f6ede5 100%);color:#332927}
.hero-card{position:relative;overflow:hidden;min-height:820rpx;padding:42rpx 42rpx 46rpx;box-sizing:border-box;border:1rpx solid #fff;border-radius:40rpx;background:linear-gradient(145deg,#fffefd,#fff5ee);box-shadow:0 22rpx 60rpx rgba(122,77,51,.13);display:flex;flex-direction:column;align-items:flex-start}
.art{position:relative;width:100%;height:410rpx;margin:0 0 26rpx;display:flex;align-items:flex-end;justify-content:center}.handle{position:absolute;top:51rpx;width:142rpx;height:112rpx;border:16rpx solid #a86645;border-bottom:0;border-radius:76rpx 76rpx 0 0}.bag-shape{position:relative;width:300rpx;height:247rpx;border:8rpx solid #b77350;border-radius:14rpx 14rpx 50rpx 50rpx;background:linear-gradient(145deg,#e6b28c,#d79063);box-shadow:inset 0 0 0 8rpx #efc3a2;transform:skewY(2deg)}.stitch{position:absolute;left:32rpx;right:32rpx;top:48rpx;border-top:3rpx dashed rgba(109,61,41,.55)}.flower{position:absolute;right:44rpx;bottom:39rpx;color:#fff4dc;font-size:74rpx;transform:rotate(-16deg)}.dot{position:absolute;border-radius:50%;background:#f4b38f}.dot-a{width:26rpx;height:26rpx;left:42rpx;top:130rpx}.dot-b{width:18rpx;height:18rpx;right:54rpx;top:90rpx;background:#b9d6b3}
.title{font-size:56rpx;font-weight:800;line-height:1.25;letter-spacing:1rpx}.subtitle{margin-top:22rpx;color:#806c64;font-size:27rpx;line-height:1.75}.start-button{width:100%;margin:50rpx 0 0;border:0;border-radius:18rpx;background:#b36d4b;color:#fff;font-size:29rpx;font-weight:700;line-height:96rpx;box-shadow:0 12rpx 22rpx rgba(160,91,57,.25)}.start-button text{margin-left:12rpx;font-size:34rpx}
</style>
