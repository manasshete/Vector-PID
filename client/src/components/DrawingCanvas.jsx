import React, { useState, useRef } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Eye, 
  Filter, 
  Info, 
  Layers, 
  Tag, 
  Box, 
  GitCommit, 
  X,
  Sliders
} from 'lucide-react';

export default function DrawingCanvas({ drawing, texts, objects, lines, relationships }) {
  const [scale, setScale] = useState(0.22);
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Layer Toggles
  const [showTexts, setShowTexts] = useState(true);
  const [showObjects, setShowObjects] = useState(true);
  const [showLines, setShowLines] = useState(true);
  const [showConnections, setShowConnections] = useState(true);

  // Selected Entity Inspection
  const [selectedEntity, setSelectedEntity] = useState(null);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPosition({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleZoom = (factor) => {
    setScale((prev) => Math.min(Math.max(prev * factor, 0.08), 1.5));
  };

  const resetView = () => {
    setScale(0.22);
    setPosition({ x: 20, y: 20 });
  };

  const getTextBadgeColor = (classification) => {
    switch (classification) {
      case 'INSTRUMENT_TAG': return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      case 'EQUIPMENT_TAG': return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'LINE_NUMBER': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'DESCRIPTION': return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'SERVICE': return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case 'ANNOTATION': return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      default: return 'bg-gray-700/40 text-gray-300 border-gray-600/40';
    }
  };

  const getObjectColor = (type) => {
    switch (type) {
      case 'INSTRUMENT': return '#06B6D4';
      case 'EQUIPMENT': return '#8B5CF6';
      case 'VALVE': return '#F59E0B';
      case 'TANK': return '#3B82F6';
      case 'PUMP': return '#10B981';
      case 'FLANGE': return '#EC4899';
      default: return '#9CA3AF';
    }
  };

  return (
    <div className="relative w-full h-[calc(100vh-65px)] bg-[#070A12] overflow-hidden select-none flex">
      {/* Main Canvas Area */}
      <div 
        className="flex-1 h-full relative cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Background Grid Pattern */}
        <div 
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle, #374151 1px, transparent 1px)`,
            backgroundSize: `${30 * scale}px ${30 * scale}px`,
            backgroundPosition: `${position.x}px ${position.y}px`
          }}
        />

        {/* Scalable & Pannable P&ID Canvas Workspace */}
        <div 
          className="absolute transform-gpu transition-transform ease-out duration-75 origin-top-left"
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            width: `${drawing.resolution.width}px`,
            height: `${drawing.resolution.height}px`,
          }}
        >
          {/* Virtual Drawing Boundary Frame */}
          <div className="absolute inset-0 border-2 border-dashed border-cyan-500/30 rounded-28 bg-[#0D1322] shadow-2xl overflow-hidden">
            <div className="absolute top-4 left-4 text-xs font-mono text-cyan-400/60 bg-gray-900/80 px-3 py-1 rounded-md border border-cyan-500/20">
              P&ID Resolution: {drawing.resolution.width} x {drawing.resolution.height} px
            </div>

            {/* Layer 1: Vector Line Segments */}
            {showLines && lines.map((line) => {
              const lineColor = line.line_type === 'BORDER' ? '#EF4444' : line.line_type === 'DIMENSION' ? '#3B82F6' : '#10B981';
              return (
                <svg key={line.id} className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
                  <line 
                    x1={line.start[0]} 
                    y1={line.start[1]} 
                    x2={line.end[0]} 
                    y2={line.end[1]} 
                    stroke={lineColor}
                    strokeWidth={line.line_type === 'BORDER' ? 4 : 2}
                    strokeOpacity={0.7}
                    strokeDasharray={line.line_type === 'DIMENSION' ? '4,4' : undefined}
                  />
                </svg>
              );
            })}

            {/* Layer 2: Spatial Connections (Dotted links) */}
            {showConnections && relationships.map((rel, idx) => {
              const fromObj = objects.find(o => o.id === rel.from_id) || lines.find(l => l.id === rel.from_id);
              const toObj = texts.find(t => t.id === rel.to_id) || objects.find(o => o.id === rel.to_id);

              if (!fromObj || !toObj) return null;

              const x1 = fromObj.bbox ? fromObj.bbox.x + fromObj.bbox.width/2 : (fromObj.start[0] + fromObj.end[0])/2;
              const y1 = fromObj.bbox ? fromObj.bbox.y + fromObj.bbox.height/2 : (fromObj.start[1] + fromObj.end[1])/2;
              const x2 = toObj.bbox.x + toObj.bbox.width/2;
              const y2 = toObj.bbox.y + toObj.bbox.height/2;

              return (
                <svg key={`rel-${idx}`} className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
                  <line 
                    x1={x1} y1={y1} x2={x2} y2={y2} 
                    stroke="#F59E0B"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                    strokeOpacity="0.6"
                  />
                </svg>
              );
            })}

            {/* Layer 3: Symbol Objects (BBoxes & Shape Indicators) */}
            {showObjects && objects.map((obj) => {
              const color = getObjectColor(obj.type);
              const isSelected = selectedEntity?.id === obj.id;

              return (
                <div
                  key={obj.id}
                  onClick={(e) => { e.stopPropagation(); setSelectedEntity({ ...obj, kind: 'OBJECT' }); }}
                  className={`absolute rounded-md cursor-pointer transition-all border ${
                    isSelected ? 'ring-4 ring-cyan-400 z-30 scale-105' : 'hover:scale-105 hover:z-20'
                  }`}
                  style={{
                    left: `${obj.bbox.x}px`,
                    top: `${obj.bbox.y}px`,
                    width: `${obj.bbox.width}px`,
                    height: `${obj.bbox.height}px`,
                    borderColor: color,
                    backgroundColor: `${color}15`,
                  }}
                >
                  <div 
                    className="absolute -top-6 left-0 text-[10px] font-mono px-1.5 py-0.5 rounded font-bold uppercase whitespace-nowrap shadow-md"
                    style={{ backgroundColor: color, color: '#000' }}
                  >
                    {obj.type}
                  </div>
                </div>
              );
            })}

            {/* Layer 4: Text Labels & Annotations */}
            {showTexts && texts.map((txt) => {
              const isSelected = selectedEntity?.id === txt.id;
              const badgeStyle = getTextBadgeColor(txt.classification);

              return (
                <div
                  key={txt.id}
                  onClick={(e) => { e.stopPropagation(); setSelectedEntity({ ...txt, kind: 'TEXT' }); }}
                  className={`absolute px-2 py-1 rounded text-xs font-mono border cursor-pointer backdrop-blur-sm whitespace-nowrap transition-all shadow-lg ${badgeStyle} ${
                    isSelected ? 'ring-4 ring-cyan-400 z-30 scale-110' : 'hover:scale-105 hover:z-20'
                  }`}
                  style={{
                    left: `${txt.bbox.x}px`,
                    top: `${txt.bbox.y}px`,
                  }}
                >
                  {txt.text}
                </div>
              );
            })}
          </div>
        </div>

        {/* Floating Canvas Controls */}
        <div className="absolute bottom-6 left-6 glass-panel p-2 flex items-center gap-2 border border-gray-800 shadow-2xl z-40">
          <button 
            onClick={() => handleZoom(1.2)} 
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button 
            onClick={() => handleZoom(0.8)} 
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button 
            onClick={resetView} 
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-cyan-400 px-2 font-bold">
            {Math.round(scale * 100)}%
          </span>
        </div>
      </div>

      {/* Right Toolbar: Layer Control & Entity Inspector Drawer */}
      <aside className="w-80 h-full border-l border-gray-800 bg-gray-900/90 backdrop-blur-md flex flex-col p-4 gap-4 z-40 overflow-y-auto">
        {/* Layer Visibility Toggles */}
        <div className="glass-panel p-4 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-300 uppercase tracking-wider">
            <Sliders className="w-4 h-4 text-cyan-400" />
            Layer Controls
          </div>

          <div className="flex flex-col gap-2">
            <label className="flex items-center justify-between text-xs text-gray-300 cursor-pointer p-2 rounded bg-gray-800/50 hover:bg-gray-800">
              <div className="flex items-center gap-2">
                <Tag className="w-3.5 h-3.5 text-cyan-400" />
                Text Labels ({texts.length})
              </div>
              <input 
                type="checkbox" 
                checked={showTexts} 
                onChange={(e) => setShowTexts(e.target.checked)} 
                className="accent-cyan-500 rounded"
              />
            </label>

            <label className="flex items-center justify-between text-xs text-gray-300 cursor-pointer p-2 rounded bg-gray-800/50 hover:bg-gray-800">
              <div className="flex items-center gap-2">
                <Box className="w-3.5 h-3.5 text-purple-400" />
                Symbols ({objects.length})
              </div>
              <input 
                type="checkbox" 
                checked={showObjects} 
                onChange={(e) => setShowObjects(e.target.checked)} 
                className="accent-purple-500 rounded"
              />
            </label>

            <label className="flex items-center justify-between text-xs text-gray-300 cursor-pointer p-2 rounded bg-gray-800/50 hover:bg-gray-800">
              <div className="flex items-center gap-2">
                <GitCommit className="w-3.5 h-3.5 text-emerald-400" />
                Lines ({lines.length})
              </div>
              <input 
                type="checkbox" 
                checked={showLines} 
                onChange={(e) => setShowLines(e.target.checked)} 
                className="accent-emerald-500 rounded"
              />
            </label>

            <label className="flex items-center justify-between text-xs text-gray-300 cursor-pointer p-2 rounded bg-gray-800/50 hover:bg-gray-800">
              <div className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                Spatial Links ({relationships.length})
              </div>
              <input 
                type="checkbox" 
                checked={showConnections} 
                onChange={(e) => setShowConnections(e.target.checked)} 
                className="accent-amber-500 rounded"
              />
            </label>
          </div>
        </div>

        {/* Selected Entity Details Drawer */}
        {selectedEntity ? (
          <div className="glass-panel p-4 flex flex-col gap-3 border-cyan-500/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-cyan-400">
                <Info className="w-4 h-4" />
                Entity Inspector
              </div>
              <button 
                onClick={() => setSelectedEntity(null)} 
                className="text-gray-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-col gap-2 font-mono text-xs text-gray-300">
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-500">ID:</span>
                <span className="text-cyan-300 font-bold">{selectedEntity.id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-500">Kind:</span>
                <span>{selectedEntity.kind}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-500">Type/Class:</span>
                <span className="text-purple-300 font-bold">
                  {selectedEntity.type || selectedEntity.classification}
                </span>
              </div>
              {selectedEntity.text && (
                <div className="flex justify-between py-1 border-b border-gray-800">
                  <span className="text-gray-500">Text Content:</span>
                  <span className="text-emerald-300 font-bold">{selectedEntity.text}</span>
                </div>
              )}
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-500">Confidence:</span>
                <span className="text-amber-400 font-bold">
                  {(selectedEntity.confidence * 100).toFixed(1)}%
                </span>
              </div>
              {selectedEntity.associated_text && (
                <div className="flex justify-between py-1 border-b border-gray-800">
                  <span className="text-gray-500">Associated Text:</span>
                  <span className="text-cyan-300">{selectedEntity.associated_text.text}</span>
                </div>
              )}
              <div className="py-1">
                <span className="text-gray-500 block mb-1">Coordinates (BBox):</span>
                <div className="bg-gray-950 p-2 rounded text-[11px] text-gray-400">
                  X: {selectedEntity.bbox.x}px | Y: {selectedEntity.bbox.y}px
                  <br />
                  W: {selectedEntity.bbox.width}px | H: {selectedEntity.bbox.height}px
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-panel p-6 flex flex-col items-center justify-center text-center gap-2 text-gray-500">
            <Info className="w-8 h-8 text-gray-600 mb-1" />
            <p className="text-xs">Click any text label, symbol bbox, or line segment on the canvas to inspect metadata.</p>
          </div>
        )}
      </aside>
    </div>
  );
}
