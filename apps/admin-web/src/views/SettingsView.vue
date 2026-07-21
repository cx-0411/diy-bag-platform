<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { settingApi } from '../services/api'
const maxDrafts = ref(3); const saving = ref(false)
async function load(): Promise<void> { try { maxDrafts.value = (await settingApi.getDesignLimit()).max_drafts } catch (e) { ElMessage.error(e instanceof Error ? e.message : '加载失败') } }
async function save(): Promise<void> { saving.value = true; try { maxDrafts.value = (await settingApi.setDesignLimit(maxDrafts.value)).max_drafts; ElMessage.success('设计数量限制已保存') } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } finally { saving.value = false } }
onMounted(load)
</script>
<template><section><el-page-header content="系统设置" /><el-card class="card"><template #header>DIY 设计草稿限制</template><p>同一浏览器设备最多可保存的设计数量；当前无用户登录，因此按设备隔离。</p><el-form label-width="180px"><el-form-item label="最多保存设计数"><el-input-number v-model="maxDrafts" :min="1" :max="20" /> 个</el-form-item><el-button type="primary" :loading="saving" @click="save">保存设置</el-button></el-form></el-card></section></template>
<style scoped>.card{max-width:680px;margin-top:20px}p{color:#606266}</style>
