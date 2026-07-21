<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type UploadFile } from 'element-plus'
import { categoryApi, fileApi, patternApi, uploadImage, type Pattern, type PatternCategory, type PatternPayload } from '../services/api'

const categories = ref<PatternCategory[]>([])
const patterns = ref<Pattern[]>([])
const loading = ref(false)
const categoryDialog = ref(false)
const patternDialog = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<string | null>(null)
const preview = ref('')
const categoryForm = reactive({ name: '', sort_order: 0 })
const form = reactive<PatternPayload>({ category_id: '', name: '', production_code: '', status: 'draft', image_asset_id: '', width_mm: 50, height_mm: 50, price_cents: 1200 })
const categoryName = computed(() => new Map(categories.value.map((item) => [item.id, item.name])))
const assetBaseUrl = 'http://localhost:8000'
async function load(): Promise<void> { loading.value = true; try { const [categoryRows, patternRows] = await Promise.all([categoryApi.list(), patternApi.list()]); categories.value = categoryRows; patterns.value = patternRows } catch (e) { ElMessage.error(e instanceof Error ? e.message : '加载失败') } finally { loading.value = false } }
function openCategory(): void { Object.assign(categoryForm, { name: '', sort_order: categories.value.length }); categoryDialog.value = true }
async function saveCategory(): Promise<void> { if (!categoryForm.name.trim()) { ElMessage.error('请输入分类名称'); return }; try { await categoryApi.create({ ...categoryForm, name: categoryForm.name.trim() }); ElMessage.success('分类已创建'); categoryDialog.value = false; await load() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } }
function openCreate(): void { editingId.value = null; preview.value = ''; Object.assign(form, { category_id: categories.value[0]?.id ?? '', name: '', production_code: '', status: 'draft', image_asset_id: '', width_mm: 50, height_mm: 50, price_cents: 1200 }); patternDialog.value = true }
async function openEdit(row: Pattern): Promise<void> { try { const versions = await patternApi.versions(row.id); const current = versions.at(-1); if (!current) { ElMessage.error('图案没有可用版本'); return }; editingId.value = row.id; Object.assign(form, { category_id: row.category_id, name: row.name, production_code: row.production_code, status: row.status, image_asset_id: current.image_asset_id, width_mm: current.width_mm, height_mm: current.height_mm, price_cents: current.price_cents }); const asset = await fileApi.get(current.image_asset_id); preview.value = `${assetBaseUrl}${asset.url}`; patternDialog.value = true } catch (e) { ElMessage.error(e instanceof Error ? e.message : '加载图案失败') } }
async function upload(file: File): Promise<void> { try { const asset = await uploadImage(file); form.image_asset_id = asset.id; preview.value = `${assetBaseUrl}${asset.url}`; ElMessage.success('透明图案图片上传成功') } catch (e) { ElMessage.error(e instanceof Error ? e.message : '上传失败') } }
function onFileChange(file: UploadFile): void { if (file.raw) void upload(file.raw) }
async function submit(): Promise<void> { if (!formRef.value || !(await formRef.value.validate().catch(() => false))) return; if (!form.category_id || !form.image_asset_id) { ElMessage.error('请选择分类并上传图案图片'); return }; try { editingId.value ? await patternApi.update(editingId.value, { ...form }) : await patternApi.create({ ...form }); ElMessage.success(editingId.value ? '图案已更新；尺寸、图片或价格变更会生成新版本' : '图案已创建'); patternDialog.value = false; await load() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } }
async function setStatus(row: Pattern, status: string): Promise<void> { try { const action = status === 'archived' ? '归档' : status === 'published' ? '上架' : '下架'; await ElMessageBox.confirm(`确认${action}“${row.name}”吗？`, '二次确认', { type: 'warning' }); const versions = await patternApi.versions(row.id); const current = versions.at(-1); if (!current) return; await patternApi.update(row.id, { category_id: row.category_id, name: row.name, production_code: row.production_code, status, image_asset_id: current.image_asset_id, width_mm: current.width_mm, height_mm: current.height_mm, price_cents: current.price_cents }); ElMessage.success(`${action}成功`); await load() } catch (e) { if (e !== 'cancel') ElMessage.error(e instanceof Error ? e.message : '操作失败') } }
onMounted(load)
</script>

<template>
  <section>
    <el-page-header content="图案管理" />
    <div class="toolbar"><el-button @click="openCategory">新增分类</el-button><el-button type="primary" :disabled="categories.length === 0" @click="openCreate">新增图案</el-button><el-button @click="load">刷新</el-button></div>
    <el-alert v-if="categories.length === 0" title="请先创建图案分类，才能新增图案。" type="info" show-icon :closable="false" />
    <el-table :data="patterns" v-loading="loading" class="table"><el-table-column prop="name" label="名称" /><el-table-column label="分类"><template #default="{ row }">{{ categoryName.get(row.category_id) ?? '—' }}</template></el-table-column><el-table-column prop="production_code" label="生产编号" /><el-table-column prop="status" label="状态" /><el-table-column label="操作" width="280"><template #default="{ row }"><el-button link type="primary" @click="openEdit(row)">编辑</el-button><el-button link type="success" @click="setStatus(row, 'published')">上架</el-button><el-button link type="warning" @click="setStatus(row, 'unpublished')">下架</el-button><el-button link type="danger" @click="setStatus(row, 'archived')">归档</el-button></template></el-table-column></el-table>
    <el-empty v-if="!loading && patterns.length === 0" description="暂无图案" />
  </section>
  <el-dialog v-model="categoryDialog" title="新增图案分类" width="440px"><el-form label-width="90px"><el-form-item label="分类名称"><el-input v-model="categoryForm.name" maxlength="100" /></el-form-item><el-form-item label="排序"><el-input-number v-model="categoryForm.sort_order" :min="0" /></el-form-item></el-form><template #footer><el-button @click="categoryDialog = false">取消</el-button><el-button type="primary" @click="saveCategory">保存</el-button></template></el-dialog>
  <el-dialog v-model="patternDialog" :title="editingId ? '编辑图案' : '新增图案'" width="620px"><el-form ref="formRef" :model="form" label-width="130px"><el-form-item label="图案分类" required><el-select v-model="form.category_id" placeholder="请选择"><el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item><el-form-item label="图案名称" required><el-input v-model="form.name" /></el-form-item><el-form-item label="生产编号" required><el-input v-model="form.production_code" /></el-form-item><el-form-item label="透明图案图片" required><el-upload accept="image/png,image/webp,image/svg+xml" :show-file-list="false" :auto-upload="false" :on-change="onFileChange"><el-button>选择并上传图片</el-button></el-upload><el-image v-if="preview" :src="preview" class="preview" fit="contain" /></el-form-item><el-form-item label="固定宽度" required><el-input-number v-model="form.width_mm" :min="1" /> mm</el-form-item><el-form-item label="固定高度" required><el-input-number v-model="form.height_mm" :min="1" /> mm</el-form-item><el-form-item label="固定价格" required><el-input-number v-model="form.price_cents" :min="0" /> 分</el-form-item><el-form-item label="尺寸规则"><el-alert title="消费者不能修改该图案尺寸。" type="warning" :closable="false" /></el-form-item></el-form><template #footer><el-button @click="patternDialog = false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template></el-dialog>
</template>

<style scoped>.toolbar { display:flex; gap:12px; margin:20px 0 }.table { margin-top:18px }.preview { display:block; margin-top:10px; width:160px; height:120px; border:1px solid var(--el-border-color) }</style>
