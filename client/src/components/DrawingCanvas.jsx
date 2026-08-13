import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Info,
  Tag,
  Box,
  GitCommit,
  Layers,
  X,
  BoxSelect,
  Cuboid,
  Focus,
  Search,
} from 'lucide-react';
import { createPidScene } from '../lib/pidScene';
import '../lib/pidScene.css';

function Minimap({ view, objects, lines, onJump }) {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !view) return;
    const ctx = canvas.getContext('2d');
    const { drawingW: W, drawingH: H } = view;
    const w = canvas.width;
    const h = canvas.height;
    const sx = w / W;
    const sy = h / H;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = '#e2e6eb';
    ctx.strokeRect(0.5, 0.5, w - 1, h - 1);

    ctx.strokeStyle = '#0f6e56';
    ctx.lineWidth = 1;
    lines.forEach((line) => {
      if (line.line_type === 'BORDER') ctx.strokeStyle = '#b42318';
      else if (line.line_type === 'DIMENSION') ctx.strokeStyle = '#1d4ed8';
      else ctx.strokeStyle = '#0f6e56';
      ctx.beginPath();
      ctx.moveTo(line.start[0] * sx, line.start[1] * sy);
      ctx.lineTo(line.end[0] * sx, line.end[1] * sy);
      ctx.stroke();
    });

    objects.forEach((obj) => {
      ctx.fillStyle = '#1c2430';
      ctx.fillRect(obj.bbox.x * sx, obj.bbox.y * sy, Math.max(2, obj.bbox.width * sx), Math.max(2, obj.bbox.height * sy));
    });

    const vx = (view.cx - view.halfW) * sx;
    const vy = (H - (view.cy + view.halfH)) * sy;
    const vw = view.halfW * 2 * sx;
    const vh = view.halfH * 2 * sy;
    ctx.strokeStyle = '#0f6e56';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(vx, vy, vw, vh);
    ctx.fillStyle = 'rgba(15, 110, 86, 0.08)';
    ctx.fillRect(vx, vy, vw, vh);
  }, [view, objects, lines]);

  const handleClick = (e) => {
    const rect = ref.current.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width;
    const ny = (e.clientY - rect.top) / rect.height;
    onJump?.(nx, ny);
  };

  return (
    <canvas
      ref={ref}
      width={180}
      height={128}
      onClick={handleClick}
      className="w-full rounded-md border border-[var(--border)] cursor-crosshair bg-white"
      title="Click to jump"
    />
  );
}

export default function DrawingCanvas({ drawing, texts, objects, lines, relationships }) {
  const mountRef = useRef(null);
  const apiRef = useRef(null);

  const [zoomPct, setZoomPct] = useState(100);
  const [view, setView] = useState(null);
  const [tilt, setTilt] = useState(false);
  const [showTexts, setShowTexts] = useState(true);
  const [showObjects, setShowObjects] = useState(true);
  const [showLines, setShowLines] = useState(true);
  const [showConnections, setShowConnections] = useState(false);
  const [labelDensity, setLabelDensity] = useState('clean');
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return undefined;

    const { api, dispose } = createPidScene(
      el,
      { drawing, texts, objects, lines, relationships },
      {
        onSelect: setSelectedEntity,
        onZoomChange: (z) => setZoomPct(Math.round(z * 100)),
        onViewChange: setView,
        labelDensity: 'clean',
      }
    );
    apiRef.current = api;
    api.setLabelDensity(labelDensity);
    api.setLayers({
      texts: showTexts,
      objects: showObjects,
      lines: showLines,
      links: showConnections,
    });
    api.setTilt(tilt);

    return () => {
      apiRef.current = null;
      dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drawing, texts, objects, lines, relationships]);

  useEffect(() => {
    apiRef.current?.setLayers({
      texts: showTexts,
      objects: showObjects,
      lines: showLines,
      links: showConnections,
    });
  }, [showTexts, showObjects, showLines, showConnections]);

  useEffect(() => {
    apiRef.current?.setTilt(tilt);
  }, [tilt]);

  useEffect(() => {
    apiRef.current?.setLabelDensity(labelDensity);
  }, [labelDensity]);

  const densityOptions = [
    { id: 'clean', label: 'Clean', hint: 'Tags & equipment only' },
    { id: 'balanced', label: 'Balanced', hint: 'More labels as you zoom' },
    { id: 'all', label: 'All', hint: 'Everything in view' },
  ];

  const layers = [
    { key: 'texts', label: 'Labels', count: texts.length, checked: showTexts, set: setShowTexts, icon: Tag },
    { key: 'objects', label: 'Symbols', count: objects.length, checked: showObjects, set: setShowObjects, icon: Box },
    { key: 'lines', label: 'Lines', count: lines.length, checked: showLines, set: setShowLines, icon: GitCommit },
    {
      key: 'links',
      label: 'Links',
      count: relationships.length,
      checked: showConnections,
      set: setShowConnections,
      icon: Layers,
    },
  ];

  const legend = [
    { color: '#0f6e56', label: 'Pipe / Instrument' },
    { color: '#1c2430', label: 'Equipment' },
    { color: '#b45309', label: 'Valve / Link' },
    { color: '#1d4ed8', label: 'Tank / Dimension' },
    { color: '#b42318', label: 'Border' },
  ];

  const catalog = useMemo(() => {
    const items = [
      ...objects.map((o) => ({
        id: o.id,
        label: o.associated_text?.text || o.type,
        kind: 'OBJECT',
        meta: o.type,
      })),
      ...texts.map((t) => ({
        id: t.id,
        label: t.text,
        kind: 'TEXT',
        meta: t.classification,
      })),
      ...lines.map((l) => ({
        id: l.id,
        label: l.id,
        kind: 'LINE',
        meta: l.line_type,
      })),
    ];
    const q = query.trim().toLowerCase();
    if (!q) return items.slice(0, 12);
    return items.filter((i) => i.id.toLowerCase().includes(q) || i.label.toLowerCase().includes(q)).slice(0, 16);
  }, [objects, texts, lines, query]);

  const related = useMemo(() => {
    if (!selectedEntity?.id) return [];
    return relationships.filter(
      (r) => r.from_id === selectedEntity.id || r.to_id === selectedEntity.id || selectedEntity.id.includes('→')
    );
  }, [selectedEntity, relationships]);

  const jumpTo = (id) => {
    apiRef.current?.selectById(id);
  };

  return (
    <div className="relative w-full h-[calc(100vh-57px)] overflow-hidden flex bg-[var(--bg-canvas)]">
      <div className="flex-1 h-full relative min-w-0">
        <div ref={mountRef} className="absolute inset-0" />

        <div className="absolute top-4 left-4 panel px-2.5 py-1.5 z-40 flex items-center gap-2 pointer-events-none">
          <BoxSelect className="w-3.5 h-3.5 text-[var(--text-muted)]" strokeWidth={1.75} />
          <span className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-muted)]">
            {drawing.resolution.width} × {drawing.resolution.height}
            {view?.visibleLabels != null && (
              <span className="ml-2">
                · {view.visibleLabels}/{view.totalLabels ?? texts.length} labels
              </span>
            )}
          </span>
        </div>

        <div className="absolute top-4 right-[18.5rem] panel p-1.5 z-40 hidden md:block w-[188px]">
          <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] px-1 mb-1.5">Overview</p>
          <Minimap
            view={view}
            objects={objects}
            lines={lines}
            onJump={(nx, ny) => apiRef.current?.panTo(nx, ny)}
          />
        </div>

        <div className="absolute bottom-5 left-5 panel p-1 flex items-center gap-0.5 z-40">
          <button
            onClick={() => apiRef.current?.zoomBy(1.2)}
            className="p-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" strokeWidth={1.75} />
          </button>
          <button
            onClick={() => apiRef.current?.zoomBy(1 / 1.2)}
            className="p-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" strokeWidth={1.75} />
          </button>
          <button
            onClick={() => apiRef.current?.fitView()}
            className="p-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
            title="Fit drawing"
          >
            <Maximize2 className="w-4 h-4" strokeWidth={1.75} />
          </button>
          <button
            onClick={() => setTilt((v) => !v)}
            className={`p-2 rounded-md transition-colors ${
              tilt
                ? 'bg-[var(--accent-soft)] text-[var(--accent)]'
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)]'
            }`}
            title="Toggle 3D tilt"
          >
            <Cuboid className="w-4 h-4" strokeWidth={1.75} />
          </button>
          {selectedEntity?.id && (
            <button
              onClick={() => apiRef.current?.focusId(selectedEntity.id)}
              className="p-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
              title="Focus selection"
            >
              <Focus className="w-4 h-4" strokeWidth={1.75} />
            </button>
          )}
          <span className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-muted)] px-2.5 tabular-nums">
            {zoomPct}%
          </span>
        </div>
      </div>

      <aside className="w-72 h-full border-l border-[var(--border)] bg-[var(--bg-elevated)] flex flex-col p-4 gap-4 z-40 overflow-y-auto shrink-0">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-3">
            Layers
          </p>
          <div className="flex flex-col gap-1">
            {layers.map(({ key, label, count, checked, set, icon: Icon }) => (
              <label
                key={key}
                className="flex items-center justify-between text-[13px] text-[var(--text-secondary)] cursor-pointer px-2.5 py-2 rounded-lg hover:bg-[var(--bg-muted)] transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Icon className="w-3.5 h-3.5 opacity-60" strokeWidth={1.75} />
                  <span>
                    {label}
                    <span className="text-[var(--text-muted)] ml-1.5 font-[family-name:var(--font-mono)] text-[11px]">
                      {count}
                    </span>
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => set(e.target.checked)}
                  className="accent-[var(--accent)] rounded"
                />
              </label>
            ))}
          </div>
        </div>

        <div className="h-px bg-[var(--border)]" />

        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-2">
            Label density
          </p>
          <div className="flex flex-col gap-1">
            {densityOptions.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setLabelDensity(opt.id)}
                className={`text-left px-2.5 py-2 rounded-lg border transition-colors ${
                  labelDensity === opt.id
                    ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30'
                    : 'border-transparent hover:bg-[var(--bg-muted)]'
                }`}
              >
                <div className="text-[12px] font-medium text-[var(--text)]">{opt.label}</div>
                <div className="text-[10px] text-[var(--text-muted)]">{opt.hint}</div>
              </button>
            ))}
          </div>
          <p className="text-[10px] text-[var(--text-muted)] mt-2 leading-relaxed">
            Zoom in to reveal more. Search jumps to any tag.
          </p>
        </div>

        <div className="h-px bg-[var(--border)]" />

        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-2">
            Find entity
          </p>
          <div className="relative mb-2">
            <Search
              className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-2.5 top-1/2 -translate-y-1/2"
              strokeWidth={1.75}
            />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Tag, OBJ, LINE…"
              className="w-full pl-8 pr-2.5 py-2 rounded-lg bg-[var(--bg-muted)] border border-transparent text-[12px] focus:outline-none focus:border-[var(--border-strong)] focus:bg-white transition-colors"
            />
          </div>
          <div className="flex flex-col gap-1 max-h-40 overflow-y-auto">
            {catalog.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => jumpTo(item.id)}
                className={`text-left px-2.5 py-1.5 rounded-lg border transition-colors ${
                  selectedEntity?.id === item.id
                    ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30'
                    : 'border-transparent hover:bg-[var(--bg-muted)]'
                }`}
              >
                <div className="text-[12px] font-[family-name:var(--font-mono)] text-[var(--text)] truncate">
                  {item.label}
                </div>
                <div className="text-[10px] text-[var(--text-muted)] truncate">
                  {item.id} · {item.meta}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="h-px bg-[var(--border)]" />

        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)] mb-3">
            Legend
          </p>
          <div className="flex flex-col gap-2">
            {legend.map((item) => (
              <div key={item.label} className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
                <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: item.color }} />
                {item.label}
              </div>
            ))}
          </div>
        </div>

        <div className="h-px bg-[var(--border)]" />

        {selectedEntity ? (
          <div className="flex flex-col gap-3 animate-in">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
                Inspector
              </p>
              <button
                onClick={() => {
                  setSelectedEntity(null);
                  apiRef.current?.selectById(null);
                }}
                className="text-[var(--text-muted)] hover:text-[var(--text)] p-1 rounded-md hover:bg-[var(--bg-muted)]"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex flex-col gap-2 font-[family-name:var(--font-mono)] text-[12px]">
              {[
                ['ID', selectedEntity.id],
                ['Kind', selectedEntity.kind],
                [
                  'Type',
                  selectedEntity.type ||
                    selectedEntity.classification ||
                    selectedEntity.line_type ||
                    selectedEntity.relationship,
                ],
                selectedEntity.text ? ['Text', selectedEntity.text] : null,
                selectedEntity.length != null ? ['Length', `${Math.round(selectedEntity.length)} px`] : null,
                selectedEntity.orientation ? ['Orient', selectedEntity.orientation] : null,
                selectedEntity.confidence != null
                  ? ['Confidence', `${(selectedEntity.confidence * 100).toFixed(1)}%`]
                  : null,
                selectedEntity.associated_text
                  ? ['Linked', selectedEntity.associated_text.text]
                  : null,
                selectedEntity.from_id ? ['From', selectedEntity.from_id] : null,
                selectedEntity.to_id ? ['To', selectedEntity.to_id] : null,
                selectedEntity.distance != null
                  ? ['Distance', `${selectedEntity.distance.toFixed?.(1) ?? selectedEntity.distance}`]
                  : null,
              ]
                .filter(Boolean)
                .map(([label, value]) => (
                  <div
                    key={label}
                    className="flex justify-between gap-3 py-1.5 border-b border-[var(--border)]"
                  >
                    <span className="text-[var(--text-muted)]">{label}</span>
                    <span className="text-[var(--text)] text-right truncate">{value}</span>
                  </div>
                ))}

              {selectedEntity.bbox && (
                <div className="pt-1">
                  <span className="text-[var(--text-muted)] block mb-1.5">BBox</span>
                  <div className="bg-[var(--bg-muted)] p-2.5 rounded-lg text-[11px] text-[var(--text-secondary)] leading-relaxed">
                    {selectedEntity.bbox.x}, {selectedEntity.bbox.y}
                    <br />
                    {selectedEntity.bbox.width} × {selectedEntity.bbox.height}
                  </div>
                </div>
              )}

              {selectedEntity.start && selectedEntity.end && (
                <div className="pt-1">
                  <span className="text-[var(--text-muted)] block mb-1.5">Segment</span>
                  <div className="bg-[var(--bg-muted)] p-2.5 rounded-lg text-[11px] text-[var(--text-secondary)] leading-relaxed">
                    ({selectedEntity.start[0]}, {selectedEntity.start[1]})
                    <br />→ ({selectedEntity.end[0]}, {selectedEntity.end[1]})
                  </div>
                </div>
              )}

              {related.length > 0 && (
                <div className="pt-1">
                  <span className="text-[var(--text-muted)] block mb-1.5">Relations</span>
                  <div className="flex flex-col gap-1">
                    {related.slice(0, 6).map((r) => {
                      const other = r.from_id === selectedEntity.id ? r.to_id : r.from_id;
                      return (
                        <button
                          key={`${r.from_id}-${r.to_id}-${r.relationship}`}
                          type="button"
                          onClick={() => jumpTo(other)}
                          className="text-left text-[11px] px-2 py-1.5 rounded-md bg-[var(--bg-muted)] hover:bg-[var(--accent-soft)] transition-colors"
                        >
                          <span className="text-[var(--accent)]">{r.relationship}</span>
                          <span className="text-[var(--text-muted)]"> → </span>
                          {other}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-start gap-2 text-[var(--text-muted)] py-2">
            <Info className="w-4 h-4 opacity-50" strokeWidth={1.75} />
            <p className="text-[12px] leading-relaxed">
              Zoom in for labels. Search to jump to any entity. Toggle density above if still busy.
            </p>
          </div>
        )}
      </aside>
    </div>
  );
}
