export interface ParamDef {
  name: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'select' | 'json'
  default?: unknown
  options?: { label: string; value: string }[]
  placeholder?: string
}

export interface NodeDef {
  type: string
  label: string
  category: string
  color: string
  icon: string
  params: ParamDef[]
  outputs: string[] // handle names, e.g. ['out'] or ['true','false']
}

export const NODE_CATEGORIES: Record<string, { label: string; color: string }> = {
  browser: { label: 'Browser', color: '#3b82f6' },
  desktop: { label: 'Desktop', color: '#8b5cf6' },
  control: { label: 'Control', color: '#f59e0b' },
  data: { label: 'Data', color: '#10b981' }
}

export const NODE_DEFS: NodeDef[] = [
  // Browser
  {
    type: 'browser.open',
    label: 'Open Browser',
    category: 'browser',
    color: '#3b82f6',
    icon: 'B',
    params: [
      { name: 'browser_type', label: 'Browser', type: 'select', default: 'chromium', options: [{ label: 'Chromium', value: 'chromium' }, { label: 'Firefox', value: 'firefox' }] },
      { name: 'headless', label: 'Headless', type: 'boolean', default: false }
    ],
    outputs: ['out']
  },
  {
    type: 'browser.navigate',
    label: 'Navigate',
    category: 'browser',
    color: '#3b82f6',
    icon: 'N',
    params: [
      { name: 'url', label: 'URL', type: 'string', placeholder: 'https://example.com' }
    ],
    outputs: ['out']
  },
  {
    type: 'browser.click',
    label: 'Click Element',
    category: 'browser',
    color: '#3b82f6',
    icon: 'C',
    params: [
      { name: 'selector', label: 'Selector', type: 'string', placeholder: '#button' }
    ],
    outputs: ['out']
  },
  {
    type: 'browser.type',
    label: 'Type Text',
    category: 'browser',
    color: '#3b82f6',
    icon: 'T',
    params: [
      { name: 'selector', label: 'Selector', type: 'string', placeholder: '#input' },
      { name: 'text', label: 'Text', type: 'string' }
    ],
    outputs: ['out']
  },
  {
    type: 'browser.getText',
    label: 'Get Text',
    category: 'browser',
    color: '#3b82f6',
    icon: 'G',
    params: [
      { name: 'selector', label: 'Selector', type: 'string' },
      { name: 'variable', label: 'Save to variable', type: 'string' }
    ],
    outputs: ['out']
  },
  {
    type: 'browser.wait',
    label: 'Wait for Element',
    category: 'browser',
    color: '#3b82f6',
    icon: 'W',
    params: [
      { name: 'selector', label: 'Selector', type: 'string' },
      { name: 'timeout', label: 'Timeout (ms)', type: 'number', default: 30000 }
    ],
    outputs: ['out']
  },
  {
    type: 'browser.screenshot',
    label: 'Screenshot',
    category: 'browser',
    color: '#3b82f6',
    icon: 'S',
    params: [
      { name: 'path', label: 'Save path', type: 'string', placeholder: 'screenshot.png' }
    ],
    outputs: ['out']
  },
  {
    type: 'browser.close',
    label: 'Close Browser',
    category: 'browser',
    color: '#3b82f6',
    icon: 'X',
    params: [],
    outputs: ['out']
  },

  // Desktop
  {
    type: 'desktop.click',
    label: 'Click',
    category: 'desktop',
    color: '#8b5cf6',
    icon: 'C',
    params: [
      { name: 'x', label: 'X', type: 'number' },
      { name: 'y', label: 'Y', type: 'number' },
      { name: 'image', label: 'Or match image', type: 'string', placeholder: 'path/to/image.png' }
    ],
    outputs: ['out']
  },
  {
    type: 'desktop.type',
    label: 'Type',
    category: 'desktop',
    color: '#8b5cf6',
    icon: 'T',
    params: [
      { name: 'text', label: 'Text', type: 'string' }
    ],
    outputs: ['out']
  },
  {
    type: 'desktop.hotkey',
    label: 'Hotkey',
    category: 'desktop',
    color: '#8b5cf6',
    icon: 'H',
    params: [
      { name: 'keys', label: 'Keys (comma-separated)', type: 'string', placeholder: 'ctrl,c' }
    ],
    outputs: ['out']
  },
  {
    type: 'desktop.screenshot',
    label: 'Screenshot',
    category: 'desktop',
    color: '#8b5cf6',
    icon: 'S',
    params: [
      { name: 'region', label: 'Region (x,y,w,h)', type: 'string', placeholder: '0,0,1920,1080' },
      { name: 'variable', label: 'Save to variable', type: 'string' }
    ],
    outputs: ['out']
  },
  {
    type: 'desktop.findImage',
    label: 'Find Image',
    category: 'desktop',
    color: '#8b5cf6',
    icon: 'F',
    params: [
      { name: 'template', label: 'Template image', type: 'string' },
      { name: 'confidence', label: 'Confidence', type: 'number', default: 0.8 },
      { name: 'variable', label: 'Save to variable', type: 'string' }
    ],
    outputs: ['out']
  },

  // Control
  {
    type: 'control.if',
    label: 'If',
    category: 'control',
    color: '#f59e0b',
    icon: '?',
    params: [
      { name: 'condition', label: 'Condition', type: 'string', placeholder: '{{ variables.x == 1 }}' }
    ],
    outputs: ['true', 'false']
  },
  {
    type: 'control.loop',
    label: 'Loop',
    category: 'control',
    color: '#f59e0b',
    icon: 'L',
    params: [
      { name: 'count', label: 'Count', type: 'number', default: 10 },
      { name: 'condition', label: 'While condition', type: 'string' }
    ],
    outputs: ['loop', 'out']
  },
  {
    type: 'control.forEach',
    label: 'For Each',
    category: 'control',
    color: '#f59e0b',
    icon: 'E',
    params: [
      { name: 'list_variable', label: 'List variable', type: 'string' },
      { name: 'item_variable', label: 'Item variable', type: 'string', default: 'item' }
    ],
    outputs: ['loop', 'out']
  },
  {
    type: 'control.tryCatch',
    label: 'Try / Catch',
    category: 'control',
    color: '#f59e0b',
    icon: '!',
    params: [],
    outputs: ['try', 'catch']
  },
  {
    type: 'control.wait',
    label: 'Wait',
    category: 'control',
    color: '#f59e0b',
    icon: 'Z',
    params: [
      { name: 'seconds', label: 'Seconds', type: 'number', default: 1 }
    ],
    outputs: ['out']
  },

  // Data
  {
    type: 'data.setVariable',
    label: 'Set Variable',
    category: 'data',
    color: '#10b981',
    icon: '=',
    params: [
      { name: 'name', label: 'Name', type: 'string' },
      { name: 'value', label: 'Value', type: 'string' }
    ],
    outputs: ['out']
  },
  {
    type: 'data.log',
    label: 'Log',
    category: 'data',
    color: '#10b981',
    icon: '>',
    params: [
      { name: 'message', label: 'Message', type: 'string' },
      { name: 'level', label: 'Level', type: 'select', default: 'info', options: [{ label: 'Info', value: 'info' }, { label: 'Warning', value: 'warning' }, { label: 'Error', value: 'error' }] }
    ],
    outputs: ['out']
  },
  {
    type: 'data.comment',
    label: 'Comment',
    category: 'data',
    color: '#10b981',
    icon: '#',
    params: [
      { name: 'text', label: 'Comment', type: 'string' }
    ],
    outputs: ['out']
  }
]

export function getNodeDef(type: string): NodeDef | undefined {
  return NODE_DEFS.find((d) => d.type === type)
}
