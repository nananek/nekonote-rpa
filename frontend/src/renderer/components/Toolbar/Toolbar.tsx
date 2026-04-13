import { useEffect, useRef, useState } from 'react'
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
  const [isPaused, setIsPaused] = useState(false)
  const [recordMode, setRecordMode] = useState<'auto' | 'element' | 'coordinate' | 'image'>('auto')
  const [recordTarget, setRecordTarget] = useState<'desktop' | 'browser'>('desktop')

  // Track blocks recorded in the current session (for "discard" option)
  const recordedBlockIds = useRef<string[]>([])

  // Listen for record events from backend
  useEffect(() => {
    const unsub = wsClient.subscribe((event: any) => {
      if (event.type === 'record.started') {
        setIsRecording(true)
        setIsPaused(false)
        recordedBlockIds.current = []
        ;(window as any).api?.showRecordBar?.()
      } else if (event.type === 'record.block') {
        const block = event.block as FlowBlock
        if (block) {
          addBlock(block)
          recordedBlockIds.current.push(block.id)
        }
      } else if (event.type === 'record.paused') {
        setIsPaused(true)
      } else if (event.type === 'record.resumed') {
        setIsPaused(false)
      } else if (event.type === 'record.completed' || event.type === 'record.failed') {
        setIsRecording(false)
        setIsPaused(false)
        ;(window as any).api?.hideRecordBar?.()
        const count = recordedBlockIds.current.length
        if (count > 0) {
          const keep = confirm(`${count}個のブロックを記録しました。\n\nOK: フローに反映\nキャンセル: 記録を破棄`)
          if (!keep) {
            const store = useFlowStore.getState()
            for (const id of recordedBlockIds.current) {
              store.removeBlock(id)
            }
          }
        }
        recordedBlockIds.current = []
      }
    })
    return unsub
  }, [addBlock])

  // Listen for record bar button actions (from floating window)
  useEffect(() => {
    const api = (window as any).api
    if (!api?.onRecordBarAction) return
    const unsub = api.onRecordBarAction((action: string) => {
      if (action === 'pause') wsClient.pauseRecording()
      else if (action === 'resume') wsClient.resumeRecording()
      else if (action === 'stop') wsClient.stopRecording()
    })
    return unsub
  }, [])

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
      } else if (e.altKey && e.ctrlKey && (e.key === 'p' || e.key === 'P')) {
        e.preventDefault()
        if (isRecording) {
          if (isPaused) wsClient.resumeRecording()
          else wsClient.pauseRecording()
        }
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
        <>
          <select
            value={recordTarget}
            onChange={(e) => setRecordTarget(e.target.value as typeof recordTarget)}
            style={{
              padding: '4px 8px', fontSize: 12,
              background: '#1e293b', color: '#e2e8f0',
              border: '1px solid #334155', borderRadius: 4, cursor: 'pointer',
            }}
            title="記録対象"
          >
            <option value="desktop">デスクトップ</option>
            <option value="browser">ブラウザ</option>
          </select>
          {recordTarget === 'desktop' && (
            <select
              value={recordMode}
              onChange={(e) => setRecordMode(e.target.value as typeof recordMode)}
              style={{
                padding: '4px 8px', fontSize: 12,
                background: '#1e293b', color: '#e2e8f0',
                border: '1px solid #334155', borderRadius: 4, cursor: 'pointer',
              }}
              title="認識モード"
            >
              <option value="auto">自動</option>
              <option value="element">要素認識</option>
              <option value="coordinate">座標</option>
              <option value="image">画像</option>
            </select>
          )}
          <button
            onClick={() => {
              if (recordTarget === 'browser') {
                const url = prompt('記録を開始するURLを入力 (空欄でabout:blank)') || ''
                wsClient.startRecording(recordMode, 'browser', url)
              } else {
                wsClient.startRecording(recordMode, 'desktop')
              }
            }}
            style={{ ...btnBase, background: '#a855f7', color: '#fff', border: 'none', fontWeight: 600 }}
            title="操作記録を開始"
          >
            ● 記録
          </button>
        </>
      ) : (
        <>
          <select
            value={recordMode}
            onChange={(e) => {
              const next = e.target.value as typeof recordMode
              setRecordMode(next)
              wsClient.setRecordMode(next)
            }}
            style={{
              padding: '4px 8px', fontSize: 12,
              background: '#1e293b', color: '#e2e8f0',
              border: '1px solid #334155', borderRadius: 4, cursor: 'pointer',
            }}
            title="認識モード"
          >
            <option value="auto">自動</option>
            <option value="element">要素認識</option>
            <option value="coordinate">座標</option>
            <option value="image">画像</option>
          </select>
          {!isPaused ? (
            <button
              onClick={() => wsClient.pauseRecording()}
              style={{ ...btnBase, background: '#f59e0b', color: '#000', border: 'none', fontWeight: 600 }}
              title="一時停止 (Alt+Ctrl+P)"
            >
              ‖ 一時停止
            </button>
          ) : (
            <button
              onClick={() => wsClient.resumeRecording()}
              style={{ ...btnBase, background: '#22c55e', color: '#000', border: 'none', fontWeight: 600 }}
              title="再開"
            >
              ▶ 再開
            </button>
          )}
          <button
            onClick={() => wsClient.stopRecording()}
            style={{ ...btnBase, background: '#ef4444', color: '#fff', border: 'none', fontWeight: 600 }}
            title="記録を終了してフローに反映"
          >
            ■ 完了
          </button>
        </>
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
