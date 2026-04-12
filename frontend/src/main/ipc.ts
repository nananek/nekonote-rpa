import { ipcMain, dialog } from 'electron'
import { readFile, writeFile } from 'fs/promises'

export function setupIpc(): void {
  ipcMain.handle('dialog:openFile', async () => {
    const result = await dialog.showOpenDialog({
      filters: [{ name: 'Nekonote Flow', extensions: ['neko', 'json'] }],
      properties: ['openFile']
    })
    if (result.canceled || result.filePaths.length === 0) return null
    const filePath = result.filePaths[0]
    const content = await readFile(filePath, 'utf-8')
    return { filePath, content }
  })

  ipcMain.handle('dialog:saveFile', async (_event, content: string, currentPath?: string) => {
    let filePath = currentPath
    if (!filePath) {
      const result = await dialog.showSaveDialog({
        filters: [{ name: 'Nekonote Flow', extensions: ['neko'] }]
      })
      if (result.canceled || !result.filePath) return null
      filePath = result.filePath
    }
    await writeFile(filePath, content, 'utf-8')
    return filePath
  })
}
