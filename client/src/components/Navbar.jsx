import React from 'react';
import { 
  Layers, 
  Share2, 
  Bot, 
  FileJson, 
  Upload, 
  CheckCircle2, 
  Activity,
  Cpu,
  Compass,
  FileCode2
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, stats, onUploadClick }) {
  return (
    <header className="glass-panel sticky top-0 z-50 px-6 py-3 border-b border-gray-800 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 animate-glow">
          <Compass className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-lg tracking-tight text-white">Vector-PID</h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              v1.0 AI Engine
            </span>
          </div>
          <p className="text-xs text-gray-400">P&ID Topology Extraction & LLM Intelligence</p>
        </div>
      </div>

      {/* Real-time Execution Metric Pills */}
      <div className="hidden lg:flex items-center gap-3 px-4 py-1.5 rounded-xl bg-gray-900/60 border border-gray-800 text-xs">
        <div className="flex items-center gap-1.5 text-emerald-400">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span className="text-gray-300">Texts:</span>
          <span className="font-mono font-bold">{stats.total_texts}</span>
        </div>
        <span className="text-gray-700">|</span>
        <div className="flex items-center gap-1.5 text-cyan-400">
          <Cpu className="w-3.5 h-3.5" />
          <span className="text-gray-300">Symbols:</span>
          <span className="font-mono font-bold">{stats.total_symbols}</span>
        </div>
        <span className="text-gray-700">|</span>
        <div className="flex items-center gap-1.5 text-purple-400">
          <Activity className="w-3.5 h-3.5" />
          <span className="text-gray-300">Lines:</span>
          <span className="font-mono font-bold">{stats.total_lines}</span>
        </div>
        <span className="text-gray-700">|</span>
        <div className="flex items-center gap-1.5 text-amber-400">
          <Share2 className="w-3.5 h-3.5" />
          <span className="text-gray-300">Graph Edges:</span>
          <span className="font-mono font-bold">{stats.graph_edges}</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-gray-900/80 p-1 rounded-xl border border-gray-800">
        <button
          onClick={() => setActiveTab('canvas')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'canvas'
              ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Canvas Viewer
        </button>

        <button
          onClick={() => setActiveTab('graph')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'graph'
              ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          <Share2 className="w-3.5 h-3.5" />
          Topology Graph
        </button>

        <button
          onClick={() => setActiveTab('grok')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'grok'
              ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          <Bot className="w-3.5 h-3.5" />
          Grok AI QA
        </button>

        <button
          onClick={() => setActiveTab('json')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'json'
              ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          <FileJson className="w-3.5 h-3.5" />
          Raw JSON
        </button>
      </nav>

      {/* Action CTA */}
      <div className="flex items-center gap-2">
        <button
          onClick={onUploadClick}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-cyan-500/20 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
        >
          <Upload className="w-3.5 h-3.5" />
          Upload P&ID PDF
        </button>
      </div>
    </header>
  );
}
