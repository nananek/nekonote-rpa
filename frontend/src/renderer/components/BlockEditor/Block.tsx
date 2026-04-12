import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { FlowBlock } from '../../types/flow'
import { getNodeDef } from '../../types/nodeDefinitions'
import { useFlowStore } from '../../stores/flowStore'
import { useExecutionStore } from '../../stores/executionStore'
import { t } from '../../i18n'
import { BlockList } from './BlockList'

interface BlockProps {
  block: FlowBlock
  depth: number
}

export function Block({ block, depth }: BlockProps): JSX.Element {
  const selectedBlockId = useFlowStore((s) => s.selectedBlockId)
  const selectBlock = useFlowStore((s) => s.selectBlock)
  const removeBlock = useFlowStore((s) => s.removeBlock)
  const activeNodeId = useExecutionStore((s) => s.activeNodeId)

  const def = getNodeDef(block.type)
  const color = def?.color ?? '#666'
  const icon = def?.icon ?? '?'
  const isSelected = selectedBlockId === block.id
  const isActive = activeNodeId === block.id
  const isControl = block.type.startsWith('control.')
  const hasChildren = isControl && block.type !== 'control.wait'

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: block.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1
  }

  const paramSummary = (): string => {
    if (!def) return ''
    const parts: string[] = []
    for (const p of def.params.slice(0, 2)) {
      const val = block.params[p.name]
      if (val !== undefined && val !== '') {
        parts.push(`${t(`param.${p.name}`)}: ${String(val)}`)
      }
    }
    return parts.join(' | ')
  }

  return (
    <div ref={setNodeRef} style={style}>
      <div
        onClick={(e) => {
          e.stopPropagation()
          selectBlock(block.id)
        }}
        style={{
          display: 'flex',
          alignItems: 'stretch',
          borderRadius: 6,
          border: `2px solid ${isActive ? '#22c55e' : isSelected ? '#60a5fa' : color + '60'}`,
          backgroundColor: isActive ? '#052e16' : isSelected ? '#1e293b' : '#111827',
          boxShadow: isActive ? '0 0 12px rgba(34,197,94,0.3)' : 'none',
          marginBottom: 4,
          overflow: 'hidden',
          transition: 'border-color 0.15s, box-shadow 0.15s'
        }}
      >
        {/* Color bar + drag handle */}
        <div
          {...attributes}
          {...listeners}
          style={{
            width: 6,
            backgroundColor: color,
            cursor: 'grab',
            flexShrink: 0
          }}
        />

        <div style={{ flex: 1, padding: '8px 12px', minWidth: 0 }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              style={{
                width: 22,
                height: 22,
                borderRadius: 4,
                backgroundColor: color,
                color: '#fff',
                display: 'inline-flex',
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
              {block.label || t(`node.${block.type}`)}
            </span>
            <span style={{ fontSize: 11, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {paramSummary()}
            </span>
            <div style={{ flex: 1 }} />
            <button
              onClick={(e) => {
                e.stopPropagation()
                removeBlock(block.id)
              }}
              style={{
                background: 'none',
                border: 'none',
                color: '#475569',
                cursor: 'pointer',
                fontSize: 14,
                padding: '0 4px',
                lineHeight: 1
              }}
              title="Delete"
            >
              ×
            </button>
          </div>

          {/* Children for control blocks */}
          {hasChildren && (
            <div style={{ marginTop: 8 }}>
              {block.type === 'control.if' ? (
                <>
                  <div style={{ fontSize: 10, color: '#22c55e', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase' }}>True</div>
                  <div style={{ borderLeft: '2px solid #22c55e30', paddingLeft: 12, marginBottom: 8 }}>
                    <BlockList blocks={block.children ?? []} parentId={block.id} branch="children" depth={depth + 1} />
                  </div>
                  <div style={{ fontSize: 10, color: '#ef4444', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase' }}>False</div>
                  <div style={{ borderLeft: '2px solid #ef444430', paddingLeft: 12 }}>
                    <BlockList blocks={block.elseChildren ?? []} parentId={block.id} branch="elseChildren" depth={depth + 1} />
                  </div>
                </>
              ) : block.type === 'control.tryCatch' ? (
                <>
                  <div style={{ fontSize: 10, color: '#3b82f6', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase' }}>Try</div>
                  <div style={{ borderLeft: '2px solid #3b82f630', paddingLeft: 12, marginBottom: 8 }}>
                    <BlockList blocks={block.children ?? []} parentId={block.id} branch="children" depth={depth + 1} />
                  </div>
                  <div style={{ fontSize: 10, color: '#f59e0b', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase' }}>Catch</div>
                  <div style={{ borderLeft: '2px solid #f59e0b30', paddingLeft: 12 }}>
                    <BlockList blocks={block.elseChildren ?? []} parentId={block.id} branch="elseChildren" depth={depth + 1} />
                  </div>
                </>
              ) : (
                // loop, forEach
                <div style={{ borderLeft: `2px solid ${color}30`, paddingLeft: 12 }}>
                  <BlockList blocks={block.children ?? []} parentId={block.id} branch="children" depth={depth + 1} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
