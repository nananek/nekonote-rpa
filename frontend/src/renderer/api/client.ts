const BASE_URL = 'http://127.0.0.1:18080/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const apiClient = {
  health: () => request<{ status: string; version: string }>('/health'),
  nodeTypes: () => request<string[]>('/nodes/types'),
  validateFlow: (flow: unknown) =>
    request<{ valid: boolean; errors: string[] }>('/flow/validate', {
      method: 'POST',
      body: JSON.stringify(flow)
    })
}
