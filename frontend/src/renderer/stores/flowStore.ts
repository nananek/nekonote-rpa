import { create } from 'zustand'
import type { Flow, FlowBlock } from '../types/flow'

const MAX_HISTORY = 50

function createEmptyFlow(): Flow {
  return {
    version: '1.0',
    id: crypto.randomUUID(),
    name: 'New Flow',
    description: '',
    variables: [],
    blocks: [
      {
        id: 'block_1',
        type: 'data.log',
        label: 'Hello',
        params: { message: 'Hello from Nekonote!' }
      },
      {
        id: 'block_2',
        type: 'data.log',
        label: 'Done',
        params: { message: 'Flow complete.' }
      }
    ]
  }
}

function cloneFlow(flow: Flow): Flow {
  return JSON.parse(JSON.stringify(flow))
}

/** Deep-find a block by ID in the block tree */
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

/** Deep-remove a block by ID, returns the removed block */
function removeBlock(blocks: FlowBlock[], id: string): { blocks: FlowBlock[]; removed: FlowBlock | null } {
  const result: FlowBlock[] = []
  let removed: FlowBlock | null = null

  for (const b of blocks) {
    if (b.id === id) {
      removed = b
      continue
    }
    const copy = { ...b }
    if (copy.children) {
      const r = removeBlock(copy.children, id)
      copy.children = r.blocks
      if (r.removed) removed = r.removed
    }
    if (copy.elseChildren) {
      const r = removeBlock(copy.elseChildren, id)
      copy.elseChildren = r.blocks
      if (r.removed) removed = r.removed
    }
    result.push(copy)
  }
  return { blocks: result, removed }
}

/** Deep-update a block by ID */
function updateBlockInTree(blocks: FlowBlock[], id: string, updater: (b: FlowBlock) => FlowBlock): FlowBlock[] {
  return blocks.map((b) => {
    if (b.id === id) return updater(b)
    const copy = { ...b }
    if (copy.children) copy.children = updateBlockInTree(copy.children, id, updater)
    if (copy.elseChildren) copy.elseChildren = updateBlockInTree(copy.elseChildren, id, updater)
    return copy
  })
}

interface FlowState {
  flow: Flow
  filePath: string | null
  isDirty: boolean
  selectedBlockId: string | null
  _history: Flow[]
  _future: Flow[]

  setFlow: (flow: Flow) => void
  updateFlow: (flow: Flow) => void
  setFilePath: (path: string | null) => void
  markClean: () => void
  newFlow: () => void
  selectBlock: (id: string | null) => void
  addBlock: (block: FlowBlock, parentId?: string, index?: number) => void
  removeBlock: (id: string) => void
  updateBlock: (id: string, updater: (b: FlowBlock) => FlowBlock) => void
  moveBlock: (id: string, targetParentId: string | null, targetIndex: number) => void
  undo: () => void
  redo: () => void
  canUndo: () => boolean
  canRedo: () => boolean
}

export const useFlowStore = create<FlowState>((set, get) => ({
  flow: createEmptyFlow(),
  filePath: null,
  isDirty: false,
  selectedBlockId: null,
  _history: [],
  _future: [],

  setFlow: (flow) => set({ flow, isDirty: false, _history: [], _future: [] }),

  updateFlow: (flow) => {
    const state = get()
    const history = [...state._history, cloneFlow(state.flow)]
    if (history.length > MAX_HISTORY) history.shift()
    set({ flow, isDirty: true, _history: history, _future: [] })
  },

  setFilePath: (filePath) => set({ filePath }),
  markClean: () => set({ isDirty: false }),
  newFlow: () => set({ flow: createEmptyFlow(), filePath: null, isDirty: false, selectedBlockId: null, _history: [], _future: [] }),
  selectBlock: (id) => set({ selectedBlockId: id }),

  addBlock: (block, parentId, index) => {
    const state = get()
    const flow = cloneFlow(state.flow)

    if (!parentId) {
      // Add to root
      const i = index ?? flow.blocks.length
      flow.blocks.splice(i, 0, block)
    } else {
      const parent = findBlock(flow.blocks, parentId)
      if (parent) {
        if (!parent.children) parent.children = []
        const i = index ?? parent.children.length
        parent.children.splice(i, 0, block)
      }
    }

    const history = [...state._history, cloneFlow(state.flow)]
    if (history.length > MAX_HISTORY) history.shift()
    set({ flow, isDirty: true, _history: history, _future: [], selectedBlockId: block.id })
  },

  removeBlock: (id) => {
    const state = get()
    const flow = cloneFlow(state.flow)
    const { blocks } = removeBlock(flow.blocks, id)
    flow.blocks = blocks

    const history = [...state._history, cloneFlow(state.flow)]
    if (history.length > MAX_HISTORY) history.shift()
    set({ flow, isDirty: true, _history: history, _future: [], selectedBlockId: state.selectedBlockId === id ? null : state.selectedBlockId })
  },

  updateBlock: (id, updater) => {
    const state = get()
    const flow = { ...state.flow, blocks: updateBlockInTree(state.flow.blocks, id, updater) }
    const history = [...state._history, cloneFlow(state.flow)]
    if (history.length > MAX_HISTORY) history.shift()
    set({ flow, isDirty: true, _history: history, _future: [] })
  },

  moveBlock: (id, targetParentId, targetIndex) => {
    const state = get()
    const flow = cloneFlow(state.flow)
    const { blocks, removed } = removeBlock(flow.blocks, id)
    if (!removed) return
    flow.blocks = blocks

    if (!targetParentId) {
      flow.blocks.splice(targetIndex, 0, removed)
    } else {
      const parent = findBlock(flow.blocks, targetParentId)
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.splice(targetIndex, 0, removed)
      }
    }

    const history = [...state._history, cloneFlow(state.flow)]
    if (history.length > MAX_HISTORY) history.shift()
    set({ flow, isDirty: true, _history: history, _future: [] })
  },

  undo: () => {
    const state = get()
    if (state._history.length === 0) return
    const history = [...state._history]
    const prev = history.pop()!
    set({ flow: prev, isDirty: true, _history: history, _future: [cloneFlow(state.flow), ...state._future] })
  },

  redo: () => {
    const state = get()
    if (state._future.length === 0) return
    const future = [...state._future]
    const next = future.shift()!
    set({ flow: next, isDirty: true, _history: [...state._history, cloneFlow(state.flow)], _future: future })
  },

  canUndo: () => get()._history.length > 0,
  canRedo: () => get()._future.length > 0
}))
