import React, { useCallback, useEffect, useRef, useState } from 'react';
import Navbar from './components/Navbar';
import DrawingCanvas from './components/DrawingCanvas';
import GraphExplorer from './components/GraphExplorer';
import AiChatDrawer from './components/AiChatDrawer';
import DataInspector from './components/DataInspector';
import { checkHealth, fetchAnalysis, pollJob, uploadDrawing } from './lib/api';
import { normalizeAnalysis, normalizeSample } from './lib/normalizeAnalysis';

import {
  SAMPLE_DRAWING,
  SAMPLE_TEXTS,
  SAMPLE_OBJECTS,
  SAMPLE_LINES,
  SAMPLE_RELATIONSHIPS,
  SAMPLE_GRAPH,
} from './data/sample_data';

const SAMPLE = normalizeSample({
  drawing: SAMPLE_DRAWING,
  texts: SAMPLE_TEXTS,
  objects: SAMPLE_OBJECTS,
  lines: SAMPLE_LINES,
  relationships: SAMPLE_RELATIONSHIPS,
  graph: SAMPLE_GRAPH,
});

export default function App() {
  const [activeTab, setActiveTab] = useState('canvas');
  const [data, setData] = useState(SAMPLE);
  const [dataSource, setDataSource] = useState('sample');
  const [apiOnline, setApiOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const fileRef = useRef(null);

  const loadFromApi = useCallback(async () => {
    try {
      const raw = await fetchAnalysis();
      const normalized = normalizeAnalysis(raw);
      if (normalized) {
        setData(normalized);
        setDataSource('api');
      }
    } catch {
      // keep sample data
    }
  }, []);

  useEffect(() => {
    checkHealth()
      .then((h) => {
        setApiOnline(h.status === 'ok');
        if (h.has_analysis) return loadFromApi();
        return null;
      })
      .catch(() => setApiOnline(false));
  }, [loadFromApi]);

  const handleUploadClick = () => {
    if (!apiOnline) {
      setStatusMsg('Start the API: python scripts/run_api.py');
      return;
    }
    fileRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setLoading(true);
    setStatusMsg(`Uploading ${file.name}…`);

    try {
      const { job_id } = await uploadDrawing(file);
      setStatusMsg('Running Python pipeline (OCR, lines, symbols, graph)…');

      const result = await pollJob(job_id, {
        intervalMs: 2500,
        onProgress: (job) => {
          if (job.status === 'pending') {
            setStatusMsg('Pipeline running — this may take several minutes…');
          }
        },
      });

      const normalized = normalizeAnalysis(result);
      setData(normalized);
      setDataSource('api');
      setStatusMsg(`Analysis complete — ${normalized.drawing.filename}`);
      setActiveTab('canvas');
    } catch (err) {
      setStatusMsg(err.message || 'Upload failed');
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(''), 8000);
    }
  };

  const { drawing, texts, objects, lines, relationships, graph, fullAnalysis } = data;

  return (
    <div className="app-shell h-screen text-[var(--text)] flex flex-col font-[family-name:var(--font-sans)]">
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp"
        className="hidden"
        onChange={handleFileChange}
      />

      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={drawing.statistics}
        onUploadClick={handleUploadClick}
        loading={loading}
        dataSource={dataSource}
        apiOnline={apiOnline}
      />

      {statusMsg && (
        <div className="px-5 py-2 text-[12px] bg-[var(--accent-soft)] text-[var(--accent)] border-b border-[var(--accent)]/20">
          {statusMsg}
        </div>
      )}

      <main className="flex-1 relative overflow-hidden animate-in" key={activeTab}>
        {activeTab === 'canvas' && (
          <DrawingCanvas
            drawing={drawing}
            texts={texts}
            objects={objects}
            lines={lines}
            relationships={relationships}
          />
        )}

        {activeTab === 'graph' && (
          <GraphExplorer graph={graph} objects={objects} texts={texts} lines={lines} />
        )}

        {activeTab === 'grok' && <AiChatDrawer apiOnline={apiOnline} hasAnalysis={dataSource === 'api'} />}

        {activeTab === 'json' && (
          <DataInspector
            fullAnalysis={fullAnalysis}
            classifiedText={texts}
            objects={objects}
            lines={lines}
            relationships={relationships}
            graph={graph}
          />
        )}
      </main>
    </div>
  );
}
