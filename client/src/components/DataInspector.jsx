import React, { useState } from 'react';
import { Copy, Check, Download } from 'lucide-react';

const ARTIFACTS = [
  { id: 'final_analysis', label: 'final_analysis' },
  { id: 'classified_text', label: 'classified_text' },
  { id: 'objects', label: 'objects' },
  { id: 'lines', label: 'lines' },
  { id: 'relationships', label: 'relationships' },
  { id: 'graph', label: 'graph' },
];

export default function DataInspector({
  fullAnalysis,
  classifiedText,
  objects,
  lines,
  relationships,
  graph,
}) {
  const [activeArtifact, setActiveArtifact] = useState('final_analysis');
  const [copied, setCopied] = useState(false);

  const getArtifactData = () => {
    switch (activeArtifact) {
      case 'classified_text':
        return classifiedText;
      case 'objects':
        return objects;
      case 'lines':
        return lines;
      case 'relationships':
        return relationships;
      case 'graph':
        return graph;
      default:
        return fullAnalysis;
    }
  };

  const currentData = getArtifactData();
  const jsonString = JSON.stringify(currentData, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeArtifact}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full h-[calc(100vh-57px)] flex flex-col p-5 gap-4 overflow-hidden">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-[17px] font-semibold tracking-tight text-[var(--text)]">Data</h2>
          <p className="text-[13px] text-[var(--text-muted)] mt-0.5">
            Inspect and export pipeline JSON artifacts
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] hover:bg-[var(--bg-muted)] text-[12px] text-[var(--text-secondary)] transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[var(--accent)]" /> : <Copy className="w-3.5 h-3.5" strokeWidth={1.75} />}
            {copied ? 'Copied' : 'Copy'}
          </button>

          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--ink)] hover:bg-[var(--text)] text-[12px] font-medium text-white transition-colors"
          >
            <Download className="w-3.5 h-3.5" strokeWidth={1.75} />
            Download
          </button>
        </div>
      </div>

      <div className="flex-1 panel flex flex-col overflow-hidden min-h-0">
        <div className="flex items-center gap-1 p-2 border-b border-[var(--border)] overflow-x-auto">
          {ARTIFACTS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveArtifact(tab.id)}
              className={`px-2.5 py-1.5 rounded-md text-[12px] font-[family-name:var(--font-mono)] transition-colors whitespace-nowrap ${
                activeArtifact === tab.id
                  ? 'bg-[var(--bg-muted)] text-[var(--text)] font-medium'
                  : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-muted)]/60'
              }`}
            >
              {tab.label}.json
            </button>
          ))}
        </div>

        <div className="flex-1 p-4 overflow-auto bg-[var(--bg)] font-[family-name:var(--font-mono)] text-[12px] text-[var(--text-secondary)] leading-relaxed">
          <pre>{jsonString}</pre>
        </div>
      </div>
    </div>
  );
}
