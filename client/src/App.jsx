import React, { useState } from 'react';
import Navbar from './components/Navbar';
import DrawingCanvas from './components/DrawingCanvas';
import GraphExplorer from './components/GraphExplorer';
import AiChatDrawer from './components/AiChatDrawer';
import DataInspector from './components/DataInspector';

import { 
  SAMPLE_DRAWING, 
  SAMPLE_TEXTS, 
  SAMPLE_OBJECTS, 
  SAMPLE_LINES, 
  SAMPLE_RELATIONSHIPS, 
  SAMPLE_GRAPH,
  MOCK_GROK_QA 
} from './data/sample_data';

export default function App() {
  const [activeTab, setActiveTab] = useState('canvas');

  const handleUploadClick = () => {
    alert("Full P&ID PDF Uploading will run Python pipeline asynchronously via FastAPI endpoint (Step 13). Currently displaying pre-analyzed drawing sample (4963x3509).");
  };

  return (
    <div className="min-h-screen bg-[#070A12] text-white flex flex-col font-sans">
      {/* Top Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={SAMPLE_DRAWING.statistics}
        onUploadClick={handleUploadClick}
      />

      {/* Main Tab Content Viewport */}
      <main className="flex-1 relative overflow-hidden">
        {activeTab === 'canvas' && (
          <DrawingCanvas
            drawing={SAMPLE_DRAWING}
            texts={SAMPLE_TEXTS}
            objects={SAMPLE_OBJECTS}
            lines={SAMPLE_LINES}
            relationships={SAMPLE_RELATIONSHIPS}
          />
        )}

        {activeTab === 'graph' && (
          <GraphExplorer
            graph={SAMPLE_GRAPH}
            objects={SAMPLE_OBJECTS}
            texts={SAMPLE_TEXTS}
            lines={SAMPLE_LINES}
          />
        )}

        {activeTab === 'grok' && (
          <AiChatDrawer
            qaHistory={MOCK_GROK_QA}
          />
        )}

        {activeTab === 'json' && (
          <DataInspector
            fullAnalysis={{
              drawing: SAMPLE_DRAWING,
              texts: SAMPLE_TEXTS,
              objects: SAMPLE_OBJECTS,
              lines: SAMPLE_LINES,
              relationships: SAMPLE_RELATIONSHIPS,
              graph: SAMPLE_GRAPH,
            }}
            classifiedText={SAMPLE_TEXTS}
            objects={SAMPLE_OBJECTS}
            lines={SAMPLE_LINES}
            relationships={SAMPLE_RELATIONSHIPS}
            graph={SAMPLE_GRAPH}
          />
        )}
      </main>
    </div>
  );
}
