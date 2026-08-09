import React, { useState } from 'react';
import { FileJson, Copy, Check, Download, FileCode } from 'lucide-react';

export default function DataInspector({ fullAnalysis, classifiedText, objects, lines, relationships, graph }) {
  const [activeArtifact, setActiveArtifact] = useState('final_analysis');
  const [copied, setCopied] = useState(false);

  const getArtifactData = () => {
    switch (activeArtifact) {
      case 'classified_text': return classifiedText;
      case 'objects': return objects;
      case 'lines': return lines;
      case 'relationships': return relationships;
      case 'graph': return graph;
      default: return fullAnalysis;
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
    <div className="w-full h-[calc(100vh-65px)] bg-[#070A12] flex flex-col p-6 gap-6 overflow-hidden">
      {/* Top Bar */}
      <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-4 border-cyan-500/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <FileJson className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Raw JSON Output Artifact Inspector
            </h2>
            <p className="text-xs text-gray-400">Inspect, validate, and download all 7 intermediate & final JSON artifacts exported by Vector-PID.</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-mono text-gray-200 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied!' : 'Copy JSON'}
          </button>

          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-xs font-semibold text-white transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Download {activeArtifact}.json
          </button>
        </div>
      </div>

      {/* Selector Tabs & Code Container */}
      <div className="flex-1 glass-panel flex flex-col overflow-hidden border-gray-800">
        {/* Artifact File Tabs */}
        <div className="flex items-center gap-2 p-3 bg-gray-900 border-b border-gray-800 overflow-x-auto">
          {[
            { id: 'final_analysis', label: 'final_analysis.json' },
            { id: 'classified_text', label: 'classified_text.json' },
            { id: 'objects', label: 'objects.json' },
            { id: 'lines', label: 'lines.json' },
            { id: 'relationships', label: 'relationships.json' },
            { id: 'graph', label: 'graph.json' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveArtifact(tab.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all whitespace-nowrap ${
                activeArtifact === tab.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Code Viewport */}
        <div className="flex-1 p-4 overflow-auto bg-gray-950 font-mono text-xs text-cyan-300 leading-relaxed">
          <pre>{jsonString}</pre>
        </div>
      </div>
    </div>
  );
}
