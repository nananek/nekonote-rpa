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
  data: { label: 'Data', color: '#10b981' },
  excel: { label: 'Excel/CSV', color: '#059669' },
  file: { label: 'File', color: '#0d9488' },
  http: { label: 'HTTP', color: '#0ea5e9' },
  db: { label: 'Database', color: '#6366f1' },
  mail: { label: 'Mail', color: '#ec4899' },
  dialog: { label: 'Dialog', color: '#f97316' },
  pdf: { label: 'PDF', color: '#dc2626' },
  ocr: { label: 'OCR', color: '#a855f7' },
  ai: { label: 'AI', color: '#7c3aed' },
  subflow: { label: 'Subflow', color: '#64748b' },
}

export const NODE_DEFS: NodeDef[] = [
  // ── Browser ──
  { type: 'browser.open', label: 'Open Browser', category: 'browser', color: '#3b82f6', icon: 'B',
    params: [
      { name: 'browser_type', label: 'Browser', type: 'select', default: 'chromium', options: [{ label: 'Chromium', value: 'chromium' }, { label: 'Firefox', value: 'firefox' }] },
      { name: 'headless', label: 'Headless', type: 'boolean', default: false }
    ], outputs: ['out'] },
  { type: 'browser.navigate', label: 'Navigate', category: 'browser', color: '#3b82f6', icon: 'N',
    params: [{ name: 'url', label: 'URL', type: 'string', placeholder: 'https://example.com' }], outputs: ['out'] },
  { type: 'browser.click', label: 'Click Element', category: 'browser', color: '#3b82f6', icon: 'C',
    params: [{ name: 'selector', label: 'Selector', type: 'string', placeholder: '#button' }], outputs: ['out'] },
  { type: 'browser.type', label: 'Type Text', category: 'browser', color: '#3b82f6', icon: 'T',
    params: [{ name: 'selector', label: 'Selector', type: 'string', placeholder: '#input' }, { name: 'text', label: 'Text', type: 'string' }], outputs: ['out'] },
  { type: 'browser.getText', label: 'Get Text', category: 'browser', color: '#3b82f6', icon: 'G',
    params: [{ name: 'selector', label: 'Selector', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'browser.wait', label: 'Wait Element', category: 'browser', color: '#3b82f6', icon: 'W',
    params: [{ name: 'selector', label: 'Selector', type: 'string' }, { name: 'timeout', label: 'Timeout (ms)', type: 'number', default: 30000 }], outputs: ['out'] },
  { type: 'browser.screenshot', label: 'Screenshot', category: 'browser', color: '#3b82f6', icon: 'S',
    params: [{ name: 'path', label: 'Save path', type: 'string', placeholder: 'screenshot.png' }], outputs: ['out'] },
  { type: 'browser.close', label: 'Close Browser', category: 'browser', color: '#3b82f6', icon: 'X', params: [], outputs: ['out'] },
  { type: 'browser.select', label: 'Select Dropdown', category: 'browser', color: '#3b82f6', icon: 'D',
    params: [{ name: 'selector', label: 'Selector', type: 'string' }, { name: 'value', label: 'Value', type: 'string' }], outputs: ['out'] },
  { type: 'browser.check', label: 'Check', category: 'browser', color: '#3b82f6', icon: 'V',
    params: [{ name: 'selector', label: 'Selector', type: 'string' }], outputs: ['out'] },
  { type: 'browser.scroll', label: 'Scroll', category: 'browser', color: '#3b82f6', icon: 'R',
    params: [{ name: 'direction', label: 'Direction', type: 'select', default: 'down', options: [{ label: 'Down', value: 'down' }, { label: 'Up', value: 'up' }] }, { name: 'amount', label: 'Amount (px)', type: 'number', default: 500 }], outputs: ['out'] },
  { type: 'browser.executeJs', label: 'Run JS', category: 'browser', color: '#3b82f6', icon: 'J',
    params: [{ name: 'expression', label: 'JavaScript', type: 'string', placeholder: 'return document.title' }], outputs: ['out'] },
  { type: 'browser.getTable', label: 'Get Table', category: 'browser', color: '#3b82f6', icon: 'T',
    params: [{ name: 'selector', label: 'Table selector', type: 'string', placeholder: 'table#data' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'browser.upload', label: 'Upload File', category: 'browser', color: '#3b82f6', icon: 'U',
    params: [{ name: 'selector', label: 'Selector', type: 'string' }, { name: 'file_path', label: 'File path', type: 'string' }], outputs: ['out'] },

  // ── Desktop ──
  { type: 'desktop.click', label: 'Click', category: 'desktop', color: '#8b5cf6', icon: 'C',
    params: [{ name: 'x', label: 'X', type: 'number' }, { name: 'y', label: 'Y', type: 'number' }, { name: 'image', label: 'Or image', type: 'string' }], outputs: ['out'] },
  { type: 'desktop.type', label: 'Type', category: 'desktop', color: '#8b5cf6', icon: 'T',
    params: [{ name: 'text', label: 'Text', type: 'string' }], outputs: ['out'] },
  { type: 'desktop.hotkey', label: 'Hotkey', category: 'desktop', color: '#8b5cf6', icon: 'H',
    params: [{ name: 'keys', label: 'Keys (comma-sep)', type: 'string', placeholder: 'ctrl,c' }], outputs: ['out'] },
  { type: 'desktop.press', label: 'Press Key', category: 'desktop', color: '#8b5cf6', icon: 'K',
    params: [{ name: 'key', label: 'Key', type: 'string', placeholder: 'enter' }], outputs: ['out'] },
  { type: 'desktop.screenshot', label: 'Screenshot', category: 'desktop', color: '#8b5cf6', icon: 'S',
    params: [{ name: 'path', label: 'Save path', type: 'string' }, { name: 'region', label: 'Region (x,y,w,h)', type: 'string' }], outputs: ['out'] },
  { type: 'desktop.findImage', label: 'Find Image', category: 'desktop', color: '#8b5cf6', icon: 'F',
    params: [{ name: 'template', label: 'Template', type: 'string' }, { name: 'confidence', label: 'Confidence', type: 'number', default: 0.8 }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'desktop.doubleClick', label: 'Double Click', category: 'desktop', color: '#8b5cf6', icon: 'D',
    params: [{ name: 'x', label: 'X', type: 'number' }, { name: 'y', label: 'Y', type: 'number' }], outputs: ['out'] },
  { type: 'desktop.rightClick', label: 'Right Click', category: 'desktop', color: '#8b5cf6', icon: 'R',
    params: [{ name: 'x', label: 'X', type: 'number' }, { name: 'y', label: 'Y', type: 'number' }], outputs: ['out'] },
  { type: 'desktop.drag', label: 'Drag', category: 'desktop', color: '#8b5cf6', icon: 'G',
    params: [{ name: 'from_x', label: 'From X', type: 'number' }, { name: 'from_y', label: 'From Y', type: 'number' }, { name: 'to_x', label: 'To X', type: 'number' }, { name: 'to_y', label: 'To Y', type: 'number' }], outputs: ['out'] },
  { type: 'desktop.scroll', label: 'Scroll', category: 'desktop', color: '#8b5cf6', icon: 'W',
    params: [{ name: 'direction', label: 'Direction', type: 'select', default: 'down', options: [{ label: 'Down', value: 'down' }, { label: 'Up', value: 'up' }, { label: 'Left', value: 'left' }, { label: 'Right', value: 'right' }] }, { name: 'clicks', label: 'Clicks', type: 'number', default: 3 }], outputs: ['out'] },
  { type: 'desktop.clickElement', label: 'Click (XPath)', category: 'desktop', color: '#8b5cf6', icon: 'X',
    params: [{ name: 'title', label: 'Window title', type: 'string' }, { name: 'xpath', label: 'XPath', type: 'string', placeholder: './/Button[@name="OK"]' }], outputs: ['out'] },
  { type: 'desktop.typeElement', label: 'Type (XPath)', category: 'desktop', color: '#8b5cf6', icon: 'E',
    params: [{ name: 'title', label: 'Window title', type: 'string' }, { name: 'xpath', label: 'XPath', type: 'string' }, { name: 'text', label: 'Text', type: 'string' }], outputs: ['out'] },

  // ── Control ──
  { type: 'control.if', label: 'If', category: 'control', color: '#f59e0b', icon: '?',
    params: [{ name: 'condition', label: 'Condition', type: 'string', placeholder: '{{ variables.x == 1 }}' }], outputs: ['true', 'false'] },
  { type: 'control.loop', label: 'Loop', category: 'control', color: '#f59e0b', icon: 'L',
    params: [{ name: 'count', label: 'Count', type: 'number', default: 10 }, { name: 'condition', label: 'While', type: 'string' }], outputs: ['loop', 'out'] },
  { type: 'control.forEach', label: 'For Each', category: 'control', color: '#f59e0b', icon: 'E',
    params: [{ name: 'list_variable', label: 'List variable', type: 'string' }, { name: 'item_variable', label: 'Item variable', type: 'string', default: 'item' }], outputs: ['loop', 'out'] },
  { type: 'control.tryCatch', label: 'Try / Catch', category: 'control', color: '#f59e0b', icon: '!', params: [], outputs: ['try', 'catch'] },
  { type: 'control.wait', label: 'Wait', category: 'control', color: '#f59e0b', icon: 'Z',
    params: [{ name: 'seconds', label: 'Seconds', type: 'number', default: 1 }], outputs: ['out'] },

  // ── Data ──
  { type: 'data.setVariable', label: 'Set Variable', category: 'data', color: '#10b981', icon: '=',
    params: [{ name: 'name', label: 'Name', type: 'string' }, { name: 'value', label: 'Value', type: 'string' }], outputs: ['out'] },
  { type: 'data.log', label: 'Log', category: 'data', color: '#10b981', icon: '>',
    params: [{ name: 'message', label: 'Message', type: 'string' }, { name: 'level', label: 'Level', type: 'select', default: 'info', options: [{ label: 'Info', value: 'info' }, { label: 'Warning', value: 'warning' }, { label: 'Error', value: 'error' }] }], outputs: ['out'] },
  { type: 'data.comment', label: 'Comment', category: 'data', color: '#10b981', icon: '#',
    params: [{ name: 'text', label: 'Comment', type: 'string' }], outputs: ['out'] },

  // ── Excel/CSV ──
  { type: 'excel.read', label: 'Read Excel', category: 'excel', color: '#059669', icon: 'R',
    params: [{ name: 'path', label: 'File path', type: 'string', placeholder: 'data.xlsx' }, { name: 'sheet', label: 'Sheet', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'excel.write', label: 'Write Excel', category: 'excel', color: '#059669', icon: 'W',
    params: [{ name: 'path', label: 'File path', type: 'string', placeholder: 'output.xlsx' }, { name: 'variable', label: 'Data variable', type: 'string' }, { name: 'sheet', label: 'Sheet', type: 'string', default: 'Sheet1' }], outputs: ['out'] },
  { type: 'excel.readCell', label: 'Read Cell', category: 'excel', color: '#059669', icon: 'C',
    params: [{ name: 'path', label: 'File', type: 'string' }, { name: 'cell', label: 'Cell', type: 'string', default: 'A1' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'excel.writeCell', label: 'Write Cell', category: 'excel', color: '#059669', icon: 'P',
    params: [{ name: 'path', label: 'File', type: 'string' }, { name: 'cell', label: 'Cell', type: 'string', default: 'A1' }, { name: 'value', label: 'Value', type: 'string' }], outputs: ['out'] },
  { type: 'excel.readCsv', label: 'Read CSV', category: 'excel', color: '#059669', icon: 'V',
    params: [{ name: 'path', label: 'File', type: 'string', placeholder: 'data.csv' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'excel.writeCsv', label: 'Write CSV', category: 'excel', color: '#059669', icon: 'S',
    params: [{ name: 'path', label: 'File', type: 'string' }, { name: 'variable', label: 'Data variable', type: 'string' }], outputs: ['out'] },

  // ── File ──
  { type: 'file.copy', label: 'Copy File', category: 'file', color: '#0d9488', icon: 'C',
    params: [{ name: 'src', label: 'Source', type: 'string' }, { name: 'dst', label: 'Destination', type: 'string' }], outputs: ['out'] },
  { type: 'file.move', label: 'Move File', category: 'file', color: '#0d9488', icon: 'M',
    params: [{ name: 'src', label: 'Source', type: 'string' }, { name: 'dst', label: 'Destination', type: 'string' }], outputs: ['out'] },
  { type: 'file.delete', label: 'Delete File', category: 'file', color: '#0d9488', icon: 'D',
    params: [{ name: 'path', label: 'Path', type: 'string' }], outputs: ['out'] },
  { type: 'file.readText', label: 'Read Text', category: 'file', color: '#0d9488', icon: 'R',
    params: [{ name: 'path', label: 'Path', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'file.writeText', label: 'Write Text', category: 'file', color: '#0d9488', icon: 'W',
    params: [{ name: 'path', label: 'Path', type: 'string' }, { name: 'content', label: 'Content', type: 'string' }], outputs: ['out'] },
  { type: 'file.listFiles', label: 'List Files', category: 'file', color: '#0d9488', icon: 'L',
    params: [{ name: 'directory', label: 'Directory', type: 'string' }, { name: 'pattern', label: 'Pattern', type: 'string', default: '*' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'file.zip', label: 'ZIP', category: 'file', color: '#0d9488', icon: 'Z',
    params: [{ name: 'archive', label: 'Archive path', type: 'string' }, { name: 'files', label: 'Files (JSON array)', type: 'string' }], outputs: ['out'] },
  { type: 'file.unzip', label: 'Unzip', category: 'file', color: '#0d9488', icon: 'U',
    params: [{ name: 'archive', label: 'Archive', type: 'string' }, { name: 'dest', label: 'Destination', type: 'string', default: '.' }], outputs: ['out'] },

  // ── HTTP ──
  { type: 'http.get', label: 'HTTP GET', category: 'http', color: '#0ea5e9', icon: 'G',
    params: [{ name: 'url', label: 'URL', type: 'string' }, { name: 'headers', label: 'Headers (JSON)', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'http.post', label: 'HTTP POST', category: 'http', color: '#0ea5e9', icon: 'P',
    params: [{ name: 'url', label: 'URL', type: 'string' }, { name: 'json', label: 'Body (JSON)', type: 'string' }, { name: 'headers', label: 'Headers (JSON)', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'http.download', label: 'Download', category: 'http', color: '#0ea5e9', icon: 'D',
    params: [{ name: 'url', label: 'URL', type: 'string' }, { name: 'save_to', label: 'Save to', type: 'string' }], outputs: ['out'] },

  // ── Database ──
  { type: 'db.connect', label: 'DB Connect', category: 'db', color: '#6366f1', icon: 'C',
    params: [{ name: 'driver', label: 'Driver', type: 'select', default: 'sqlite', options: [{ label: 'SQLite', value: 'sqlite' }, { label: 'PostgreSQL', value: 'postgresql' }, { label: 'MySQL', value: 'mysql' }] }, { name: 'database', label: 'Database', type: 'string' }, { name: 'host', label: 'Host', type: 'string', default: 'localhost' }], outputs: ['out'] },
  { type: 'db.query', label: 'DB Query', category: 'db', color: '#6366f1', icon: 'Q',
    params: [{ name: 'sql', label: 'SQL', type: 'string', placeholder: 'SELECT * FROM users' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'db.execute', label: 'DB Execute', category: 'db', color: '#6366f1', icon: 'E',
    params: [{ name: 'sql', label: 'SQL', type: 'string', placeholder: 'INSERT INTO ...' }], outputs: ['out'] },

  // ── Mail ──
  { type: 'mail.send', label: 'Send Email', category: 'mail', color: '#ec4899', icon: 'S',
    params: [{ name: 'to', label: 'To (comma-sep)', type: 'string' }, { name: 'subject', label: 'Subject', type: 'string' }, { name: 'body', label: 'Body', type: 'string' }, { name: 'smtp_server', label: 'SMTP Server', type: 'string', default: 'smtp.gmail.com' }], outputs: ['out'] },
  { type: 'mail.receive', label: 'Receive Email', category: 'mail', color: '#ec4899', icon: 'R',
    params: [{ name: 'imap_server', label: 'IMAP Server', type: 'string', default: 'imap.gmail.com' }, { name: 'folder', label: 'Folder', type: 'string', default: 'INBOX' }, { name: 'limit', label: 'Limit', type: 'number', default: 10 }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },

  // ── Dialog ──
  { type: 'dialog.message', label: 'Message Box', category: 'dialog', color: '#f97316', icon: 'M',
    params: [{ name: 'message', label: 'Message', type: 'string' }, { name: 'title', label: 'Title', type: 'string', default: 'Nekonote' }], outputs: ['out'] },
  { type: 'dialog.confirm', label: 'Confirm', category: 'dialog', color: '#f97316', icon: '?',
    params: [{ name: 'message', label: 'Message', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'dialog.input', label: 'Input', category: 'dialog', color: '#f97316', icon: 'I',
    params: [{ name: 'message', label: 'Message', type: 'string' }, { name: 'default', label: 'Default', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'dialog.openFile', label: 'Open File Dialog', category: 'dialog', color: '#f97316', icon: 'O',
    params: [{ name: 'filter', label: 'Filter', type: 'string', default: 'All Files (*.*)|*.*' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },

  // ── PDF ──
  { type: 'pdf.readText', label: 'Read PDF Text', category: 'pdf', color: '#dc2626', icon: 'T',
    params: [{ name: 'path', label: 'File', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'pdf.readTables', label: 'Read PDF Tables', category: 'pdf', color: '#dc2626', icon: 'A',
    params: [{ name: 'path', label: 'File', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },

  // ── OCR ──
  { type: 'ocr.read', label: 'OCR Read', category: 'ocr', color: '#a855f7', icon: 'O',
    params: [{ name: 'path', label: 'Image', type: 'string' }, { name: 'lang', label: 'Language', type: 'string', default: 'jpn+eng' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'ocr.readScreen', label: 'OCR Screen', category: 'ocr', color: '#a855f7', icon: 'S',
    params: [{ name: 'region', label: 'Region (x,y,w,h)', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },

  // ── AI ──
  { type: 'ai.generate', label: 'AI Generate', category: 'ai', color: '#7c3aed', icon: 'A',
    params: [{ name: 'prompt', label: 'Prompt', type: 'string' }, { name: 'model', label: 'Model', type: 'string', default: 'gpt-4o' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },
  { type: 'ai.generateJson', label: 'AI JSON', category: 'ai', color: '#7c3aed', icon: 'J',
    params: [{ name: 'prompt', label: 'Prompt', type: 'string' }, { name: 'schema', label: 'JSON Schema', type: 'string' }, { name: 'variable', label: 'Save to', type: 'string' }], outputs: ['out'] },

  // ── Subflow ──
  { type: 'subflow.call', label: 'Call Subflow', category: 'subflow', color: '#64748b', icon: 'F',
    params: [{ name: 'name', label: 'Subflow name', type: 'string' }, { name: 'inputs', label: 'Inputs (JSON)', type: 'string', default: '{}' }], outputs: ['out'] },
]

export function getNodeDef(type: string): NodeDef | undefined {
  return NODE_DEFS.find((d) => d.type === type)
}
