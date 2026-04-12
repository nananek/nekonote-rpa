import { useState } from 'react'
import { NODE_DEFS, NODE_CATEGORIES, type NodeDef } from '../../types/nodeDefinitions'
import { useFlowStore } from '../../stores/flowStore'
import { getNodeDef } from '../../types/nodeDefinitions'
import { t } from '../../i18n'

function nodeLabel(def: NodeDef): string {
  return t(`node.${def.type}`)
}

let blockIdCounter = 200

function PaletteItem({ def }: { def: NodeDef }): JSX.Element {
  const addBlock = useFlowStore((s) => s.addBlock)

  const handleClick = (): void => {
    const defaultParams: Record<string, unknown> = {}
    for (const p of def.params) {
      if (p.default !== undefined) defaultParams[p.name] = p.default
    }

    const newBlock = {
      id: `block_${++blockIdCounter}_${Date.now()}`,
      type: def.type,
      label: nodeLabel(def),
      params: defaultParams,
      ...(def.outputs.includes('true') || def.outputs.includes('loop') || def.outputs.includes('try')
        ? { children: [], elseChildren: [] }
        : {})
    }

    addBlock(newBlock)
  }

  return (
    <div
      onClick={handleClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 10px',
        borderRadius: 6,
        cursor: 'pointer',
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        fontSize: 12,
        color: '#e2e8f0',
        transition: 'background-color 0.1s'
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.backgroundColor = '#334155'
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.backgroundColor = '#1e293b'
      }}
    >
      <span
        style={{
          width: 20,
          height: 20,
          borderRadius: 4,
          backgroundColor: def.color,
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 11,
          fontWeight: 700,
          flexShrink: 0
        }}
      >
        {def.icon}
      </span>
      <span>{nodeLabel(def)}</span>
    </div>
  )
}

export function NodePalette(): JSX.Element {
  const [search, setSearch] = useState('')
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  const filtered = search
    ? NODE_DEFS.filter(
        (d) =>
          nodeLabel(d).toLowerCase().includes(search.toLowerCase()) ||
          d.type.toLowerCase().includes(search.toLowerCase())
      )
    : NODE_DEFS

  const grouped: Record<string, NodeDef[]> = {}
  for (const def of filtered) {
    if (!grouped[def.category]) grouped[def.category] = []
    grouped[def.category].push(def)
  }

  return (
    <div
      style={{
        width: 220,
        backgroundColor: '#0f172a',
        borderRight: '1px solid #334155',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      <div style={{ padding: '10px 10px 6px', fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>
        {t('palette.title')}
      </div>

      <div style={{ padding: '0 10px 8px' }}>
        <input
          type="text"
          placeholder={t('palette.search')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
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

      <div style={{ flex: 1, overflow: 'auto', padding: '0 10px 10px' }}>
        {Object.entries(grouped).map(([cat, defs]) => {
          const catInfo = NODE_CATEGORIES[cat]
          const isCollapsed = collapsed[cat]

          return (
            <div key={cat} style={{ marginBottom: 8 }}>
              <div
                onClick={() => setCollapsed((c) => ({ ...c, [cat]: !c[cat] }))}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '4px 0',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 600,
                  color: catInfo?.color ?? '#aaa',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  userSelect: 'none'
                }}
              >
                <span style={{ fontSize: 9 }}>{isCollapsed ? '▶' : '▼'}</span>
                {t(`category.${cat}`)}
                <span style={{ color: '#64748b', fontWeight: 400 }}>({defs.length})</span>
              </div>

              {!isCollapsed && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {defs.map((def) => (
                    <PaletteItem key={def.type} def={def} />
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
