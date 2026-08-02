const API_BASE_URL = 'http://localhost:8000/api'

export interface ApiArea { id: string; bag_id: string; relative_x: number; relative_y: number; relative_width: number; relative_height: number; width_mm: number; height_mm: number }
export interface ApiBag { id: string; name: string; image_url: string; width_mm: number; height_mm: number; base_price_cents: number; embroidery_area: ApiArea }
export interface ApiCategory { id: string; name: string; sort_order: number; icon: string; description: string }
export interface ApiPattern { id: string; category_id: string; name: string; image_url: string; width_mm: number; height_mm: number; price_cents: number; pattern_version_id: string }
export interface ApiDesign { id: string; bag_id: string; total_price_cents: number; items: Array<{ id: string; pattern_version_id: string; center_x_ratio: number; center_y_ratio: number; rotation_degrees: number; z_index: number }> }
export interface ApiAsset { id: string; original_name: string; content_type: string; size_bytes: number; url: string }

type RequestMethod = 'GET' | 'POST' | 'DELETE'
function errorMessage(detail: unknown, statusCode: number): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string' ? item.msg : '').filter(Boolean)
    if (messages.length) return `请求参数有误：${messages.join('；')}`
  }
  return `请求失败（${statusCode}）`
}
function request<T>(path: string, method: RequestMethod = 'GET', data?: object): Promise<T> {
  return new Promise((resolve, reject) => uni.request({ url: `${API_BASE_URL}${path}`, method, data, header: { 'content-type': 'application/json' }, success: (response) => { if (response.statusCode >= 200 && response.statusCode < 300) resolve(response.data as T); else { const body = response.data as { detail?: unknown }; reject(new Error(errorMessage(body.detail, response.statusCode))) } }, fail: () => reject(new Error('网络请求失败，请确认后端服务已启动')) }))
}
export const catalogApi = {
  bags: () => request<ApiBag[]>('/catalog/bags'),
  categories: () => request<ApiCategory[]>('/catalog/pattern-categories'),
  patterns: () => request<ApiPattern[]>('/catalog/patterns'),
  limit: () => request<{ max_drafts: number }>('/settings/design-limit'),
  saveDesign: (data: { bag_id: string; client_key: string; items: Array<{ pattern_version_id: string; center_x_ratio: number; center_y_ratio: number; rotation_degrees: number; z_index: number }> }) => request<ApiDesign>('/designs', 'POST', data),
  designs: (clientKey: string) => request<ApiDesign[]>(`/designs?client_key=${encodeURIComponent(clientKey)}`),
  deleteDesign: (id: string, clientKey: string) => request<void>(`/designs/${id}?client_key=${encodeURIComponent(clientKey)}`, 'DELETE'),
  previewDesign: (id: string, clientKey: string) => request<ApiAsset>(`/designs/${id}/preview?client_key=${encodeURIComponent(clientKey)}`, 'POST'),
  createOrder: (designId: string, clientKey: string) => request<ApiOrder>('/orders', 'POST', { design_id: designId, client_key: clientKey }),
  orders: (clientKey: string) => request<ApiOrder[]>(`/orders?client_key=${encodeURIComponent(clientKey)}`),
  mockPay: (orderId: string, clientKey: string) => request<ApiOrder>(`/orders/${orderId}/mock-pay?client_key=${encodeURIComponent(clientKey)}`, 'POST'),
  addCartItem: (designId: string, clientKey: string) => request<ApiCartItem>('/cart-items', 'POST', { design_id: designId, client_key: clientKey }),
  cartItems: (clientKey: string) => request<ApiCartItem[]>(`/cart-items?client_key=${encodeURIComponent(clientKey)}`),
  deleteCartItem: (id: string, clientKey: string) => request<void>(`/cart-items/${id}?client_key=${encodeURIComponent(clientKey)}`, 'DELETE'),
}
export interface ApiOrder { id: string; order_no: string; design_id: string; status: string; total_price_cents: number; created_at: string; paid_at: string | null }
export interface ApiCartItem { id: string; design_id: string; created_at: string; total_price_cents: number }
