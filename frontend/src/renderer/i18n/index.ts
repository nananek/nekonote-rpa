import ja from './ja.json'

const messages: Record<string, string> = ja

export function t(key: string, params?: Record<string, string | number>): string {
  let text = messages[key] ?? key
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(`{${k}}`, String(v))
    }
  }
  return text
}
