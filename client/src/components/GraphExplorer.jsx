import React, { useState } from 'react';
import { Search, ArrowRight } from 'lucide-react';

export default function GraphExplorer({ graph }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState('OBJ-0003');
  const [nodeTypeFilter, setNodeTypeFilter] = useState('ALL');
  const [tracePath, setTracePath] = useState([
    'OBJ-0003',
    'LINE-0003',
    'LINE-0005',
    'OBJ-0005',
    'LINE-0007',
    'OBJ-0004',
    'LINE-0009',
    'OBJ-0002',
  ]);

  const filteredNodes = graph.nodes.filter((node) => {
    const matchesSearch =
      node.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (node.text && node.text.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (node.category && node.category.toLowerCase().includes(searchQuery.toLowerCase()));

    if (nodeTypeFilter === 'ALL') return matchesSearch;
    return matchesSearch && node.node_type === nodeTypeFilter;
  });

  const handleTraceClick = (nodeId) => {
    setSelectedNode(nodeId);
    const relatedEdges = graph.edges.filter((e) => e.from_id === nodeId || e.to_id === nodeId);
    const neighbors = relatedEdges.map((e) => (e.from_id === nodeId ? e.to_id : e.from_id));
    setTracePath([nodeId, ...neighbors]);
  };

  const filters = [
    { id: 'ALL', label: 'All' },
    { id: 'OBJECT', label: 'Symbols' },
    { id: 'TEXT', label: 'Texts' },
    { id: 'LINE', label: 'Lines' },
  ];

  return (
    <div className="w-full h-[calc(100vh-57px)] flex flex-col p-5 gap-4 overflow-hidden">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-[17px] font-semibold tracking-tight text-[var(--text)]">Topology</h2>
          <p className="text-[13px] text-[var(--text-muted)] mt-0.5">
            Trace piping pathways and inspect node relationships
          </p>
        </div>
        <div className="flex items-center gap-3 text-[12px] font-[family-name:var(--font-mono)] text-[var(--text-secondary)]">
          <span>
            {graph.num_nodes} <span className="text-[var(--text-muted)]">nodes</span>
          </span>
          <span className="text-[var(--border-strong)]">·</span>
          <span>
            {graph.num_edges} <span className="text-[var(--text-muted)]">edges</span>
          </span>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 overflow-hidden min-h-0">
        <div className="panel p-4 flex flex-col gap-4 overflow-y-auto">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-1">
              Path tracer
            </p>
            <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed">
              Select a node to follow connected downstream components.
            </p>
          </div>

          <div className="px-3 py-2.5 rounded-lg bg-[var(--bg-muted)]">
            <span className="text-[11px] text-[var(--text-muted)] block mb-0.5">Origin</span>
            <div className="flex items-center justify-between gap-2">
              <span className="text-[13px] font-[family-name:var(--font-mono)] font-medium text-[var(--text)]">
                {selectedNode}
              </span>
              <span className="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
                {graph.nodes.find((n) => n.id === selectedNode)?.category || 'EQUIPMENT'}
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            {tracePath.map((stepId, idx) => {
              const nodeInfo = graph.nodes.find((n) => n.id === stepId);
              const isFirst = idx === 0;
              const isLast = idx === tracePath.length - 1;

              return (
                <React.Fragment key={`trace-${stepId}-${idx}`}>
                  <button
                    type="button"
                    onClick={() => handleTraceClick(stepId)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      isFirst
                        ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30'
                        : isLast
                          ? 'bg-[var(--bg-muted)] border-[var(--border)]'
                          : 'bg-transparent border-[var(--border)] hover:bg-[var(--bg-muted)]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-5 h-5 rounded-full bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center text-[10px] font-[family-name:var(--font-mono)] text-[var(--text-muted)] shrink-0">
                        {idx + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="text-[12px] font-[family-name:var(--font-mono)] font-medium text-[var(--text)] truncate">
                          {stepId}
                          {nodeInfo?.text ? (
                            <span className="text-[var(--text-secondary)] font-normal"> · {nodeInfo.text}</span>
                          ) : null}
                        </div>
                        <span className="text-[11px] text-[var(--text-muted)]">
                          {nodeInfo?.category || nodeInfo?.node_type || 'COMPONENT'}
                        </span>
                      </div>
                    </div>
                  </button>
                  {!isLast && (
                    <div className="flex justify-center py-0.5">
                      <ArrowRight className="w-3.5 h-3.5 text-[var(--text-muted)] rotate-90" strokeWidth={1.5} />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        <div className="lg:col-span-2 panel p-4 flex flex-col gap-3 overflow-hidden min-h-0">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[180px]">
              <Search
                className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2"
                strokeWidth={1.75}
              />
              <input
                type="text"
                placeholder="Search tags, IDs…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-[var(--bg-muted)] border border-transparent text-[13px] text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] focus:bg-[var(--bg-elevated)] transition-colors"
              />
            </div>

            <div className="flex items-center gap-0.5 p-1 rounded-lg bg-[var(--bg-muted)]">
              {filters.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setNodeTypeFilter(f.id)}
                  className={`px-2.5 py-1 rounded-md text-[12px] transition-colors ${
                    nodeTypeFilter === f.id
                      ? 'bg-[var(--bg-elevated)] text-[var(--text)] shadow-sm font-medium'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text)]'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-2 overflow-y-auto pr-0.5 min-h-0 content-start">
            {filteredNodes.map((node) => {
              const isSelected = node.id === selectedNode;

              return (
                <button
                  key={node.id}
                  type="button"
                  onClick={() => handleTraceClick(node.id)}
                  className={`text-left p-3 rounded-lg border transition-colors ${
                    isSelected
                      ? 'bg-[var(--accent-soft)] border-[var(--accent)]/35'
                      : 'bg-transparent border-[var(--border)] hover:bg-[var(--bg-muted)]'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <span className="text-[12px] font-[family-name:var(--font-mono)] font-medium text-[var(--text)] block truncate">
                        {node.id}
                      </span>
                      {node.text && (
                        <span className="text-[12px] text-[var(--text-secondary)] block mt-0.5 truncate">
                          {node.text}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] uppercase tracking-wide text-[var(--text-muted)] shrink-0">
                      {node.category || node.node_type}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-2 mt-2 border-t border-[var(--border)]">
                    <span className="font-[family-name:var(--font-mono)]">
                      {((node.confidence || 0.8) * 100).toFixed(0)}%
                    </span>
                    <span className="flex items-center gap-1 text-[var(--accent)]">
                      Trace <ArrowRight className="w-3 h-3" strokeWidth={1.75} />
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
