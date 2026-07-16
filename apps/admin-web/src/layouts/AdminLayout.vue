<template>
  <el-container class="layout">
    <el-aside width="220px">
      <h1>刺绣 DIY 管理台</h1>
      <el-menu router :default-active="$route.path">
        <el-menu-item index="/bags">包包管理</el-menu-item>
        <el-menu-item index="/patterns">图案管理</el-menu-item>
        <el-menu-item index="/orders">订单管理</el-menu-item>
      </el-menu>
    </el-aside>
    <el-main><router-view /></el-main>
  </el-container>
</template>
