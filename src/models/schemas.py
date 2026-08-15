"""Pydantic data models for the entire pipeline."""
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box in original image coordinates."""
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)

    @property
    def xyxy(self) -> list[float]:
        return [self.x, self.y, self.x + self.width, self.y + self.height]

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


class ImageMetadata(BaseModel):
    """Immutable metadata captured at load time."""
    filename: str
    width: int
    height: int
    channels: int
    dpi: tuple[float, float] | None = None
    source_format: str


class DetectedObject(BaseModel):
    """Base model for all detected entities."""
    id: str
    type: str
    bbox: BoundingBox
    confidence: float = Field(..., ge=0, le=1)
    properties: dict = Field(default_factory=dict)
    source_method: str = ""


class ExtractedText(BaseModel):
    """OCR result with classification."""
    id: str
    text: str
    classification: str = "UNKNOWN"
    bbox: BoundingBox
    confidence: float = Field(..., ge=0, le=1)
    method: str = "rule"  # "rule" or "grok"


class Connection(BaseModel):
    """Relationship between two detected entities."""
    from_id: str
    to_id: str
    relationship: str
    confidence: float = Field(..., ge=0, le=1)


class DetectedLine(BaseModel):
    """Detected line segment in global image coordinates."""
    id: str
    start: tuple[float, float]
    end: tuple[float, float]
    length: float
    orientation: str  # "horizontal", "vertical", "diagonal"
    line_type: str  # "LIKELY_PIPE", "DIMENSION", "BORDER", "UNKNOWN"
    confidence: float = Field(..., ge=0, le=1)
    source_method: str = "opencv_hough"


class SpatialRelationship(BaseModel):
    """Spatial or logical relationship between two entities."""
    from_id: str
    to_id: str
    relationship: str  # "near", "connected_to", "annotated_by", "flows_to"
    distance: float
    confidence: float = Field(..., ge=0, le=1)


# --- AI Reasoning Models (Gemini Vision Output) ---

class AIConnectionComponent(BaseModel):
    """A component involved in an AI-reasoned connection."""
    id: str = ""
    tag: str = ""
    type: str = ""


class AIConnection(BaseModel):
    """A single AI-reasoned connection between two drawing components."""
    from_component: AIConnectionComponent
    to_component: AIConnectionComponent
    connection_type: str = ""          # "pipe", "signal", "instrument", etc.
    flow_direction: str = ""           # e.g., "P-200 → V-100"
    reason: str = ""                   # Engineering reasoning
    confidence: float = Field(default=0.5, ge=0, le=1)
    line_ids: list[str] = Field(default_factory=list)


class ProcessFlow(BaseModel):
    """An AI-identified process flow path through the drawing."""
    flow_name: str = ""
    path: list[str] = Field(default_factory=list)
    description: str = ""


class AIReasoning(BaseModel):
    """Complete AI reasoning output for a P&ID drawing."""
    drawing_summary: str = ""
    connections: list[AIConnection] = Field(default_factory=list)
    process_flows: list[ProcessFlow] = Field(default_factory=list)
    ai_model: str = "llama-3.3-70b-versatile"
    timestamp: str = ""