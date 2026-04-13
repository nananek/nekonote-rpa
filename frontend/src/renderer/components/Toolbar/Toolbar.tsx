import { useEffect, useState } from 'react'
import { useFlowStore } from '../../stores/flowStore'
import { useExecutionStore } from '../../stores/executionStore'
import { wsClient } from '../../api/ws'
import { t } from '../../i18n'
import type { ViewMode } from '../../App'
import type { FlowBlock } from '../../types/flow'


interface ToolbarProps {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
}

export function Toolbar({ viewMode, onViewModeChange }: ToolbarProps): JSX.Element {
  const flow = useFlowStore((s) => s.flow)
  const setFlow = useFlowStore((s) => s.setFlow)
  const setFilePath = useFlowStore((s) => s.setFilePath)
  const filePath = useFlowStore((s) => s.filePath)
  const isDirty = useFlowStore((s) => s.isDirty)
  const markClean = useFlowStore((s) => s.markClean)
  const newFlow = useFlowStore((s) => s.newFlow)
  const undo = useFlowStore((s) => s.undo)
  const redo = useFlowStore((s) => s.redo)
  const canUndo = useFlowStore((s) => s.canUndo)
  const canRedo = useFlowStore((s) => s.canRedo)
  const isRunning = useExecutionStore((s) => s.isRunning)
  const executionId = useExecutionStore((s) => s.executionId)
  const addBlock = useFlowStore((s) => s.addBlock)
  const [isRecording, setIsRecording] = useState(false)

  // Listen for record events from backend
  useEffect(() => {
    const unsub = wsClient.subscribe((event: any) => {
      if (event.type === 'record.started') {
        setIsRecording(true)
      } else if (event.type === 'record.completed') {
        setIsRecording(false)
        const blocks = event.blocks as FlowBlock[]
        if (blocks?.length) {
          for (const block of blocks) {
            addBlock(block)
          }
        }
      } else if (event.type === 'record.failed') {
        setIsRecording(false)
      }
    })
    return unsub
  }, [addBlock])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent): void => {
      if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault()
        undo()
      } else if (e.ctrlKey && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault()
        redo()
      } else if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        handleSave()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  })

  const handleNew = (): void => {
    newFlow()
  }

  const handleOpen = async (): Promise<void> => {
    if (!window.api) return
    const result = await window.api.openFile()
    if (result) {
      try {
        const parsed = JSON.parse(result.content)
        setFlow(parsed)
        setFilePath(result.filePath)
      } catch (e) {
        console.error('Failed to parse flow file:', e)
      }
    }
  }

  const handleSave = async (): Promise<void> => {
    const content = JSON.stringify(useFlowStore.getState().flow, null, 2)
    const currentPath = useFlowStore.getState().filePath
    if (!window.api) return
    const savedPath = await window.api.saveFile(content, currentPath ?? undefined)
    if (savedPath) {
      setFilePath(savedPath)
      markClean()
    }
  }

  const handleRun = (): void => {
    wsClient.executeFlow(flow)
  }

  const handleStop = (): void => {
    if (executionId) {
      wsClient.stopExecution(executionId)
    }
  }

  const btnBase = {
    padding: '5px 12px',
    border: '1px solid #555',
    borderRadius: '4px',
    cursor: 'pointer' as const,
    fontSize: '12px',
    fontWeight: 500 as const
  }

  const btnDefault = { ...btnBase, background: '#2d3748', color: '#e2e8f0' }
  const btnDisabled = { ...btnBase, background: '#1e293b', color: '#475569', cursor: 'default' as const, border: '1px solid #334155' }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 16px',
        backgroundColor: '#16213e',
        borderBottom: '1px solid #333'
      }}
    >
      <span style={{ fontWeight: 'bold', color: '#e2e8f0', marginRight: '12px', fontSize: '14px' }}>
        {t('app.title')}
      </span>

      <button onClick={handleNew} style={btnDefault}>{t('toolbar.new')}</button>
      <button onClick={handleOpen} style={btnDefault}>{t('toolbar.open')}</button>
      <button onClick={handleSave} style={btnDefault}>
        {t('toolbar.save')}{isDirty ? ' *' : ''}
      </button>

      <div style={{ width: 1, height: 20, backgroundColor: '#334155', margin: '0 4px' }} />

      <button
        onClick={undo}
        disabled={!canUndo()}
        style={canUndo() ? btnDefault : btnDisabled}
        title={`${t('toolbar.undo')} (Ctrl+Z)`}
      >
        {t('toolbar.undo')}
      </button>
      <button
        onClick={redo}
        disabled={!canRedo()}
        style={canRedo() ? btnDefault : btnDisabled}
        title={`${t('toolbar.redo')} (Ctrl+Y)`}
      >
        {t('toolbar.redo')}
      </button>

      <div style={{ width: 1, height: 20, backgroundColor: '#334155', margin: '0 4px' }} />

      {(['visual', 'split', 'code'] as ViewMode[]).map((mode) => (
        <button
          key={mode}
          onClick={() => onViewModeChange(mode)}
          style={viewMode === mode
            ? { ...btnBase, background: '#3b82f6', color: '#fff', border: 'none' }
            : btnDefault
          }
        >
          {{ visual: 'Visual', split: 'Split', code: 'Code' }[mode]}
        </button>
      ))}

      <div style={{ flex: 1 }} />

      {!isRecording ? (
        <button
          onClick={() => wsClient.startRecording(30)}
          style={{ ...btnBase, background: '#a855f7', color: '#fff', border: 'none', fontWeight: 600 }}
          title="Record desktop operations for 30 seconds"
        >
          Rec
        </button>
      ) : (
        <button
          onClick={() => wsClient.stopRecording()}
          style={{ ...btnBase, background: '#ef4444', color: '#fff', border: 'none', fontWeight: 600, animation: 'pulse 1s infinite' }}
        >
          Stop Rec
        </button>
      )}

      {!isRunning ? (
        <button
          onClick={handleRun}
          style={{ ...btnBase, background: '#22c55e', color: '#000', border: 'none', fontWeight: 600 }}
        >
          {t('toolbar.run')}
        </button>
      ) : (
        <button
          onClick={handleStop}
          style={{ ...btnBase, background: '#ef4444', color: '#fff', border: 'none', fontWeight: 600 }}
        >
          {t('toolbar.stop')}
        </button>
      )}
    </div>
  )
}
