import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy
} from '@dnd-kit/sortable'
import { useDroppable } from '@dnd-kit/core'
import type { FlowBlock } from '../../types/flow'
import { useFlowStore } from '../../stores/flowStore'
import { Block } from './Block'

interface BlockListProps {
  blocks: FlowBlock[]
  parentId?: string
  branch?: 'children' | 'elseChildren'
  depth: number
}

export function BlockList({ blocks, parentId, branch, depth }: BlockListProps): JSX.Element {
  const moveBlock = useFlowStore((s) => s.moveBlock)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  const { setNodeRef, isOver } = useDroppable({
    id: parentId ? `${parentId}:${branch ?? 'children'}` : 'root'
  })

  const handleDragEnd = (event: DragEndEvent): void => {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const overIndex = blocks.findIndex((b) => b.id === over.id)
    if (overIndex !== -1) {
      moveBlock(String(active.id), parentId ?? null, overIndex)
    }
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
        <div
          ref={setNodeRef}
          style={{
            minHeight: blocks.length === 0 ? 40 : undefined,
            borderRadius: 4,
            border: isOver ? '1px dashed #3b82f6' : '1px dashed transparent',
            padding: blocks.length === 0 ? 8 : 0,
            transition: 'border-color 0.15s'
          }}
        >
          {blocks.length === 0 && (
            <div style={{ fontSize: 11, color: '#475569', textAlign: 'center', padding: 8 }}>
              ここにブロックをドロップ
            </div>
          )}
          {blocks.map((block) => (
            <Block key={block.id} block={block} depth={depth} />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}
