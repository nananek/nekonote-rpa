import { contextBridge, ipcRenderer } from 'electron'

export const api = {
  openFile: (): Promise<{ filePath: string; content: string } | null> =>
    ipcRenderer.invoke('dialog:openFile'),
  saveFile: (content: string, currentPath?: string): Promise<string | null> =>
    ipcRenderer.invoke('dialog:saveFile', content, currentPath)
}

contextBridge.exposeInMainWorld('api', api)
