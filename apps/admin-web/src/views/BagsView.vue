<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { bagApi, fileApi, uploadImage, type Bag } from '../services/api'

const assetBaseUrl = 'http://localhost:8000'
const bags = ref<Bag[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const areaVisible = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<string | null>(null)
const selectedBag = ref<Bag | null>(null)
const imagePreview = ref('')
const uploadProgress = ref(0)
const form = reactive({ name: '', image_asset_id: '', width_mm: 280, height_mm: 220, base_price_cents: 15900, status: 'draft' })
const area = reactive({ relative_x: 0.2, relative_y: 0.2, relative_width: 0.6, relative_height: 0.45, width_mm: 160, height_mm: 100 })
const drag = reactive({ mode: '' as '' | 'move' | 'resize', startX: 0, startY: 0, startLeft: 0, startTop: 0, startWidth: 0, startHeight: 0, canvasWidth: 1, canvasHeight: 1 })
const rules: FormRules = {
  name: [{ required: true, message: '请输入包包名称', trigger: 'blur' }],
  image_asset_id: [{ required: true, message: '请先上传包包图片', trigger: 'change' }],
  width_mm: [{ required: true, type: 'number', min: 1, message: '宽度必须大于 0', trigger: 'blur' }],
  height_mm: [{ required: true, type: 'number', min: 1, message: '高度必须大于 0', trigger: 'blur' }],
}
async function load(): Promise<void> { loading.value = true; try { bags.value = await bagApi.list() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '加载失败') } finally { loading.value = false } }
function openCreate(): void { editingId.value = null; imagePreview.value = ''; Object.assign(form, { name: '', image_asset_id: '', width_mm: 280, height_mm: 220, base_price_cents: 15900, status: 'draft' }); dialogVisible.value = true }
async function openEdit(row: Bag): Promise<void> { editingId.value = row.id; Object.assign(form, row); try { const asset = await fileApi.get(row.image_asset_id); imagePreview.value = `${assetBaseUrl}${asset.url}` } catch { imagePreview.value = '' }; dialogVisible.value = true }
async function upload(file: File): Promise<void> { uploadProgress.value = 10; try { const asset = await uploadImage(file); form.image_asset_id = asset.id; imagePreview.value = `${assetBaseUrl}${asset.url}`; uploadProgress.value = 100; ElMessage.success('图片上传成功') } catch (e) { uploadProgress.value = 0; ElMessage.error(e instanceof Error ? e.message : '上传失败') } }
function onFileChange(file: UploadFile): void { if (file.raw) void upload(file.raw) }
async function submit(): Promise<void> { if (!formRef.value || !(await formRef.value.validate().catch(() => false))) return; try { const payload = { ...form }; editingId.value ? await bagApi.update(editingId.value, payload) : await bagApi.create(payload); ElMessage.success('保存成功'); dialogVisible.value = false; await load() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } }
async function changeStatus(row: Bag, status: string): Promise<void> { const action = status === 'archived' ? '归档' : status === 'published' ? '上架' : '下架'; try { await ElMessageBox.confirm(`确认${action}“${row.name}”吗？`, '二次确认', { type: 'warning' }); await bagApi.setStatus(row.id, status); ElMessage.success(`${action}成功`); await load() } catch (e) { if (e !== 'cancel') ElMessage.error(e instanceof Error ? e.message : '操作失败') } }
async function openArea(row: Bag): Promise<void> { selectedBag.value = row; try { const [asset, saved] = await Promise.all([fileApi.get(row.image_asset_id), bagApi.area(row.id).catch(() => null)]); imagePreview.value = `${assetBaseUrl}${asset.url}`; if (saved) Object.assign(area, saved); else Object.assign(area, { relative_x: 0.2, relative_y: 0.2, relative_width: 0.6, relative_height: 0.45, width_mm: Math.round(row.width_mm * 0.6), height_mm: Math.round(row.height_mm * 0.45) }); areaVisible.value = true } catch (e) { ElMessage.error(e instanceof Error ? e.message : '无法加载包包图片') } }
function clampArea(): void { area.relative_width = Math.min(1, Math.max(0.01, area.relative_width)); area.relative_height = Math.min(1, Math.max(0.01, area.relative_height)); area.relative_x = Math.min(1 - area.relative_width, Math.max(0, area.relative_x)); area.relative_y = Math.min(1 - area.relative_height, Math.max(0, area.relative_y)) }
function beginDrag(event: PointerEvent, mode: 'move' | 'resize'): void { const canvas = (event.currentTarget as HTMLElement).closest('.area-editor'); if (!canvas) return; const bounds = canvas.getBoundingClientRect(); Object.assign(drag, { mode, startX: event.clientX, startY: event.clientY, startLeft: area.relative_x, startTop: area.relative_y, startWidth: area.relative_width, startHeight: area.relative_height, canvasWidth: bounds.width, canvasHeight: bounds.height }); window.addEventListener('pointermove', moveArea); window.addEventListener('pointerup', endDrag, { once: true }) }
function moveArea(event: PointerEvent): void { if (!drag.mode) return; const dx = (event.clientX - drag.startX) / drag.canvasWidth; const dy = (event.clientY - drag.startY) / drag.canvasHeight; if (drag.mode === 'move') { area.relative_x = drag.startLeft + dx; area.relative_y = drag.startTop + dy } else { area.relative_width = drag.startWidth + dx; area.relative_height = drag.startHeight + dy }; clampArea() }
function endDrag(): void { drag.mode = ''; window.removeEventListener('pointermove', moveArea) }
async function saveArea(): Promise<void> { if (!selectedBag.value || area.width_mm < 1 || area.height_mm < 1) { ElMessage.error('请填写大于 0 的实际毫米尺寸'); return }; clampArea(); try { await bagApi.saveArea(selectedBag.value.id, { ...area }); ElMessage.success('刺绣区域已按比例坐标保存'); areaVisible.value = false } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } }
onMounted(load)
</script>

<template>
  <section>
    <el-page-header content="包包管理" />
    <div class="toolbar"><el-button type="primary" @click="openCreate">新增包包</el-button><el-button @click="load">刷新</el-button></div>
    <el-table :data="bags" v-loading="loading">
      <el-table-column prop="name" label="名称" />
      <el-table-column label="真实尺寸"><template #default="{ row }">{{ row.width_mm }} × {{ row.height_mm }} mm</template></el-table-column>
      <el-table-column label="基础价格"><template #default="{ row }">¥{{ (row.base_price_cents / 100).toFixed(2) }}</template></el-table-column>
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="350"><template #default="{ row }"><el-button link type="primary" @click="openEdit(row)">编辑</el-button><el-button link @click="openArea(row)">刺绣区域</el-button><el-button link type="success" @click="changeStatus(row, 'published')">上架</el-button><el-button link type="warning" @click="changeStatus(row, 'unpublished')">下架</el-button><el-button link type="danger" @click="changeStatus(row, 'archived')">归档</el-button></template></el-table-column>
    </el-table>
    <el-empty v-if="!loading && bags.length === 0" description="暂无包包，请先上传图片并新增包包" />
  </section>
  <el-dialog v-model="dialogVisible" :title="editingId ? '编辑包包' : '新增包包'" width="580px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="包包图片" prop="image_asset_id"><el-upload accept="image/*" :show-file-list="false" :auto-upload="false" :on-change="onFileChange"><el-button>选择并上传图片</el-button></el-upload><el-progress v-if="uploadProgress" :percentage="uploadProgress" /><el-image v-if="imagePreview" :src="imagePreview" class="preview" fit="contain" /></el-form-item>
      <el-form-item label="真实宽度" prop="width_mm"><el-input-number v-model="form.width_mm" :min="1" /> mm</el-form-item><el-form-item label="真实高度" prop="height_mm"><el-input-number v-model="form.height_mm" :min="1" /> mm</el-form-item><el-form-item label="基础价格"><el-input-number v-model="form.base_price_cents" :min="0" /> 分</el-form-item>
    </el-form><template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
  </el-dialog>
  <el-dialog v-model="areaVisible" title="配置矩形刺绣区域" width="760px">
    <p class="hint">矩形保存为相对于原图的比例坐标，不保存电脑屏幕像素。拖动或输入比例后，都会限制在图片内。</p>
    <div class="area-editor" :style="{ backgroundImage: `url(${imagePreview})` }"><div class="area-box" :style="{ left: `${area.relative_x * 100}%`, top: `${area.relative_y * 100}%`, width: `${area.relative_width * 100}%`, height: `${area.relative_height * 100}%` }" @pointerdown.stop="beginDrag($event, 'move')"><span class="resize-handle" @pointerdown.stop="beginDrag($event, 'resize')" /></div></div>
    <el-form label-width="140px" class="area-form"><el-form-item label="左上 X 比例"><el-input-number v-model="area.relative_x" :min="0" :max="1 - area.relative_width" :step="0.01" @change="clampArea" /></el-form-item><el-form-item label="左上 Y 比例"><el-input-number v-model="area.relative_y" :min="0" :max="1 - area.relative_height" :step="0.01" @change="clampArea" /></el-form-item><el-form-item label="区域宽比例"><el-input-number v-model="area.relative_width" :min="0.01" :max="1" :step="0.01" @change="clampArea" /></el-form-item><el-form-item label="区域高比例"><el-input-number v-model="area.relative_height" :min="0.01" :max="1" :step="0.01" @change="clampArea" /></el-form-item><el-form-item label="实际宽度"><el-input-number v-model="area.width_mm" :min="1" /> mm</el-form-item><el-form-item label="实际高度"><el-input-number v-model="area.height_mm" :min="1" /> mm</el-form-item></el-form>
    <template #footer><el-button @click="areaVisible = false">取消</el-button><el-button type="primary" @click="saveArea">保存区域</el-button></template>
  </el-dialog>
</template>

<style scoped>
.toolbar { display:flex; gap:12px; margin:20px 0 }.preview { display:block; width:180px; height:120px; margin-top:10px; border:1px solid var(--el-border-color) }.hint { color:#606266; font-size:13px }.area-editor { position:relative; width:100%; max-width:680px; aspect-ratio: 4 / 3; background:#f5f7fa center / contain no-repeat; border:1px solid #dcdfe6; touch-action:none }.area-box { position:absolute; box-sizing:border-box; border:2px solid #409eff; background:rgba(64,158,255,.2); cursor:move; touch-action:none }.resize-handle { position:absolute; width:14px; height:14px; right:-7px; bottom:-7px; background:#409eff; border-radius:2px; cursor:nwse-resize }.area-form { margin-top:18px; display:grid; grid-template-columns:1fr 1fr }
</style>
