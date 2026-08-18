"""Central configuration manager for Vector-PID processing pipeline."""
import os
from pydantic import BaseModel, Field


class TilingConfig(BaseModel):
    """Tiling parameters for high-resolution drawing slicing."""
    tile_size: int = Field(default=1024, ge=256, le=4096)
    overlap: int = Field(default=100, ge=0, le=512)


class LineDetectionConfig(BaseModel):
    """Hough line transform detection thresholds."""
    rho: float = Field(default=1.0, gt=0)
    theta_degrees: float = Field(default=1.0, gt=0)
    threshold: int = Field(default=50, ge=10)
    min_line_length: float = Field(default=30.0, ge=5.0)
    max_line_gap: float = Field(default=10.0, ge=0.0)
    collinear_max_gap: float = Field(default=15.0, ge=0.0)
    collinear_max_angle_diff: float = Field(default=5.0, ge=0.0)


class SymbolDetectionConfig(BaseModel):
    """Contour and symbol detection parameters."""
    min_area: float = Field(default=100.0, ge=10.0)
    max_area: float = Field(default=50000.0, ge=100.0)
    aspect_ratio_tolerance: float = Field(default=0.3, ge=0.0, le=1.0)


class SpatialConfig(BaseModel):
    """Spatial relationship attachment distances."""
    proximity_threshold: float = Field(default=80.0, ge=10.0)
    max_connection_distance: float = Field(default=120.0, ge=10.0)


class LLMConfig(BaseModel):
    """Groq / LLM reasoning configuration."""
    api_key: str = Field(default_factory=lambda: os.getenv("GROK_API_KEY", ""))
    base_url: str = Field(default_factory=lambda: os.getenv("GROK_BASE_URL", "https://api.groq.com/openai/v1"))
    model: str = Field(default_factory=lambda: os.getenv("GROK_MODEL", "llama-3.3-70b-versatile"))
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4096, ge=256)


class PipelineConfig(BaseModel):
    """Master configuration container for end-to-end extraction."""
    tiling: TilingConfig = Field(default_factory=TilingConfig)
    lines: LineDetectionConfig = Field(default_factory=LineDetectionConfig)
    symbols: SymbolDetectionConfig = Field(default_factory=SymbolDetectionConfig)
    spatial: SpatialConfig = Field(default_factory=SpatialConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    output_dir: str = Field(default="data/outputs")


def load_config() -> PipelineConfig:
    """Load default or environment-configured pipeline settings."""
    return PipelineConfig()
