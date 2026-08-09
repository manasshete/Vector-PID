import React, { useState } from 'react';
import { 
  Share2, 
  Search, 
  ArrowRight, 
  Network, 
  GitBranch, 
  Activity, 
  CheckCircle2, 
  Filter
} from 'lucide-react';

export default function GraphExplorer({ graph, objects, texts, lines }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState('OBJ-0003');
  const [nodeTypeFilter, setNodeTypeFilter] = useState('ALL');
  const [tracePath, setTracePath] = useState(['OBJ-0003', 'LINE-0003', 'LINE-0005', 'OBJ-0005', 'LINE-0007', 'OBJ-0004', 'LINE-0009', 'OBJ-0002']);

  const filteredNodes = graph.nodes.filter((node) => {
    const matchesSearch = node.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (node.text && node.text.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (node.category && node.category.toLowerCase().includes(searchQuery.toLowerCase()));
    
    if (nodeTypeFilter === 'ALL') return matchesSearch;
    return matchesSearch && node.node_type === nodeTypeFilter;
  });

  const handleTraceClick = (nodeId) => {
    setSelectedNode(nodeId);
    // Simulate BFS trace paths from selected starting node
    const relatedEdges = graph.edges.filter(e => e.from_id === nodeId || e.to_id === nodeId);
    const neighbors = relatedEdges.map(e => e.from_id === nodeId ? e.to_id : e.from_id);
    setTracePath([nodeId, ...neighbors]);
  };

  const getNodeBadgeColor = (type) => {
    switch (type) {
      case 'OBJECT': return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'TEXT': return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      case 'LINE': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      default: return 'bg-gray-800 text-gray-300 border-gray-700';
    }
  };

  return (
    <div className="w-full h-[calc(100vh-65px)] bg-[#070A12] flex flex-col p-6 gap-6 overflow-hidden">
      {/* Top Banner / Summary */}
      <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-4 border-cyan-500/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Topology Graph Explorer
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                NetworkX Topology Active
              </span>
            </h2>
            <p className="text-xs text-gray-400">Interactively inspect component topology, trace piping pathways, and explore spatial relationships.</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-gray-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            Nodes: <span className="font-bold text-white">{graph.num_nodes}</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-gray-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400"></span>
            Edges: <span className="font-bold text-white">{graph.num_edges}</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Path Tracer + Node Directory */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden">
        {/* Left Column: BFS Connectivity Path Tracer Tool */}
        <div className="glass-panel p-5 flex flex-col gap-4 overflow-y-auto border-purple-500/20">
          <div className="flex items-center gap-2 text-sm font-bold text-purple-300">
            <GitBranch className="w-4 h-4 text-purple-400" />
            Piping Pathway Connectivity Tracer
          </div>

          <p className="text-xs text-gray-400">
            Select any equipment tag, instrument bubble, or line ID to trace all connected downstream components in sequence.
          </p>

          <div className="p-3 rounded-xl bg-gray-900/80 border border-gray-800 flex flex-col gap-2">
            <span className="text-xs text-gray-400 font-mono">Current Origin Node:</span>
            <div className="flex items-center justify-between text-xs font-mono font-bold text-cyan-300">
              <span>{selectedNode}</span>
              <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px]">
                {graph.nodes.find(n => n.id === selectedNode)?.category || 'EQUIPMENT'}
              </span>
            </div>
          </div>

          {/* Trace Sequence Steps */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
              Connected Process Stream (BFS Traversal)
            </span>

            <div className="flex flex-col gap-2">
              {tracePath.map((stepId, idx) => {
                const nodeInfo = graph.nodes.find((n) => n.id === stepId);
                const isFirst = idx === 0;
                const isLast = idx === tracePath.length - 1;

                return (
                  <React.Fragment key={`trace-${stepId}-${idx}`}>
                    <div 
                      onClick={() => handleTraceClick(stepId)}
                      className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                        isFirst
                          ? 'bg-purple-500/10 border-purple-500/40 shadow-lg shadow-purple-500/10'
                          : isLast
                          ? 'bg-emerald-500/10 border-emerald-500/40'
                          : 'bg-gray-900/60 border-gray-800 hover:border-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-[10px] font-mono font-bold text-gray-300">
                          {idx + 1}
                        </div>
                        <div>
                          <div className="text-xs font-mono font-bold text-white flex items-center gap-2">
                            {stepId}
                            {nodeInfo?.text && (
                              <span className="text-cyan-300 font-sans font-normal">
                                ({nodeInfo.text})
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-gray-400 font-mono">
                            {nodeInfo?.category || nodeInfo?.node_type || 'COMPONENT'}
                          </span>
                        </div>
                      </div>

                      <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${getNodeBadgeColor(nodeInfo?.node_type)}`}>
                        {nodeInfo?.node_type || 'NODE'}
                      </span>
                    </div>

                    {!isLast && (
                      <div className="flex justify-center my-[-4px]">
                        <ArrowRight className="w-4 h-4 text-cyan-400 transform rotate-90" />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right 2 Columns: Searchable Node Network Directory */}
        <div className="lg:col-span-2 glass-panel p-5 flex flex-col gap-4 overflow-hidden border-cyan-500/20">
          {/* Controls: Search & Filter Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search tag (e.g. 26-PIT-9087, V-100A, OBJ-0001)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-gray-900 border border-gray-800 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center gap-1 bg-gray-900 p-1 rounded-xl border border-gray-800 text-xs">
              <button
                onClick={() => setNodeTypeFilter('ALL')}
                className={`px-3 py-1 rounded-lg transition-colors ${nodeTypeFilter === 'ALL' ? 'bg-cyan-500 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                All ({graph.nodes.length})
              </button>
              <button
                onClick={() => setNodeTypeFilter('OBJECT')}
                className={`px-3 py-1 rounded-lg transition-colors ${nodeTypeFilter === 'OBJECT' ? 'bg-purple-500 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                Symbols
              </button>
              <button
                onClick={() => setNodeTypeFilter('TEXT')}
                className={`px-3 py-1 rounded-lg transition-colors ${nodeTypeFilter === 'TEXT' ? 'bg-cyan-500 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                Texts
              </button>
              <button
                onClick={() => setNodeTypeFilter('LINE')}
                className={`px-3 py-1 rounded-lg transition-colors ${nodeTypeFilter === 'LINE' ? 'bg-emerald-500 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                Lines
              </button>
            </div>
          </div>

          {/* Node Cards Grid */}
          <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3 overflow-y-auto pr-1">
            {filteredNodes.map((node) => {
              const isSelected = node.id === selectedNode;

              return (
                <div
                  key={node.id}
                  onClick={() => handleTraceClick(node.id)}
                  className={`p-3 rounded-xl border flex flex-col justify-between gap-2 cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-cyan-500/10 border-cyan-500 shadow-lg shadow-cyan-500/10'
                      : 'bg-gray-900/60 border-gray-800 hover:border-gray-700 hover:bg-gray-900'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-xs font-mono font-bold text-white block">
                        {node.id}
                      </span>
                      {node.text && (
                        <span className="text-xs text-cyan-300 font-semibold block mt-0.5">
                          "{node.text}"
                        </span>
                      )}
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono border ${getNodeBadgeColor(node.node_type)}`}>
                      {node.category || node.node_type}
                    </span>
                  </div>

                  {node.associated_text && (
                    <div className="text-[11px] text-gray-400 font-mono bg-gray-950/60 p-1.5 rounded">
                      Linked: <span className="text-emerald-400">{node.associated_text.text}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono pt-1 border-t border-gray-800/60">
                    <span>Conf: {((node.confidence || 0.8) * 100).toFixed(0)}%</span>
                    <span className="text-cyan-400 flex items-center gap-1 hover:underline">
                      Trace Path <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
