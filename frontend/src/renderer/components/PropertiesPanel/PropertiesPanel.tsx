import { useState, useEffect, useCallback } from 'react'
import { useFlowStore } from '../../stores/flowStore'
import { getNodeDef, type ParamDef } from '../../types/nodeDefinitions'
import { t } from '../../i18n'
import { wsClient } from '../../api/ws'
import { useExecutionStore } from '../../stores/executionStore'
import type { FlowBlock } from '../../types/flow'
import type { ExecutionEvent } from '../../types/api'

interface Props {
  selectedNodeId: string | null
}

function findBlock(blocks: FlowBlock[], id: string): FlowBlock | null {
  for (const b of blocks) {
    if (b.id === id) return b
    if (b.children) {
      const found = findBlock(b.children, id)
      if (found) return found
    }
    if (b.elseChildren) {
      const found = findBlock(b.elseChildren, id)
      if (found) return found
    }
  }
  return null
}

/** Params that represent a CSS selector and should get the picker button */
const SELECTOR_PARAMS = new Set(['selector'])

function ParamInput({
  param,
  value,
  onChange,
  onPickerRequest
}: {
  param: ParamDef
  value: unknown
  onChange: (val: unknown) => void
  onPickerRequest?: () => void
}): JSX.Element {
  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '5px 8px',
    borderRadius: 4,
    border: '1px solid #334155',
    backgroundColor: '#1e293b',
    color: '#e2e8f0',
    fontSize: 12,
    outline: 'none'
  }

  const isSelector = SELECTOR_PARAMS.has(param.name)

  switch (param.type) {
    case 'boolean':
      return (
        <input
          type="checkbox"
          checked={!!value}
          onChange={(e) => onChange(e.target.checked)}
          style={{ accentColor: '#3b82f6' }}
        />
      )
    case 'number':
      return (
        <input
          type="number"
          value={value === undefined ? '' : String(value)}
          onChange={(e) => onChange(e.target.value === '' ? undefined : Number(e.target.value))}
          placeholder={param.placeholder}
          style={inputStyle}
        />
      )
    case 'select':
      return (
        <select
          value={String(value ?? param.default ?? '')}
          onChange={(e) => onChange(e.target.value)}
          style={inputStyle}
        >
          {param.options?.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      )
    default:
      if (isSelector && onPickerRequest) {
        return (
          <div style={{ display: 'flex', gap: 4 }}>
            <input
              type="text"
              value={String(value ?? '')}
              onChange={(e) => onChange(e.target.value)}
              placeholder={param.placeholder}
              style={{ ...inputStyle, flex: 1 }}
            />
            <button
              onClick={onPickerRequest}
              title="要素を選択"
              style={{
                padding: '4px 8px',
                borderRadius: 4,
                border: '1px solid #334155',
                backgroundColor: '#3b82f6',
                color: '#fff',
                cursor: 'pointer',
                fontSize: 14,
                flexShrink: 0,
                lineHeight: 1
              }}
            >
              🎯
            </button>
          </div>
        )
      }
      return (
        <input
          type="text"
          value={String(value ?? '')}
          onChange={(e) => onChange(e.target.value)}
          placeholder={param.placeholder}
          style={inputStyle}
        />
      )
  }
}

export function PropertiesPanel({ selectedNodeId }: Props): JSX.Element {
  const flow = useFlowStore((s) => s.flow)
  const updateBlock = useFlowStore((s) => s.updateBlock)
  const [pickerState, setPickerState] = useState<'idle' | 'opening' | 'picking'>('idle')
  const [pickerTargetParam, setPickerTargetParam] = useState<string | null>(null)

  const block = selectedNodeId ? findBlock(flow.blocks, selectedNodeId) : null
  const def = block ? getNodeDef(block.type) : null

  // Listen for picker events
  const handlePickerEvent = useCallback((event: ExecutionEvent) => {
    if (event.type === 'picker.browserReady') {
      setPickerState('picking')
      wsClient.startPicker()
    } else if (event.type === 'picker.started') {
      setPickerState('picking')
    } else if (event.type === 'picker.result') {
      setPickerState('idle')
      if (!event.cancelled && event.selector && pickerTargetParam && block) {
        updateBlock(block.id, (b) => ({
          ...b,
          params: { ...b.params, [pickerTargetParam]: event.selector }
        }))
      }
      setPickerTargetParam(null)
    } else if (event.type === 'picker.error') {
      setPickerState('idle')
      setPickerTargetParam(null)
      console.error('Picker error:', event.error)
    }
  }, [pickerTargetParam, block, updateBlock])

  useEffect(() => {
    const unsub = wsClient.subscribe(handlePickerEvent)
    return unsub
  }, [handlePickerEvent])

  const startPicker = (paramName: string): void => {
    setPickerTargetParam(paramName)
    setPickerState('opening')
    // Open browser if needed, then start picker
    wsClient.openPickerBrowser()
  }

  const updateParam = (paramName: string, value: unknown): void => {
    if (!block) return
    updateBlock(block.id, (b) => ({ ...b, params: { ...b.params, [paramName]: value } }))
  }

  const updateLabel = (label: string): void => {
    if (!block) return
    updateBlock(block.id, (b) => ({ ...b, label }))
  }

  if (!block) {
    return (
      <div
        style={{
          width: 260,
          backgroundColor: '#0f172a',
          borderLeft: '1px solid #334155',
          padding: 16,
          fontSize: 12,
          color: '#64748b'
        }}
      >
        {t('properties.noSelection')}
      </div>
    )
  }

  return (
    <div
      style={{
        width: 260,
        backgroundColor: '#0f172a',
        borderLeft: '1px solid #334155',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      <div
        style={{
          padding: '10px 12px',
          borderBottom: '1px solid #334155',
          fontSize: 13,
          fontWeight: 600,
          color: '#e2e8f0'
        }}
      >
        {t('properties.title')}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
        <div
          style={{
            display: 'inline-block',
            padding: '2px 8px',
            borderRadius: 4,
            backgroundColor: `${def?.color ?? '#666'}30`,
            color: def?.color ?? '#aaa',
            fontSize: 11,
            fontWeight: 600,
            marginBottom: 12
          }}
        >
          {block.type}
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 4 }}>
            {t('properties.label')}
          </label>
          <input
            type="text"
            value={block.label}
            onChange={(e) => updateLabel(e.target.value)}
            style={{
              width: '100%',
              padding: '5px 8px',
              borderRadius: 4,
              border: '1px solid #334155',
              backgroundColor: '#1e293b',
              color: '#e2e8f0',
              fontSize: 12,
              outline: 'none'
            }}
          />
        </div>

        {def?.params.map((param) => (
          <div key={param.name} style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 4 }}>
              {t(`param.${param.name}`)}
            </label>
            <ParamInput
              param={param}
              value={block.params[param.name]}
              onChange={(val) => updateParam(param.name, val)}
              onPickerRequest={
                SELECTOR_PARAMS.has(param.name) ? () => startPicker(param.name) : undefined
              }
            />
          </div>
        ))}

        {/* Picker status */}
        {pickerState !== 'idle' && (
          <div
            style={{
              marginTop: 8,
              padding: '8px 12px',
              borderRadius: 6,
              backgroundColor: '#1e293b',
              border: '1px solid #3b82f6',
              fontSize: 12,
              color: '#93c5fd'
            }}
          >
            {pickerState === 'opening' && 'ブラウザを起動中...'}
            {pickerState === 'picking' && '要素をクリックしてください (Escでキャンセル)'}
          </div>
        )}

        <div style={{ marginTop: 16, fontSize: 10, color: '#475569' }}>ID: {block.id}</div>
      </div>
    </div>
  )
}
