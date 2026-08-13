import React from 'react';
import { Layers, Share2, Bot, FileJson, Upload, Loader2 } from 'lucide-react';

const TABS = [
  { id: 'canvas', label: 'Canvas', icon: Layers },
  { id: 'graph', label: 'Graph', icon: Share2 },
  { id: 'grok', label: 'Ask AI', icon: Bot },
  { id: 'json', label: 'Data', icon: FileJson },
];

export default function Navbar({
  activeTab,
  setActiveTab,
  stats,
  onUploadClick,
  loading,
  dataSource,
  apiOnline,
}) {
  return (
    <header className="sticky top-0 z-50 px-5 py-3 flex items-center justify-between gap-4 bg-[var(--bg-elevated)]/90 backdrop-blur-md border-b border-[var(--border)]">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-lg bg-[var(--ink)] flex items-center justify-center shrink-0">
          <span className="text-[11px] font-semibold tracking-tight text-white">VP</span>
        </div>
        <div className="min-w-0">
          <h1 className="text-[15px] font-semibold tracking-tight text-[var(--text)] leading-none">
            Vector-PID
          </h1>
          <p className="text-[11px] text-[var(--text-muted)] mt-0.5 truncate">
            {stats.total_texts} texts · {stats.total_symbols} symbols · {stats.graph_edges} edges
            <span className="mx-1.5">·</span>
            <span className={dataSource === 'api' ? 'text-[var(--accent)]' : ''}>
              {dataSource === 'api' ? 'Live API' : 'Sample'}
            </span>
            {!apiOnline && <span className="text-[var(--warn)]"> · API offline</span>}
          </p>
        </div>
      </div>

      <nav className="flex items-center gap-0.5 p-1 rounded-xl bg-[var(--bg-muted)]">
        {TABS.map(({ id, label, icon: Icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors ${
                active
                  ? 'bg-[var(--bg-elevated)] text-[var(--text)] shadow-sm'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text)]'
              }`}
            >
              <Icon className="w-3.5 h-3.5 opacity-70" strokeWidth={1.75} />
              <span className="hidden sm:inline">{label}</span>
            </button>
          );
        })}
      </nav>

      <button
        onClick={onUploadClick}
        disabled={loading}
        className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[var(--ink)] hover:bg-[var(--text)] text-white text-[12px] font-medium transition-colors shrink-0 disabled:opacity-60"
      >
        {loading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.75} />
        ) : (
          <Upload className="w-3.5 h-3.5" strokeWidth={1.75} />
        )}
        <span className="hidden md:inline">{loading ? 'Analyzing…' : 'Upload'}</span>
      </button>
    </header>
  );
}
