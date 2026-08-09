"""Image loading and configurable preprocessing for engineering drawings."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

from src.models.schemas import ImageMetadata


def load_engineering_drawing(
    path: str | Path,
    pdf_dpi: int = 300,
    pdf_page: int = 1,
) -> tuple[np.ndarray, ImageMetadata]:
    """Load a raster image or PDF page as an RGB numpy array with metadata.

    Parameters
    ----------
    path : str | Path
        Absolute or relative path to the drawing file.  Supported formats:
        ``.pdf``, ``.png``, ``.jpg``/``.jpeg``, ``.tiff``/``.tif``.
    pdf_dpi : int, optional
        Rasterisation resolution for PDF files, in dots-per-inch.  Must be
        between 72 and 1200 (inclusive).  Default is ``300``.
    pdf_page : int, optional
        1-indexed page number to extract from a multi-page PDF.  Default is
        ``1`` (first page).  Currently only a single page is loaded per call;
        this parameter is reserved for future multi-page batch support.

    Returns
    -------
    tuple[np.ndarray, ImageMetadata]
        ``(image, metadata)`` where *image* is an ``(H, W, 3)`` uint8 RGB
        array and *metadata* captures filename, dimensions, DPI, and source
        format.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist on the filesystem.
    ImportError
        If ``pdf2image`` is not installed when a PDF is requested.
    EnvironmentError
        If the Poppler binaries required by ``pdf2image`` are missing.
    ValueError
        If *pdf_dpi* is outside [72, 1200], the PDF has zero pages, the PDF
        is corrupt, or the file format is unsupported.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Drawing not found: {path}")

    suffix = path.suffix.lower()
    metadata_kwargs = {"filename": path.name, "source_format": suffix.lstrip('.')}

    if suffix == ".pdf":
        # --- DPI range guard ---
        if not (72 <= pdf_dpi <= 1200):
            raise ValueError(
                f"pdf_dpi must be between 72 and 1200 (got {pdf_dpi}). "
                "Values below 72 produce unreadable output; values above 1200 "
                "consume excessive memory."
            )

        # --- PDF rendering (pdf2image -> pypdfium2 -> pymupdf fallback) ---
        img = None
        # Try pdf2image first
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(
                str(path),
                dpi=pdf_dpi,
                first_page=pdf_page,
                last_page=pdf_page,
            )
            if images:
                pil_img = images[0].convert("RGB")
                img = np.array(pil_img)
        except Exception:
            pass

        # Try pypdfium2 fallback (pure python binary wheel, no system Poppler needed)
        if img is None:
            try:
                import pypdfium2 as pdfium
                pdf = pdfium.PdfDocument(str(path))
                if pdf_page < 1 or pdf_page > len(pdf):
                    raise ValueError(f"Requested page {pdf_page} out of bounds (1-{len(pdf)})")
                page = pdf[pdf_page - 1]
                scale = pdf_dpi / 72.0
                bitmap = page.render(scale=scale)
                pil_img = bitmap.to_pil().convert("RGB")
                img = np.array(pil_img)
            except Exception:
                pass

        # Try PyMuPDF (fitz) fallback
        if img is None:
            try:
                import fitz
                doc = fitz.open(str(path))
                if pdf_page < 1 or pdf_page > len(doc):
                    raise ValueError(f"Requested page {pdf_page} out of bounds (1-{len(doc)})")
                page = doc[pdf_page - 1]
                zoom = pdf_dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))
            except Exception:
                pass

        if img is None:
            raise EnvironmentError(
                "Failed to render PDF drawing. Please ensure 'pypdfium2' or 'pymupdf' is installed:\n"
                "    pip install pypdfium2 pymupdf"
            )

        metadata_kwargs["dpi"] = (pdf_dpi, pdf_dpi)
    elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".tif"}:
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Failed to read image: {path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        with Image.open(path) as pil_img:
            metadata_kwargs["dpi"] = pil_img.info.get("dpi")
    else:
        raise ValueError(f"Unsupported format: {suffix}")

    h, w, c = img.shape
    metadata = ImageMetadata(width=w, height=h, channels=c, **metadata_kwargs)
    return img, metadata


def preprocess_drawing(image: np.ndarray, config: dict | None = None) -> dict[str, np.ndarray]:
    """Configurable preprocessing pipeline. Returns all intermediate stages."""
    if image is None or image.size == 0:
        raise ValueError("Input image is empty or None")
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

    default_config = {
        "blur_kernel_size": 3,
        "threshold_method": "adaptive",
        "contrast_clip_limit": 2.0,
        "contrast_grid_size": (8, 8),
        "deskew_enabled": False,
        "denoise_strength": 10,
    }
    cfg = {**default_config, **(config or {})}

    valid_thresholds = {"adaptive", "otsu", "binary"}
    if cfg["threshold_method"] not in valid_thresholds:
        raise ValueError(f"Invalid threshold_method. Must be one of {valid_thresholds}")

    stages: dict[str, np.ndarray] = {"original": image.copy()}

    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    stages["grayscale"] = gray

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=cfg["denoise_strength"])
    stages["denoised"] = denoised

    # Contrast Enhancement (CLAHE)
    clahe = cv2.createCLAHE(
        clipLimit=cfg["contrast_clip_limit"],
        tileGridSize=tuple(cfg["contrast_grid_size"])
    )
    enhanced = clahe.apply(denoised)
    stages["contrast_enhanced"] = enhanced

    # Thresholding
    blur_k = max(3, cfg["blur_kernel_size"] | 1)  # Ensure odd
    blurred = cv2.GaussianBlur(enhanced, (blur_k, blur_k), 0)

    if cfg["threshold_method"] == "adaptive":
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    elif cfg["threshold_method"] == "otsu":
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:  # binary
        _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
    stages["thresholded"] = thresh

    # Deskew (optional)
    if cfg["deskew_enabled"]:
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        h, w = thresh.shape
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        stages["deskewed"] = cv2.warpAffine(thresh, M, (w, h), borderValue=255)
    else:
        stages["deskewed"] = thresh.copy()

    return stages