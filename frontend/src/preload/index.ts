import { contextBridge, ipcRenderer } from 'electron'

export const api = {
  openFile: (): Promise<{ filePath: string; content: string } | null> =>
    ipcRenderer.invoke('dialog:openFile'),
  saveFile: (content: string, currentPath?: string): Promise<string | null> =>
    ipcRenderer.invoke('dialog:saveFile', content, currentPath),

  // Auto-update
  updateCheck: (): Promise<unknown> => ipcRenderer.invoke('update:check'),
  updateDownload: (): Promise<unknown> => ipcRenderer.invoke('update:download'),
  updateInstall: (): void => ipcRenderer.send('update:install'),
  onUpdateEvent: (callback: (event: string, payload?: unknown) => void): (() => void) => {
    const channels = ['update:checking', 'update:available', 'update:none', 'update:progress', 'update:downloaded', 'update:error']
    const handlers = channels.map((ch) => {
      const h = (_: unknown, data: unknown): void => callback(ch, data)
      ipcRenderer.on(ch, h)
      return { ch, h }
    })
    return () => handlers.forEach(({ ch, h }) => ipcRenderer.removeListener(ch, h))
  },

  // Record bar
  showRecordBar: (): void => ipcRenderer.send('recordbar:show'),
  hideRecordBar: (): void => ipcRenderer.send('recordbar:hide'),
  onRecordBarAction: (callback: (action: string) => void): (() => void) => {
    const handler = (_: unknown, action: string): void => callback(action)
    ipcRenderer.on('recordbar:action', handler)
    return () => ipcRenderer.removeListener('recordbar:action', handler)
  },

  // Backend communication via stdio
  sendToBackend: (msg: unknown): void => {
    ipcRenderer.send('backend:send', msg)
  },
  onBackendEvent: (callback: (event: unknown) => void): (() => void) => {
    const handler = (_: unknown, data: unknown): void => callback(data)
    ipcRenderer.on('backend:event', handler)
    return () => ipcRenderer.removeListener('backend:event', handler)
  },

  // Flow sync (for MCP integration)
  flowSyncToFile: (flowJson: string): void => {
    ipcRenderer.send('flow:syncToFile', flowJson)
  },
  flowStartWatching: (): Promise<boolean> => ipcRenderer.invoke('flow:startWatching'),
  flowStopWatching: (): Promise<boolean> => ipcRenderer.invoke('flow:stopWatching'),
  flowGetSharedPath: (): Promise<string> => ipcRenderer.invoke('flow:getSharedPath'),
  onFlowExternalUpdate: (callback: (flowJson: string) => void): (() => void) => {
    const handler = (_: unknown, data: string): void => callback(data)
    ipcRenderer.on('flow:externalUpdate', handler)
    return () => ipcRenderer.removeListener('flow:externalUpdate', handler)
  },

  // Terminal (Claude Code only)
  terminalSpawn: (opts?: { cwd?: string }): Promise<boolean> =>
    ipcRenderer.invoke('terminal:spawn', opts),
  terminalInput: (data: string): void => {
    ipcRenderer.send('terminal:input', data)
  },
  terminalResize: (cols: number, rows: number): void => {
    ipcRenderer.send('terminal:resize', cols, rows)
  },
  terminalKill: (): Promise<boolean> => ipcRenderer.invoke('terminal:kill'),
  onTerminalData: (callback: (data: string) => void): (() => void) => {
    const handler = (_: unknown, data: string): void => callback(data)
    ipcRenderer.on('terminal:data', handler)
    return () => ipcRenderer.removeListener('terminal:data', handler)
  },
  onTerminalExit: (callback: (code: number) => void): (() => void) => {
    const handler = (_: unknown, code: number): void => callback(code)
    ipcRenderer.on('terminal:exit', handler)
    return () => ipcRenderer.removeListener('terminal:exit', handler)
  },

  // Auto-Y
  setAutoYes: (enabled: boolean): void => {
    ipcRenderer.send('terminal:setAutoYes', enabled)
  },
  getAutoYes: (): Promise<{ enabled: boolean; log: Array<{ time: string; prompt: string }> }> =>
    ipcRenderer.invoke('terminal:getAutoYes'),
  onAutoYes: (callback: (entry: { time: string; prompt: string }) => void): (() => void) => {
    const handler = (_: unknown, entry: { time: string; prompt: string }): void => callback(entry)
    ipcRenderer.on('terminal:autoYes', handler)
    return () => ipcRenderer.removeListener('terminal:autoYes', handler)
  },
  onAutoYesState: (callback: (state: { enabled: boolean; log: Array<{ time: string; prompt: string }> }) => void): (() => void) => {
    const handler = (_: unknown, state: any): void => callback(state)
    ipcRenderer.on('terminal:autoYesState', handler)
    return () => ipcRenderer.removeListener('terminal:autoYesState', handler)
  }
}

contextBridge.exposeInMainWorld('api', api)
