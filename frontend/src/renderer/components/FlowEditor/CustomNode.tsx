import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { getNodeDef } from '../../types/nodeDefinitions'

interface CustomNodeData {
  nodeType: string
  label: string
  params: Record<string, unknown>
  isActive: boolean
  hasError: boolean
}

function CustomNodeComponent({ data, selected }: NodeProps): JSX.Element {
  const nd = data as unknown as CustomNodeData
  const def = getNodeDef(nd.nodeType)
  const color = def?.color ?? '#666'
  const icon = def?.icon ?? '?'
  const outputs = def?.outputs ?? ['out']

  return (
    <div
      style={{
        minWidth: 160,
        borderRadius: 8,
        border: `2px solid ${nd.isActive ? '#22c55e' : nd.hasError ? '#ef4444' : selected ? '#60a5fa' : color}`,
        backgroundColor: nd.isActive ? '#052e16' : nd.hasError ? '#450a0a' : '#1e293b',
        boxShadow: nd.isActive
          ? '0 0 12px rgba(34,197,94,0.4)'
          : selected
            ? '0 0 8px rgba(96,165,250,0.3)'
            : '0 2px 4px rgba(0,0,0,0.3)',
        fontFamily: 'sans-serif',
        transition: 'border-color 0.15s, box-shadow 0.15s'
      }}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        id="in"
        style={{
          width: 10,
          height: 10,
          backgroundColor: '#64748b',
          border: '2px solid #334155'
        }}
      />

      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 12px',
          borderBottom: `1px solid ${color}33`,
          borderRadius: '6px 6px 0 0',
          backgroundColor: `${color}20`
        }}
      >
        <span
          style={{
            width: 22,
            height: 22,
            borderRadius: 4,
            backgroundColor: color,
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 12,
            fontWeight: 700,
            flexShrink: 0
          }}
        >
          {icon}
        </span>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>
          {nd.label || def?.label || nd.nodeType}
        </span>
      </div>

      {/* Params preview */}
      <div style={{ padding: '4px 12px 8px', fontSize: 11, color: '#94a3b8' }}>
        {def?.params.slice(0, 2).map((p) => {
          const val = nd.params[p.name]
          if (val === undefined || val === '') return null
          return (
            <div key={p.name} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 180 }}>
              {p.label}: {String(val)}
            </div>
          )
        })}
        {(!def?.params.length) && (
          <div style={{ fontStyle: 'italic' }}>No parameters</div>
        )}
      </div>

      {/* Output handles */}
      {outputs.length === 1 ? (
        <Handle
          type="source"
          position={Position.Bottom}
          id={outputs[0]}
          style={{
            width: 10,
            height: 10,
            backgroundColor: color,
            border: '2px solid #334155'
          }}
        />
      ) : (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            padding: '0 8px 4px'
          }}
        >
          {outputs.map((handle) => (
            <div key={handle} style={{ position: 'relative', textAlign: 'center' }}>
              <span style={{ fontSize: 9, color: '#94a3b8' }}>{handle}</span>
              <Handle
                type="source"
                position={Position.Bottom}
                id={handle}
                style={{
                  position: 'relative',
                  transform: 'none',
                  width: 10,
                  height: 10,
                  backgroundColor: handle === 'true' || handle === 'try' || handle === 'loop' ? '#22c55e' : '#ef4444',
                  border: '2px solid #334155',
                  margin: '0 auto'
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export const CustomNode = memo(CustomNodeComponent)
