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
  }
}

contextBridge.exposeInMainWorld('api', api)
