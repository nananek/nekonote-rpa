import { contextBridge, ipcRenderer } from 'electron'

export const api = {
  openFile: (): Promise<{ filePath: string; content: string } | null> =>
    ipcRenderer.invoke('dialog:openFile'),
  saveFile: (content: string, currentPath?: string): Promise<string | null> =>
    ipcRenderer.invoke('dialog:saveFile', content, currentPath),

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
