"""Abstract base class for all object detectors in the platform."""
from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np

from src.models.schemas import DetectedObject


class Detector(ABC):
    """Abstract Detector interface for engineering symbol/entity detection."""

    @abstractmethod
    def detect(self, image: np.ndarray, tile_offset: tuple[float, float] = (0.0, 0.0)) -> list[DetectedObject]:
        """Detect objects in an image array.

        Parameters
        ----------
        image : np.ndarray
            RGB image array.
        tile_offset : tuple[float, float]
            (x_offset, y_offset) to map local coords to global image space.

        Returns
        -------
        list[DetectedObject]
            Detected symbols/entities in global coordinates.
        """
        raise NotImplementedError
