const API_BASE_URL = 'http://localhost:8000/api'

export interface ApiArea { id: string; bag_id: string; relative_x: number; relative_y: number; relative_width: number; relative_height: number; width_mm: number; height_mm: number }
export interface ApiBag { id: string; name: string; image_url: string; width_mm: number; height_mm: number; base_price_cents: number; embroidery_area: ApiArea }
export interface ApiCategory { id: string; name: string; sort_order: number }
export interface ApiPattern { id: string; category_id: string; name: string; image_url: string; width_mm: number; height_mm: number; price_cents: number; pattern_version_id: string }
export interface ApiDesign { id: string; bag_id: string; total_price_cents: number; items: Array<{ id: string; pattern_version_id: string; center_x_ratio: number; center_y_ratio: number; rotation_degrees: number }> }

type RequestMethod = 'GET' | 'POST'
function request<T>(path: string, method: RequestMethod = 'GET', data?: object): Promise<T> {
  return new Promise((resolve, reject) => uni.request({ url: `${API_BASE_URL}${path}`, method, data, header: { 'content-type': 'application/json' }, success: (response) => { if (response.statusCode >= 200 && response.statusCode < 300) resolve(response.data as T); else { const body = response.data as { detail?: string }; reject(new Error(body.detail ?? `请求失败（${response.statusCode}）`)) } }, fail: () => reject(new Error('网络请求失败，请确认后端服务已启动')) }))
}
export const catalogApi = {
  bags: () => request<ApiBag[]>('/catalog/bags'),
  categories: () => request<ApiCategory[]>('/catalog/pattern-categories'),
  patterns: () => request<ApiPattern[]>('/catalog/patterns'),
  saveDesign: (data: { bag_id: string; items: Array<{ pattern_version_id: string; center_x_ratio: number; center_y_ratio: number; rotation_degrees: number }> }) => request<ApiDesign>('/designs', 'POST', data),
}
