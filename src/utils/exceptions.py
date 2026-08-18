"""Custom exception hierarchy for the Vector-PID platform."""


class VectorPIDError(Exception):
    """Base exception for all Vector-PID domain errors."""
    def __init__(self, message: str, stage: str = "general", details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "stage": self.stage,
            "details": self.details,
        }


class PipelineError(VectorPIDError):
    """Raised when an end-to-end pipeline execution stage fails."""
    def __init__(self, message: str, stage: str = "pipeline", details: dict | None = None):
        super().__init__(message, stage=stage, details=details)


class TilingError(VectorPIDError):
    """Raised when tile grid computation or coordinate translation fails."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, stage="tiling", details=details)


class OCRExtractionError(VectorPIDError):
    """Raised when OCR detection fails on drawing image tiles."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, stage="ocr", details=details)


class SymbolDetectionError(VectorPIDError):
    """Raised when CV symbol detection or contour analysis fails."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, stage="symbol_detection", details=details)


class TopologyError(VectorPIDError):
    """Raised when spatial graph construction or path tracing fails."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, stage="topology", details=details)


class AIRuntimeError(VectorPIDError):
    """Raised when AI connection reasoning or LLM inference fails."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, stage="ai_reasoning", details=details)
