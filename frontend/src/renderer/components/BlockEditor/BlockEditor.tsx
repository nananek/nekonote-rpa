import { useCallback, useEffect, useState } from 'react'
import { useFlowStore } from '../../stores/flowStore'
import { BlockList } from './BlockList'
import { t } from '../../i18n'

export function BlockEditor(): JSX.Element {
  const flow = useFlowStore((s) => s.flow)
  const selectedBlockId = useFlowStore((s) => s.selectedBlockId)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)

  // Keyboard shortcuts for block operations
  useEffect(() => {
    const handler = (e: KeyboardEvent): void => {
      const store = useFlowStore.getState()
      if (!store.selectedBlockId) return

      if (e.ctrlKey && e.key === 'd') {
        e.preventDefault()
        store.duplicateBlock(store.selectedBlockId)
      } else if (e.ctrlKey && e.key === 'c' && !window.getSelection()?.toString()) {
        e.preventDefault()
        store.copyBlock(store.selectedBlockId)
      } else if (e.ctrlKey && e.key === 'v') {
        e.preventDefault()
        store.pasteBlock()
      } else if (e.ctrlKey && e.key === '/') {
        e.preventDefault()
        store.toggleDisabled(store.selectedBlockId)
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
          e.preventDefault()
          store.removeBlock(store.selectedBlockId)
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Ctrl+F for search
  useEffect(() => {
    const handler = (e: KeyboardEvent): void => {
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        setShowSearch(true)
      } else if (e.key === 'Escape') {
        setShowSearch(false)
        setSearchQuery('')
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const searchResults = searchQuery ? useFlowStore.getState().searchBlocks(searchQuery) : []

  return (
    <div
      style={{
        flex: 1,
        overflow: 'auto',
        padding: '16px 24px',
        backgroundColor: '#0f0f23',
        position: 'relative'
      }}
      onClick={() => useFlowStore.getState().selectBlock(null)}
    >
      {/* Search bar */}
      {showSearch && (
        <div style={{
          position: 'sticky', top: 0, zIndex: 10,
          display: 'flex', gap: 8, alignItems: 'center',
          padding: '8px 12px', marginBottom: 8,
          backgroundColor: '#1e293b', borderRadius: 6, border: '1px solid #334155',
        }}>
          <input
            autoFocus
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search blocks... (Esc to close)"
            onClick={(e) => e.stopPropagation()}
            style={{
              flex: 1, padding: '4px 8px', fontSize: 13,
              backgroundColor: '#0f0f23', color: '#e2e8f0',
              border: '1px solid #334155', borderRadius: 4, outline: 'none',
            }}
          />
          <span style={{ fontSize: 11, color: '#64748b' }}>
            {searchQuery ? `${searchResults.length} found` : ''}
          </span>
          <button
            onClick={() => { setShowSearch(false); setSearchQuery('') }}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 14 }}
          >
            ×
          </button>
        </div>
      )}

      <div style={{ maxWidth: 700, margin: '0 auto' }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 12 }}>
          {flow.name || t('app.title')}
        </div>
        <BlockList blocks={flow.blocks} depth={0} />
      </div>
    </div>
  )
}
