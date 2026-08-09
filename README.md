# Vector-PID 📐🤖

**AI-Powered P&ID Topology Extraction & Semantic Reasoning Platform**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyTest Status](https://img.shields.io/badge/tests-72%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture: Modular](https://img.shields.io/badge/architecture-Python--First-orange.svg)]()

**Vector-PID** is an enterprise-grade, end-to-end computer vision and semantic AI framework designed to process, extract, and reason over ultra-high-resolution Piping and Instrumentation Diagrams (P&IDs) and engineering schematics.

It combines **deterministic computer vision** (bidirectional tiling, vector line detection, contour analysis, and regex text classification) with **graph topology construction** (NetworkX) and **LLM semantic reasoning** (Grok API) to turn static engineering drawings into queryable digital twin data structures.

---

## 📋 Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Pipeline Breakdown (Steps 1–12)](#-pipeline-breakdown-steps-112)
- [Repository Structure](#-repository-structure)
- [Installation & Setup](#-installation--setup)
- [Usage & Execution Guide](#-usage--execution-guide)
- [Data Schemas & JSON Output Artifacts](#-data-schemas--json-output-artifacts)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Honesty Disclosures & Model Limitations](#-honesty-disclosures--model-limitations)
- [Hosting & Docker Deployment](#-hosting--docker-deployment)
- [Production Roadmap](#-production-roadmap)

---

## 🎯 Executive Summary

Process engineering drawings (P&IDs) are massive, high-density vector PDFs (often 5000×3500+ pixels) containing thousands of interconnected components, instruments, line numbers, and annotations. 

Traditional single-pass OCR and generic vision models fail due to memory limits, text scaling, and loss of geometric context. **Vector-PID** solves this by enforcing a strict 12-stage pipeline:

1. **Zero-Drift Tiling**: Splits drawings into overlapping 1024×1024 tiles with 100% loss-free bidirectional coordinate mapping (`local ⇄ global`).
2. **Deterministic Extraction**: Extracts text via EasyOCR, lines via Hough Transform with collinear segment merging, and symbols via shape contour analysis.
3. **Structured Spatial Topology**: Connects text annotations to physical components and builds a NetworkX topology graph representing piping flow and connectivity.
4. **Grounded LLM Reasoning**: Feeds structured sub-contexts into Grok LLM to answer complex process engineering queries without hallucinating equipment tags or dimensions.

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
                                  |     GrokService LLM   |
                                  | (Grounded QA & Trace) |
                                  +-----------------------+
```

---

## 🔬 Pipeline Breakdown (Steps 1–12)

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
| **Step 11** | `src.services.grok_service` | OpenAI-compatible Grok API client with strict system prompt enforcement, relevant sub-context retrieval, and automated 429 rate-limit backoff retry. | Natural language QA responses |
| **Step 12** | `src.pipeline.drawing_pipeline` | Single entry point (`analyze_drawing()`) orchestrating all stages and exporting 7 structured JSON artifacts. | `data/outputs/final_analysis.json` |

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
│   ├── models/                  # Pydantic data models (BoundingBox, DetectedLine, etc.)
│   ├── ocr/                     # EasyOCR engine & rule-based TextClassifier
│   ├── pipeline/                # End-to-end orchestration (analyze_drawing)
│   ├── preprocessing/           # Image processor, PDF renderer, TileManager
│   ├── services/                # GrokService LLM reasoning integration
│   ├── spatial/                 # Spatial reasoning & relationship extraction
│   └── utils/                   # Visualization helpers
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
│   └── 11_end_to_end_pipeline.py# Execute full end-to-end pipeline
│
├── tests/                       # Unit test suite (72 tests)
│   ├── test_drawing_graph.py
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
    └── outputs/                 # Final 7 JSON artifacts
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python**: 3.10 or higher
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

# 4. Configure environment variables
cp .env.example .env
```

Edit `.env` to add your Groq/Grok API credentials:
```env
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
This generates all 7 structured JSON artifacts in `data/outputs/`.

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

## 📊 Data Schemas & JSON Output Artifacts

Execution of `analyze_drawing()` exports 7 intermediate and final JSON files to `data/outputs/`:

1. **`ocr_results.json`**: Raw OCR detections with tile-mapped global bounding boxes.
2. **`classified_text.json`**: Categorized OCR text (`PIPE_TAG`, `EQUIPMENT_TAG`, `INSTRUMENT_TAG`, etc.).
3. **`lines.json`**: Vector line segments with start/end coordinates, length, orientation, and type.
4. **`objects.json`**: Enriched symbol detections with associated nearest text metadata.
5. **`relationships.json`**: Extracted topology pairs (`from_id`, `to_id`, `relationship`, `distance`, `confidence`).
6. **`graph.json`**: Full NetworkX graph export with node/edge attribute maps.
7. **`final_analysis.json`**: Consolidated single JSON payload containing the complete drawing intelligence model.

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

---

## 🧪 Testing & Quality Assurance

The platform features an automated unit test suite covering geometry math, coordinate transforms, OCR data schemas, classifier rules, graph topology building, and pipeline orchestration.

Run the test suite with PyTest:
```bash
python -m pytest tests/ -v
```

### Test Suite Summary (`72 passed`)
- `tests/test_geometry_utils.py`: Line intersection, point-to-line distance, collinear line merging.
- `tests/test_line_detector.py`: Synthetic edge detection and line orientation checks.
- `tests/test_symbol_detector.py`: Contour heuristic tests and confidence boundary assertions.
- `tests/test_spatial_analyzer.py`: Deduplication of tile overlap text & proximity calculations.
- `tests/test_drawing_graph.py`: NetworkX graph construction & BFS path tracing (`trace_from_object`).
- `tests/test_pipeline.py`: End-to-end pipeline mocking and artifact generation.
- `tests/test_text_classifier.py`: 36 regex tests for P&ID text classification.
- `tests/test_ocr.py`: BoundingBox coordinate translation tests.
- `tests/test_tiling.py`: Grid calculation and loss-free coordinate mapping tests.

---

## ⚠️ Honesty Disclosures & Model Limitations

- **Symbol Detector Accuracy**: `OpenCVSymbolDetector` uses traditional contour shape heuristics. On complex engineering drawings, contour analysis achieves **<40% mAP** due to overlapping line work. It serves as an architectural baseline and should be upgraded to a trained YOLOv8 / RT-DETR model for production.
- **Line Detector Limitations**: `LineDetector` uses Hough Line Transformation. While effective for straight lines (>90% recall), it cannot easily distinguish between electrical signal lines, instrument tubing, and major process piping without deep vector learning.
- **LLM Sub-Context Pacing**: Grok API queries in `scripts/10_grok_analysis.py` implement strict sub-context filtering and automated backoff retry logic to operate reliably within Groq API free-tier rate limits (30 RPM).

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
- [ ] **FastAPI REST Server**: Expose `POST /api/v1/analyze`, `GET /api/v1/graph`, and `POST /api/v1/chat` endpoints.
- [ ] **React SVG Canvas UI**: Interactive web viewer with bounding box toggle overlays and click-to-trace line highlighting.
- [ ] **Multi-Sheet PDF Linker**: Parse matchline text (`SEE DWG-XXXX`) to link cross-drawing process flows into a unified graph.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.

---

**Author**: [Manas Shete](https://github.com/manasshete)  
**Project**: Vector-PID Platform