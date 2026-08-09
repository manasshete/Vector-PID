/**
 * Sample dataset for Vector-PID Engineering Drawing Intelligence Platform.
 * Extracted from Export Gas Compressor P&ID (4963 x 3509 resolution).
 */

export const SAMPLE_DRAWING = {
  filename: "Export Gas Compressor-P&ID.pdf",
  type: "Process & Instrumentation Diagram (P&ID)",
  resolution: { width: 4963, height: 3509 },
  statistics: {
    total_texts: 633,
    total_symbols: 515,
    total_lines: 2928,
    total_relationships: 6118,
    graph_nodes: 4076,
    graph_edges: 6118,
    text_categories: {
      UNKNOWN: 395,
      GRID_LABEL: 81,
      DRAWING_REFERENCE: 41,
      SERVICE: 34,
      ANNOTATION: 33,
      LINE_NUMBER: 28,
      DESCRIPTION: 25,
      INSTRUMENT_TAG: 12,
      EQUIPMENT_TAG: 6,
      PIPE_SIZE: 4,
      SPEC_REFERENCE: 2,
    },
    symbol_types: {
      FLANGE: 342,
      INSTRUMENT: 72,
      EQUIPMENT: 58,
      TANK: 21,
      VALVE: 15,
      PUMP: 7,
    },
    line_types: {
      LIKELY_PIPE: 2922,
      BORDER: 4,
      DIMENSION: 2,
    },
  },
};

export const SAMPLE_TEXTS = [
  { id: "TXT-000-0001", text: "STAGE HP GAS EXPORT", classification: "DESCRIPTION", confidence: 0.82, bbox: { x: 106, y: 94, width: 232, height: 26 }, tile_id: 0 },
  { id: "TXT-000-0002", text: "COMPRESSOR INLET HEADER", classification: "DESCRIPTION", confidence: 0.82, bbox: { x: 106, y: 120, width: 290, height: 26 }, tile_id: 0 },
  { id: "TXT-000-0003", text: "26-PY-9087B", classification: "INSTRUMENT_TAG", confidence: 0.90, bbox: { x: 583, y: 127, width: 132, height: 26 }, tile_id: 0 },
  { id: "TXT-000-0004", text: "26-000001-001", classification: "LINE_NUMBER", confidence: 0.88, bbox: { x: 750, y: 180, width: 160, height: 24 }, tile_id: 0 },
  { id: "TXT-000-0005", text: "SP 108.5", classification: "SPEC_REFERENCE", confidence: 0.93, bbox: { x: 920, y: 180, width: 90, height: 24 }, tile_id: 0 },
  { id: "TXT-001-0010", text: "26-KZ-902", classification: "EQUIPMENT_TAG", confidence: 0.91, bbox: { x: 1450, y: 850, width: 140, height: 30 }, tile_id: 1 },
  { id: "TXT-001-0012", text: "3\"-DO-56-9051", classification: "LINE_NUMBER", confidence: 0.94, bbox: { x: 1650, y: 920, width: 210, height: 28 }, tile_id: 1 },
  { id: "TXT-002-0018", text: "INSTRUMENT AIR", classification: "SERVICE", confidence: 0.92, bbox: { x: 2100, y: 1100, width: 180, height: 25 }, tile_id: 2 },
  { id: "TXT-002-0020", text: "NOTE 18", classification: "ANNOTATION", confidence: 0.95, bbox: { x: 2350, y: 1150, width: 90, height: 24 }, tile_id: 2 },
  { id: "TXT-003-0025", text: "6\"-PG-26-9001", classification: "LINE_NUMBER", confidence: 0.94, bbox: { x: 2800, y: 1400, width: 190, height: 28 }, tile_id: 3 },
  { id: "TXT-003-0028", text: "V-100A", classification: "EQUIPMENT_TAG", confidence: 0.91, bbox: { x: 3100, y: 1550, width: 110, height: 32 }, tile_id: 3 },
  { id: "TXT-004-0035", text: "26-PIT-9087", classification: "INSTRUMENT_TAG", confidence: 0.92, bbox: { x: 3800, y: 2200, width: 145, height: 28 }, tile_id: 4 },
  { id: "TXT-004-0040", text: "HP GAS EXPORT COMPRESSOR", classification: "DESCRIPTION", confidence: 0.88, bbox: { x: 4100, y: 2400, width: 310, height: 30 }, tile_id: 4 },
];

export const SAMPLE_OBJECTS = [
  { id: "OBJ-0001", type: "INSTRUMENT", bbox: { x: 3953, y: 3435, width: 45, height: 45 }, confidence: 0.65, associated_text: { id: "TXT-004-0035", text: "26-PIT-9087", distance: 12.4 } },
  { id: "OBJ-0002", type: "EQUIPMENT", bbox: { x: 4592, y: 3163, width: 180, height: 240 }, confidence: 0.60, associated_text: { id: "TXT-004-0040", text: "HP GAS EXPORT COMPRESSOR", distance: 18.2 } },
  { id: "OBJ-0003", type: "EQUIPMENT", bbox: { x: 1400, y: 800, width: 220, height: 160 }, confidence: 0.55, associated_text: { id: "TXT-001-0010", text: "26-KZ-902", distance: 15.0 } },
  { id: "OBJ-0004", type: "TANK", bbox: { x: 3050, y: 1500, width: 160, height: 280 }, confidence: 0.60, associated_text: { id: "TXT-003-0028", text: "V-100A", distance: 22.1 } },
  { id: "OBJ-0005", type: "VALVE", bbox: { x: 1700, y: 910, width: 35, height: 35 }, confidence: 0.55, associated_text: { id: "TXT-001-0012", text: "3\"-DO-56-9051", distance: 14.5 } },
  { id: "OBJ-0006", type: "FLANGE", bbox: { x: 2850, y: 1410, width: 15, height: 25 }, confidence: 0.45, associated_text: { id: "TXT-003-0025", text: "6\"-PG-26-9001", distance: 8.0 } },
  { id: "OBJ-0007", type: "PUMP", bbox: { x: 2150, y: 1120, width: 75, height: 75 }, confidence: 0.50, associated_text: { id: "TXT-002-0018", text: "INSTRUMENT AIR", distance: 19.3 } },
];

export const SAMPLE_LINES = [
  { id: "LINE-0001", start: [50, 50], end: [4900, 50], length: 4850, orientation: "horizontal", line_type: "BORDER", confidence: 0.85 },
  { id: "LINE-0002", start: [59, 3423], end: [4900, 3426], length: 4841, orientation: "horizontal", line_type: "LIKELY_PIPE", confidence: 0.75 },
  { id: "LINE-0003", start: [100, 125], end: [1400, 125], length: 1300, orientation: "horizontal", line_type: "LIKELY_PIPE", confidence: 0.75 },
  { id: "LINE-0004", start: [1400, 125], end: [1400, 800], length: 675, orientation: "vertical", line_type: "LIKELY_PIPE", confidence: 0.75 },
  { id: "LINE-0005", start: [1620, 880], end: [2800, 880], length: 1180, orientation: "horizontal", line_type: "LIKELY_PIPE", confidence: 0.75 },
  { id: "LINE-0006", start: [2800, 880], end: [2800, 1400], length: 520, orientation: "vertical", line_type: "LIKELY_PIPE", confidence: 0.75 },
  { id: "LINE-0007", start: [2990, 1415], end: [3050, 1550], length: 148, orientation: "diagonal", line_type: "LIKELY_PIPE", confidence: 0.75 },
  { id: "LINE-0008", start: [3210, 1600], end: [3950, 1600], length: 740, orientation: "horizontal", line_type: "LIKELY_PIPE", confidence: 0.75 },
  { id: "LINE-0009", start: [3950, 1600], end: [4590, 3160], length: 1686, orientation: "diagonal", line_type: "LIKELY_PIPE", confidence: 0.75 },
];

export const SAMPLE_RELATIONSHIPS = [
  { from_id: "OBJ-0001", to_id: "TXT-004-0035", relationship: "annotated_by", distance: 12.4, confidence: 0.90 },
  { from_id: "OBJ-0002", to_id: "TXT-004-0040", relationship: "annotated_by", distance: 18.2, confidence: 0.90 },
  { from_id: "OBJ-0003", to_id: "TXT-001-0010", relationship: "annotated_by", distance: 15.0, confidence: 0.90 },
  { from_id: "OBJ-0004", to_id: "TXT-003-0028", relationship: "annotated_by", distance: 22.1, confidence: 0.90 },
  { from_id: "LINE-0003", to_id: "OBJ-0003", relationship: "connected_to", distance: 5.0, confidence: 0.85 },
  { from_id: "LINE-0005", to_id: "OBJ-0003", relationship: "connected_to", distance: 20.0, confidence: 0.85 },
  { from_id: "LINE-0005", to_id: "OBJ-0005", relationship: "connected_to", distance: 14.5, confidence: 0.85 },
  { from_id: "LINE-0007", to_id: "OBJ-0004", relationship: "connected_to", distance: 8.0, confidence: 0.85 },
  { from_id: "LINE-0009", to_id: "OBJ-0002", relationship: "connected_to", distance: 12.0, confidence: 0.85 },
  { from_id: "OBJ-0001", to_id: "OBJ-0002", relationship: "near", distance: 412.0, confidence: 0.70 },
  { from_id: "OBJ-0003", to_id: "OBJ-0005", relationship: "near", distance: 310.0, confidence: 0.70 },
];

export const SAMPLE_GRAPH = {
  num_nodes: 23,
  num_edges: 11,
  nodes: [
    { id: "OBJ-0001", node_type: "OBJECT", category: "INSTRUMENT", confidence: 0.65, associated_text: { text: "26-PIT-9087" } },
    { id: "OBJ-0002", node_type: "OBJECT", category: "EQUIPMENT", confidence: 0.60, associated_text: { text: "HP GAS EXPORT COMPRESSOR" } },
    { id: "OBJ-0003", node_type: "OBJECT", category: "EQUIPMENT", confidence: 0.55, associated_text: { text: "26-KZ-902" } },
    { id: "OBJ-0004", node_type: "OBJECT", category: "TANK", confidence: 0.60, associated_text: { text: "V-100A" } },
    { id: "OBJ-0005", node_type: "OBJECT", category: "VALVE", confidence: 0.55, associated_text: { text: "3\"-DO-56-9051" } },
    { id: "TXT-000-0001", node_type: "TEXT", category: "DESCRIPTION", text: "STAGE HP GAS EXPORT", confidence: 0.82 },
    { id: "TXT-000-0002", node_type: "TEXT", category: "DESCRIPTION", text: "COMPRESSOR INLET HEADER", confidence: 0.82 },
    { id: "TXT-000-0003", node_type: "TEXT", category: "INSTRUMENT_TAG", text: "26-PY-9087B", confidence: 0.90 },
    { id: "TXT-001-0010", node_type: "TEXT", category: "EQUIPMENT_TAG", text: "26-KZ-902", confidence: 0.91 },
    { id: "TXT-003-0028", node_type: "TEXT", category: "EQUIPMENT_TAG", text: "V-100A", confidence: 0.91 },
    { id: "TXT-004-0035", node_type: "TEXT", category: "INSTRUMENT_TAG", text: "26-PIT-9087", confidence: 0.92 },
    { id: "LINE-0003", node_type: "LINE", category: "LIKELY_PIPE", orientation: "horizontal", length: 1300, confidence: 0.75 },
    { id: "LINE-0005", node_type: "LINE", category: "LIKELY_PIPE", orientation: "horizontal", length: 1180, confidence: 0.75 },
    { id: "LINE-0007", node_type: "LINE", category: "LIKELY_PIPE", orientation: "diagonal", length: 148, confidence: 0.75 },
    { id: "LINE-0009", node_type: "LINE", category: "LIKELY_PIPE", orientation: "diagonal", length: 1686, confidence: 0.75 },
  ],
  edges: SAMPLE_RELATIONSHIPS,
};

export const MOCK_GROK_QA = [
  {
    question: "What is the main process line or service described in this drawing?",
    answer: `Based on extracted metadata, the main process line is **3rd Stage HP Gas Export**. Key process indicators:
• **Compressor Unit**: OBJ-0002 (HP GAS EXPORT COMPRESSOR)
• **Inlet Header**: TXT-000-0002 (COMPRESSOR INLET HEADER)
• **Piping Specs**: 6"-PG-26-9001 (Line number) & SP 108.5 specification.`,
    sources: ["TXT-000-0001", "TXT-000-0002", "OBJ-0002"],
  },
  {
    question: "List all detected equipment and instrument tags with coordinates.",
    answer: `Extracted Equipment & Instruments:
1. **26-PIT-9087** (Instrument) — OBJ-0001 @ (3953, 3435) | Conf: 0.92
2. **26-KZ-902** (Package Unit) — OBJ-0003 @ (1400, 800) | Conf: 0.91
3. **V-100A** (Vessel / Tank) — OBJ-0004 @ (3050, 1500) | Conf: 0.91
4. **HP GAS EXPORT COMPRESSOR** — OBJ-0002 @ (4592, 3163) | Conf: 0.88`,
    sources: ["OBJ-0001", "OBJ-0002", "OBJ-0003", "OBJ-0004"],
  },
  {
    question: "Trace connections for compressor or inlet header equipment.",
    answer: `Connectivity Trace Result for **OBJ-0003 (26-KZ-902)**:
➜ Start: OBJ-0003 (Compressor Package)
➜ Connected via **LINE-0003** (1300px Horizontal Pipe)
➜ Connected via **LINE-0005** to **OBJ-0005 (3"-DO-56-9051 Valve)**
➜ Flow continues via **LINE-0007** to **OBJ-0004 (V-100A Vessel)**
➜ Output stream connects to **OBJ-0002 (HP Gas Export Compressor)**.`,
    sources: ["OBJ-0003", "LINE-0003", "LINE-0005", "OBJ-0005", "LINE-0007", "OBJ-0004", "OBJ-0002"],
  },
];
