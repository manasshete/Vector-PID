# Vector-PID 

**AI-Powered P&ID Topology Extraction & Semantic Reasoning Platform**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyTest Status](https://img.shields.io/badge/tests-88%20passed-brightgreen.svg)]()
[![AI Reasoning](https://img.shields.io/badge/AI_Reasoning-Groq_LLM-orange.svg)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture: Modular](https://img.shields.io/badge/architecture-Python--First-orange.svg)]()

**Vector-PID** is an enterprise-grade, end-to-end computer vision and semantic AI framework designed to process, extract, and reason over ultra-high-resolution Piping and Instrumentation Diagrams (P&IDs) and engineering schematics.

It combines **deterministic computer vision** (bidirectional tiling, vector line detection, contour analysis, and regex text classification) with **graph topology construction** (NetworkX) and **LLM-powered AI reasoning & semantic Q&A** (Groq API) to turn static engineering drawings into queryable digital twin data structures.

---

## 📋 Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Pipeline Breakdown (Steps 1–12)](#-pipeline-breakdown-steps-112)
- [Repository Structure](#-repository-structure)
- [Installation & Setup](#-installation--setup)
- [Usage & Execution Guide](#-usage--execution-guide)
- [Web Platform (API + React UI)](#-web-platform-api--react-ui)
- [REST API Reference](#-rest-api-reference)
- [Data Schemas & JSON Output Artifacts](#-data-schemas--json-output-artifacts)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Honesty Disclosures & Model Limitations](#-honesty-disclosures--model-limitations)
- [Hosting & Docker Deployment](#-hosting--docker-deployment)
- [Production Roadmap](#-production-roadmap)

---

## 🎯 Executive Summary

Process engineering drawings (P&IDs) are massive, high-density vector PDFs (often 5000×3500+ pixels) containing thousands of interconnected components, instruments, line numbers, and annotations. 

Traditional single-pass OCR and generic vision models fail due to memory limits, text scaling, and loss of geometric context. **Vector-PID** solves this by enforcing a strict 14-stage pipeline:

1. **Zero-Drift Tiling**: Splits drawings into overlapping 1024×1024 tiles with 100% loss-free bidirectional coordinate mapping (`local ⇄ global`).
2. **Deterministic Extraction**: Extracts text via EasyOCR, lines via Hough Transform with collinear segment merging, and symbols via shape contour analysis.
3. **Structured Spatial Topology**: Connects text annotations to physical components and builds a NetworkX topology graph representing piping flow and connectivity.
4. **AI Connection Reasoning**: Feeds all structured CV data into Groq LLM, producing a structured JSON explaining which parts connect to which, why they connect (engineering reasoning), and what process flows exist.
5. **Grounded LLM Reasoning**: Feeds structured sub-contexts into Grok LLM to answer complex process engineering queries without hallucinating equipment tags or dimensions.
6. **Interactive Web Viewer**: React + Three.js canvas with topology graph explorer, JSON inspector, and live Grok Q&A — connected to the Python pipeline via FastAPI.

---

## 🏗️ System Architecture

```text
                                  +-----------------------+
                                  |   Raw P&ID PDF / Image|
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |  Load & Preprocessing |
                                  |  (Poppler + OpenCV)   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |    TileManager Grid   |
                                  |  (1024x1024 + 100px)  |
                                  +-----------+-----------+
                                              |
                     +------------------------+------------------------+
                     |                        |                        |
                     v                        v                        v
         +-----------+-----------+ +----------+----------+ +-----------+-----------+
         |      EasyOCR Engine   | |   LineDetector      | | OpenCVSymbolDetector |
         |   (Tile OCR Parallel) | | (Hough + Collinear) | |  (Contour Analysis)  |
         +-----------+-----------+ +----------+----------+ +-----------+-----------+
                     |                        |                        |
                     v                        |                        |
         +-----------+-----------+            |                        |
         |    TextClassifier     |            |                        |
         | (Regex & P&ID Rules)  |            |                        |
         +-----------+-----------+            |                        |
                     |                        |                        |
                     +------------------------+------------------------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |   RelationshipEngine  |
                                  | (Spatial Proximity)   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |   DrawingGraph Engine |
                                  | (NetworkX Topology)   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |  AI Reasoning (Groq)  |
                                  | (Connection Reasoning)|
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |     GrokService LLM   |
                                  | (Grounded QA & Trace) |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |   FastAPI REST Server |
                                  |  (Upload, Graph, Chat)|
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |  React + Three.js UI  |
                                  | (Canvas, Graph, JSON) |
                                  +-----------------------+
```

---

## 🔬 Pipeline Breakdown (Steps 1–14)

| Stage | Module | Responsibility | Key Output |
| :--- | :--- | :--- | :--- |
| **Step 1–2** | `src.preprocessing.image_processor` | PDF rendering via Poppler (300 DPI), binarization, Otsu thresholding, noise removal. | Clean high-res image array |
| **Step 3–4** | `src.preprocessing.tiling` | TileManager splits large image into 1024×1024 tiles with 100px overlap and exact coordinate translation. | 24 grid tiles (0 error drift) |
| **Step 5** | `src.ocr.ocr_engine` | Tile-by-tile text extraction using PyTorch EasyOCR with local-to-global bounding box transformation. | `data/outputs/ocr_results.json` |
| **Step 6** | `src.ocr.text_classifier` | Rule-based regex engine classifying text into `PIPE_TAG`, `EQUIPMENT_TAG`, `INSTRUMENT_TAG`, `LINE_NUMBER`, `SPEC_REFERENCE`, `PIPE_SIZE`, `SERVICE`, `DESCRIPTION`, `ANNOTATION`, `DRAWING_REFERENCE`, and `GRID_LABEL`. | `data/outputs/classified_text.json` |
| **Step 7** | `src.geometry.line_detector` | Hough line transform with collinear segment merging (5° angle, 15px gap), orientation (`horizontal`, `vertical`, `diagonal`), and type classification (`LIKELY_PIPE`, `BORDER`, `DIMENSION`). | `data/outputs/lines.json` |
| **Step 8** | `src.detection.symbol_detector` | OpenCV contour shape heuristics for symbol classification (`VALVE`, `PUMP`, `TANK`, `INSTRUMENT`, `FLANGE`, `EQUIPMENT`). | `data/outputs/objects.json` |
| **Step 9** | `src.spatial.relationship_engine` | Deduplicates tile-overlap text, computes Euclidean proximity between symbols and text (`annotated_by`), and associates line endpoints to symbols (`connected_to`). | `data/outputs/relationships.json` |
| **Step 10** | `src.graph.drawing_graph` | Constructs NetworkX `nx.Graph` linking objects, lines, and text. Enables BFS path tracing (`trace_from_object`). | `data/outputs/graph.json` |
| **Step 11** | `src.services.gemini_service` | **AI connection reasoning** — sends all structured CV data to Groq LLM (same API key as Grok). Produces structured JSON with connection reasoning, engineering explanations, and process flow paths. | `data/outputs/ai_reasoning.json` |
| **Step 12** | `src.services.grok_service` | OpenAI-compatible Grok API client with strict system prompt enforcement, relevant sub-context retrieval, and automated 429 rate-limit backoff retry. | Natural language QA responses |
| **Step 13** | `src.pipeline.drawing_pipeline` | Single entry point (`analyze_drawing()`) orchestrating all stages and exporting 8 structured JSON artifacts. | `data/outputs/final_analysis.json` |
| **Step 14** | `src.api.main` | FastAPI server exposing upload, analysis retrieval, graph export, AI reasoning, and Grok chat to the React client. | REST JSON over HTTP |

---

## 📁 Repository Structure

```text
engineering-drawing-intelligence/
├── Dockerfile                   # Production containerization setup
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
│
├── src/                         # Core Python modules
│   ├── detection/               # Object/Symbol detection (Detector & OpenCVSymbolDetector)
│   ├── geometry/                # Vector line detector & geometry utilities
│   ├── graph/                   # NetworkX graph representation (DrawingGraph)
│   ├── models/                  # Pydantic data models (BoundingBox, DetectedLine, AIReasoning, etc.)
│   ├── ocr/                     # EasyOCR engine & rule-based TextClassifier
│   ├── pipeline/                # End-to-end orchestration (analyze_drawing)
│   ├── preprocessing/           # Image processor, PDF renderer, TileManager
│   ├── services/                # GrokService LLM Q&A + AI Connection Reasoning
│   ├── spatial/                 # Spatial reasoning & relationship extraction
│   ├── api/                     # FastAPI REST server (Step 14)
│   └── utils/                   # Visualization helpers
│
├── client/                      # React + Vite + Three.js web UI
│   ├── src/
│   │   ├── components/          # Canvas, GraphExplorer, AiChatDrawer, DataInspector
│   │   ├── lib/                 # pidScene.js (Three.js), api.js, normalizeAnalysis.js
│   │   └── data/                # Sample fallback dataset
│   ├── package.json
│   └── vite.config.js           # Dev proxy: /api → localhost:8000
│
├── scripts/                     # Standalone CLI execution scripts
│   ├── 03_tiling.py             # Test tiling grid generation
│   ├── 04_ocr.py                # Run OCR engine
│   ├── 05_text_classification.py# Run text classifier
│   ├── 06_line_detection.py     # Run line segment detection
│   ├── 07_symbol_detection.py   # Run symbol contour detector
│   ├── 08_spatial_reasoning.py  # Extract spatial relationships
│   ├── 09_graph_construction.py # Build NetworkX topology graph
│   ├── 10_grok_analysis.py      # Run Grok LLM QA test suite
│   ├── 11_end_to_end_pipeline.py# Execute full end-to-end pipeline
│   └── run_api.py               # Start FastAPI server (port 8000)
│
├── tests/                       # Unit test suite (88 tests)
│   ├── test_drawing_graph.py
│   ├── test_gemini_reasoning.py # 🆕 AI reasoning model & service tests
│   ├── test_geometry_utils.py
│   ├── test_line_detector.py
│   ├── test_ocr.py
│   ├── test_pipeline.py
│   ├── test_spatial_analyzer.py
│   ├── test_symbol_detector.py
│   ├── test_text_classifier.py
│   └── test_tiling.py
│
└── data/                        # Project datasets & outputs
    ├── raw/                     # Input P&ID files (.pdf, .png)
    ├── processed/               # Preprocessed image cache
    ├── tiles/                   # Generated tile images
    └── outputs/                 # Final 8 JSON artifacts (incl. ai_reasoning.json)
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18+ *(for the React web client)*
- **Poppler Utilities** *(required for PDF rendering)*:
  - **Linux**: `sudo apt-get install poppler-utils`
  - **macOS**: `brew install poppler`
  - **Windows**: Download Poppler binaries and add `/bin` to system `PATH`.

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/manasshete/Vector-PID.git
cd Vector-PID

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install web client dependencies
cd client && npm install && cd ..

# 5. Configure environment variables
cp .env.example .env
```

Edit `.env` to add your API credentials:
```env
# Groq LLM (used for both chat Q&A and AI connection reasoning)
GROK_API_KEY=your_groq_api_key_here
GROK_BASE_URL=https://api.groq.com/openai/v1
GROK_MODEL=llama-3.3-70b-versatile
```

---

## 🚀 Usage & Execution Guide

### 1. Run the End-to-End Pipeline
Place your target PDF in `data/raw/` and execute:
```bash
python scripts/11_end_to_end_pipeline.py
```
This generates all 8 structured JSON artifacts in `data/outputs/`, including `ai_reasoning.json` with AI connection reasoning.

### 2. Run Individual Pipeline Stages

```bash
# Run Text Classification
python scripts/05_text_classification.py

# Run Line Detection
python scripts/06_line_detection.py

# Run Symbol Detection
python scripts/07_symbol_detection.py

# Run Spatial Relationship Extraction
python scripts/08_spatial_reasoning.py

# Run Topology Graph Construction
python scripts/09_graph_construction.py

# Run Grok LLM Reasoning QA
python scripts/10_grok_analysis.py
```

---

## 🌐 Web Platform (API + React UI)

The React client talks to the Python pipeline through a FastAPI server. Upload a P&ID, run the full CV pipeline in the background, then explore results in an interactive Three.js canvas.

### Quick Start (two terminals)

**Terminal 1 — API server** (from project root):
```bash
python scripts/run_api.py
```
Server runs at `http://localhost:8000`. On startup it auto-loads `data/outputs/final_analysis.json` if present.

**Terminal 2 — Web client**:
```bash
cd client
npm run dev
```
Open the URL Vite prints (usually `http://localhost:5173`). The Vite dev proxy forwards `/api/*` to port 8000.

### UI Features

| Tab | Description |
| :--- | :--- |
| **Canvas** | Three.js P&ID viewer — 3D pipe tubes, symbol meshes, zoom-based label decluttering, minimap, layer toggles |
| **Graph** | Topology explorer with BFS path tracer and searchable node directory |
| **Ask AI** | Grounded Grok Q&A against the loaded analysis (requires `GROK_API_KEY`) |
| **Data** | Raw JSON artifact inspector with copy/download |

### Upload Flow

1. Click **Upload** in the navbar and select a `.pdf` or image (`.png`, `.jpg`, `.tif`, `.bmp`).
2. The API returns a `job_id`; the client polls until the pipeline completes.
3. Results populate all tabs from `final_analysis.json` structure.
4. Without the API running, the UI falls back to bundled sample data.

> **Note:** Full pipeline analysis on large P&IDs can take several minutes (OCR + line/symbol detection). Keep the API terminal open while jobs run.

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Server status, whether analysis is loaded, Grok & Gemini keys configured |
| `GET` | `/api/v1/analysis` | Full `final_analysis.json` payload (includes `ai_reasoning`) |
| `GET` | `/api/v1/graph` | NetworkX graph export only |
| `GET` | `/api/v1/reasoning` | AI reasoning JSON — connection explanations & process flows from Groq LLM |
| `POST` | `/api/v1/analyze` | Upload drawing file → returns `{ job_id, status: "pending" }` |
| `GET` | `/api/v1/jobs/{job_id}` | Poll job status; `completed` includes `result` |
| `POST` | `/api/v1/chat` | Body: `{ "question": "..." }` → grounded Grok answer + cited source IDs |

**Example — upload and poll:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze -F "file=@data/raw/your-drawing.pdf"
# → {"job_id":"...","status":"pending"}

curl http://localhost:8000/api/v1/jobs/<job_id>
# → {"status":"completed","result":{...}}
```

**Example — get AI reasoning:**
```bash
curl http://localhost:8000/api/v1/reasoning
# → {"drawing_summary":"...","connections":[{"from_component":{...},"to_component":{...},"reason":"..."},...],"process_flows":[...]}
```

**Example — chat:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"List all equipment tags"}'
```

---

## 📊 Data Schemas & JSON Output Artifacts

Execution of `analyze_drawing()` exports 8 intermediate and final JSON files to `data/outputs/`:

1. **`ocr_results.json`**: Raw OCR detections with tile-mapped global bounding boxes.
2. **`classified_text.json`**: Categorized OCR text (`PIPE_TAG`, `EQUIPMENT_TAG`, `INSTRUMENT_TAG`, etc.).
3. **`lines.json`**: Vector line segments with start/end coordinates, length, orientation, and type.
4. **`objects.json`**: Enriched symbol detections with associated nearest text metadata.
5. **`relationships.json`**: Extracted topology pairs (`from_id`, `to_id`, `relationship`, `distance`, `confidence`).
6. **`graph.json`**: Full NetworkX graph export with node/edge attribute maps.
7. **`ai_reasoning.json`**: AI structured reasoning — connection explanations with engineering rationale and process flow paths.
8. **`final_analysis.json`**: Consolidated single JSON payload containing the complete drawing intelligence model (including `ai_reasoning`).

### Key Schema Snippet (`DetectedLine` & `SpatialRelationship`)

```python
class DetectedLine(BaseModel):
    id: str                             # e.g., "LINE-0042"
    start: tuple[float, float]          # Global (x, y)
    end: tuple[float, float]            # Global (x, y)
    length: float                       # Pixel length
    orientation: str                    # "horizontal", "vertical", "diagonal"
    line_type: str                      # "LIKELY_PIPE", "DIMENSION", "BORDER"
    confidence: float                   # Score 0.0 - 1.0
    source_method: str = "opencv_hough"

class SpatialRelationship(BaseModel):
    from_id: str                        # e.g., "OBJ-0001"
    to_id: str                          # e.g., "TXT-022-0012"
    relationship: str                   # "annotated_by", "connected_to", "near"
    distance: float                     # Distance in pixels
    confidence: float                   # Score 0.0 - 1.0
```

### 🆕 AI Reasoning Schema (`ai_reasoning.json`)

```json
{
  "drawing_summary": "P&ID showing a gas compression system with...",
  "connections": [
    {
      "from_component": { "id": "OBJ-001", "tag": "V-100", "type": "VALVE" },
      "to_component": { "id": "OBJ-005", "tag": "P-200", "type": "PUMP" },
      "connection_type": "pipe",
      "flow_direction": "P-200 → V-100",
      "reason": "Valve V-100 is on the discharge line of Pump P-200, regulating flow to the downstream heat exchanger.",
      "confidence": 0.92,
      "line_ids": ["LINE-042", "LINE-043"]
    }
  ],
  "process_flows": [
    {
      "flow_name": "Main Gas Compression Loop",
      "path": ["E-100 (Inlet Separator)", "K-200 (Compressor)", "E-300 (Cooler)", "V-400 (Discharge)"],
      "description": "Gas enters the inlet separator, passes through the compressor, is cooled, and exits via the discharge valve."
    }
  ],
  "ai_model": "gemini-2.5-flash",
  "timestamp": "2026-08-14T23:00:00Z"
}
```

---

## 🧪 Testing & Quality Assurance

The platform features an automated unit test suite covering geometry math, coordinate transforms, OCR data schemas, classifier rules, graph topology building, and pipeline orchestration.

Run the test suite with PyTest:
```bash
python -m pytest tests/ -v
```

### Test Suite Summary (`88 passed`)
- `tests/test_geometry_utils.py`: Line intersection, point-to-line distance, collinear line merging.
- `tests/test_line_detector.py`: Synthetic edge detection and line orientation checks.
- `tests/test_symbol_detector.py`: Contour heuristic tests and confidence boundary assertions.
- `tests/test_spatial_analyzer.py`: Deduplication of tile overlap text & proximity calculations.
- `tests/test_drawing_graph.py`: NetworkX graph construction & BFS path tracing (`trace_from_object`).
- `tests/test_pipeline.py`: End-to-end pipeline mocking and artifact generation.
- `tests/test_text_classifier.py`: 36 regex tests for P&ID text classification.
- `tests/test_ocr.py`: BoundingBox coordinate translation tests.
- `tests/test_tiling.py`: Grid calculation and loss-free coordinate mapping tests.
- `tests/test_gemini_reasoning.py`: 🆕 16 tests — AI reasoning Pydantic models, image helpers, Gemini service init, and pipeline graceful fallback.

---

## ⚠️ Honesty Disclosures & Model Limitations

- **Symbol Detector Accuracy**: `OpenCVSymbolDetector` uses traditional contour shape heuristics. On complex engineering drawings, contour analysis achieves **<40% mAP** due to overlapping line work. It serves as an architectural baseline and should be upgraded to a trained YOLOv8 / RT-DETR model for production.
- **Line Detector Limitations**: `LineDetector` uses Hough Line Transformation. While effective for straight lines (>90% recall), it cannot easily distinguish between electrical signal lines, instrument tubing, and major process piping without deep vector learning.
- **LLM Sub-Context Pacing**: Grok API queries in `scripts/10_grok_analysis.py` implement strict sub-context filtering and automated backoff retry logic to operate reliably within Groq API free-tier rate limits (30 RPM).
- **AI Connection Reasoning**: The Groq LLM reasoning layer provides engineering-level connection explanations based on structured CV data. Accuracy depends on the quality of upstream detections (OCR, symbol detection, spatial relationships). The reasoning layer gracefully skips if `GROK_API_KEY` is not configured.

---

## 🐳 Hosting & Docker Deployment

### Docker Containerization

Vector-PID includes a pre-configured `Dockerfile` that packages Python 3.11, OpenCV C++ libraries, PyTorch, and Poppler utilities.

#### Build & Run Container Locally:

```bash
# 1. Build Docker image
docker build -t vector-pid .

# 2. Run end-to-end pipeline in container
docker run --rm --env-file .env -v "${PWD}/data/outputs:/app/data/outputs" vector-pid
```

#### Cloud Deployment (Render / Railway / Fly.io / AWS)

1. Connect your GitHub repository (`manasshete/Vector-PID`) to your cloud PaaS.
2. Select **Docker** as the deployment runtime.
3. Add your environment variables (`GROK_API_KEY`, `GROK_BASE_URL`, `GROK_MODEL`).
4. Allocate at least **1.5 GB – 2 GB RAM** for EasyOCR/PyTorch memory management.

---

## 🛣️ Production Roadmap

- [ ] **YOLOv8 / RT-DETR Symbol Detector**: Replace OpenCV contour detector with a fine-tuned deep learning model trained on ISO 14617 / ANSI P&ID symbol datasets (>85% mAP).
- [x] **AI Connection Reasoning**: Structured connection analysis with engineering reasoning via Groq LLM — explains which parts connect, why, and traces process flows.
- [x] **FastAPI REST Server**: `POST /api/v1/analyze`, `GET /api/v1/graph`, `GET /api/v1/reasoning`, `POST /api/v1/chat`, job polling.
- [x] **React Three.js Canvas UI**: Interactive web viewer with layer toggles, topology graph, JSON inspector, and Grok chat.
- [ ] **Multi-Sheet PDF Linker**: Parse matchline text (`SEE DWG-XXXX`) to link cross-drawing process flows into a unified graph.
- [ ] **Production CORS & Auth**: Token-based API auth and configurable allowed origins for deployed frontends.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.

---

**Author**: [Manas Shete](https://github.com/manasshete)  
**Project**: Vector-PID Platform