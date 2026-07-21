const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

export interface Bag { id: string; name: string; image_asset_id: string; width_mm: number; height_mm: number; base_price_cents: number; status: string }
export interface EmbroideryArea { id: string; bag_id: string; relative_x: number; relative_y: number; relative_width: number; relative_height: number; width_mm: number; height_mm: number }
export interface Asset { id: string; original_name: string; content_type: string; size_bytes: number; url: string }

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: { 'Content-Type': 'application/json', ...init.headers }, ...init })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `请求失败（${response.status}）`) }
  return response.json() as Promise<T>
}
export const bagApi = {
  list: () => request<Bag[]>('/bags'),
  get: (id: string) => request<Bag>(`/bags/${id}`),
  create: (data: Omit<Bag, 'id'>) => request<Bag>('/bags', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Omit<Bag, 'id'>) => request<Bag>(`/bags/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  setStatus: (id: string, status: string) => request<Bag>(`/bags/${id}/status?status=${status}`, { method: 'POST' }),
  area: (id: string) => request<EmbroideryArea>(`/bags/${id}/embroidery-area`),
  saveArea: (id: string, data: Omit<EmbroideryArea, 'id' | 'bag_id'>) => request<EmbroideryArea>(`/bags/${id}/embroidery-area`, { method: 'POST', body: JSON.stringify(data) }),
}
export async function uploadImage(file: File): Promise<Asset> {
  const data = new FormData(); data.append('file', file)
  const response = await fetch(`${API_BASE_URL}/files`, { method: 'POST', body: data })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `上传失败（${response.status}）`) }
  return response.json() as Promise<Asset>
}
