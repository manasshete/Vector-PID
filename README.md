# Vector-PID

**AI-Powered P&ID Topology Extraction & Semantic Reasoning Platform**

An end-to-end computer vision and semantic AI framework for processing, extracting, and reasoning over complex Piping and Instrumentation Diagrams (P&IDs) and engineering schematics.

---

## 🌟 Key Features

- 📐 **High-Resolution PDF Rendering & Preprocessing**: Handles ultra-high-resolution P&IDs (4963×3509+) with noise filtering and DPI scaling.
- 🧩 **Deterministic Tiling Engine**: Splits large engineering drawings into 1024×1024 tiles with 0-error bidirectional local-to-global coordinate mapping.
- 🔤 **EasyOCR Text Recognition**: High-precision text detection producing global bounding boxes.
- 🏷️ **Rule-Based & Semantic Text Classification**: Categorizes P&ID text into `PIPE_TAG`, `EQUIPMENT_TAG`, `INSTRUMENT_TAG`, `LINE_NUMBER`, `PIPE_SIZE`, `SERVICE`, `DESCRIPTION`, and `GRID_LABEL`.
- 📏 **Line Vector Detection**: Hough transform line detector with collinear segment merging, orientation classification, and line type scoring (`LIKELY_PIPE`, `BORDER`, `DIMENSION`).
- 🔘 **Symbol Contour Detection**: Contour geometry analysis for symbols (`VALVE`, `PUMP`, `TANK`, `INSTRUMENT`, `FLANGE`, `EQUIPMENT`).
- 🔗 **Spatial Relationship Engine**: Proximity analysis extracting `annotated_by`, `connected_to`, and `near` relationships between drawing entities.
- 🕸️ **NetworkX Topology Graph**: Graph representation supporting BFS connectivity tracing (`trace_from_object`).
- 🤖 **Grok LLM Integration**: Grounded Q&A and semantic reasoning using strict sub-context retrieval and rate limit backoff.

---

## 📁 Repository Structure

```text
engineering-drawing-intelligence/
├── src/
│   ├── detection/           # Symbol detector (Detector base & OpenCVSymbolDetector)
│   ├── geometry/            # Line detection & collinear line merging utilities
│   ├── graph/               # NetworkX topology graph (DrawingGraph)
│   ├── models/              # Pydantic data schemas (DetectedLine, SpatialRelationship, etc.)
│   ├── ocr/                 # EasyOCR wrapper & rule-based TextClassifier
│   ├── pipeline/            # End-to-end pipeline (analyze_drawing)
│   ├── preprocessing/       # PDF loading, image enhancement & TileManager
│   ├── services/            # GrokService (OpenAI-compatible LLM endpoint)
│   └── spatial/             # Spatial reasoning & relationship extraction
├── scripts/                 # CLI execution scripts (Steps 03–11)
├── tests/                   # 72 unit tests across 9 test modules
├── data/                    # Raw inputs, processed tiles, and output JSON artifacts
└── requirements.txt         # Project dependencies
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/manasshete/Vector-PID.git
cd Vector-PID

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy environment template and set your API keys:
```bash
cp .env.example .env
```
*(Add your `GROK_API_KEY` in `.env` if testing LLM reasoning features)*

### 3. Run End-to-End Pipeline

```bash
python scripts/11_end_to_end_pipeline.py
```

### 4. Run Test Suite

```bash
python -m pytest tests/ -v
```

---

## 🧪 Pipeline Artifacts

Running the pipeline exports 7 structured JSON artifacts to `data/outputs/`:
1. `ocr_results.json`
2. `classified_text.json`
3. `lines.json`
4. `objects.json`
5. `relationships.json`
6. `graph.json`
7. `final_analysis.json`