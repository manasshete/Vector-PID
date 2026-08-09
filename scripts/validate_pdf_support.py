#!/usr/bin/env python3
"""Validate PDF ingestion pipeline across edge cases.

Run from the project root::

    python scripts/validate_pdf_support.py

Optional – test against a real PDF::

    python scripts/validate_pdf_support.py --pdf path/to/drawing.pdf

Exit codes
----------
0  All checks passed.
1  One or more checks failed.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so ``src`` imports resolve correctly
# when the script is run from any working directory.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.image_processor import load_engineering_drawing  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"
INFO = "\033[94m[INFO]\033[0m"


def _result(label: str, ok: bool, detail: str = "") -> bool:
    marker = PASS if ok else FAIL
    print(f"  {marker} {label}" + (f": {detail}" if detail else ""))
    return ok


# ---------------------------------------------------------------------------
# Individual test cases
# ---------------------------------------------------------------------------

def check_pdf2image_importable() -> bool:
    """Confirm pdf2image can be imported."""
    try:
        import pdf2image  # noqa: F401
        return _result("pdf2image importable", True)
    except ImportError as exc:
        _result("pdf2image importable", False, str(exc))
        print(f"    Fix: pip install pdf2image")
        return False


def check_poppler_available() -> bool:
    """Confirm Poppler binaries (pdftoppm / pdfinfo) are on PATH."""
    import shutil
    missing = [b for b in ("pdftoppm", "pdfinfo") if shutil.which(b) is None]
    if not missing:
        pdftoppm = shutil.which("pdftoppm")
        return _result("Poppler binaries on PATH", True, f"pdftoppm -> {pdftoppm}")
    _result("Poppler binaries on PATH", False, f"not found: {missing}")
    print(
        "    Fix:\n"
        "      Ubuntu/Debian : sudo apt-get install poppler-utils\n"
        "      macOS         : brew install poppler\n"
        "      Windows       : https://github.com/oschwartz10612/poppler-windows/releases"
    )
    return False


def check_missing_file_raises() -> bool:
    """FileNotFoundError must be raised for a path that does not exist."""
    fake = Path("/nonexistent/drawing.pdf")
    try:
        load_engineering_drawing(fake)
        return _result("Missing file -> FileNotFoundError", False, "no exception raised")
    except FileNotFoundError:
        return _result("Missing file -> FileNotFoundError", True)
    except Exception as exc:
        return _result("Missing file -> FileNotFoundError", False, f"unexpected {type(exc).__name__}: {exc}")


def check_dpi_too_low_raises() -> bool:
    """ValueError must be raised when pdf_dpi < 72."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tmp = Path(tf.name)
    try:
        load_engineering_drawing(tmp, pdf_dpi=10)
        return _result("pdf_dpi=10 -> ValueError", False, "no exception raised")
    except ValueError as exc:
        return _result("pdf_dpi=10 -> ValueError", True, str(exc)[:80])
    except Exception as exc:
        return _result("pdf_dpi=10 -> ValueError", False, f"unexpected {type(exc).__name__}: {exc}")
    finally:
        tmp.unlink(missing_ok=True)


def check_dpi_too_high_raises() -> bool:
    """ValueError must be raised when pdf_dpi > 1200."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tmp = Path(tf.name)
    try:
        load_engineering_drawing(tmp, pdf_dpi=1500)
        return _result("pdf_dpi=1500 -> ValueError", False, "no exception raised")
    except ValueError as exc:
        return _result("pdf_dpi=1500 -> ValueError", True, str(exc)[:80])
    except Exception as exc:
        return _result("pdf_dpi=1500 -> ValueError", False, f"unexpected {type(exc).__name__}: {exc}")
    finally:
        tmp.unlink(missing_ok=True)


def check_dpi_boundary_values_accepted() -> bool:
    """DPI values 72 and 1200 are on-boundary and must not raise ValueError for DPI itself.

    The actual conversion may fail due to empty/corrupt content, which is acceptable
    here -- we only verify the DPI guard does NOT fire.
    """
    results = []
    for dpi in (72, 1200):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tmp = Path(tf.name)
        try:
            load_engineering_drawing(tmp, pdf_dpi=dpi)
            results.append(_result(f"pdf_dpi={dpi} boundary accepted", True))
        except ValueError as exc:
            msg = str(exc)
            # A DPI guard error contains "72 and 1200" in its message.
            if "72 and 1200" in msg:
                results.append(_result(f"pdf_dpi={dpi} boundary accepted", False, msg[:80]))
            else:
                # Some other ValueError (e.g. empty PDF) -- DPI guard passed.
                results.append(_result(f"pdf_dpi={dpi} boundary accepted", True, f"non-DPI error: {msg[:60]}"))
        except Exception:
            # ImportError / EnvironmentError from missing dependencies -- DPI guard passed.
            results.append(_result(f"pdf_dpi={dpi} boundary accepted", True, "dependency error (DPI guard passed)"))
        finally:
            tmp.unlink(missing_ok=True)
    return all(results)


def check_corrupt_pdf_raises(poppler_available: bool) -> bool:
    """A file with .pdf extension but invalid content must raise an error (not crash silently)."""
    if not poppler_available:
        print(f"  {SKIP} Corrupt PDF check skipped (Poppler not available)")
        return True  # skip, not a failure

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as tf:
        tf.write(b"THIS IS NOT A VALID PDF CONTENT")
        tmp = Path(tf.name)
    try:
        load_engineering_drawing(tmp)
        return _result("Corrupt PDF -> exception", False, "no exception raised -- silent failure")
    except (ValueError, EnvironmentError, Exception):
        return _result("Corrupt PDF -> exception", True, f"{type(sys.exc_info()[1]).__name__} raised")
    finally:
        tmp.unlink(missing_ok=True)


def check_real_pdf_roundtrip(pdf_path: Path, poppler_available: bool) -> bool:
    """Load a real PDF and confirm output shape and metadata are plausible."""
    if not poppler_available:
        print(f"  {SKIP} Real-PDF round-trip skipped (Poppler not available)")
        return True
    if pdf_path is None:
        print(f"  {SKIP} Real-PDF round-trip skipped (no --pdf argument supplied)")
        return True

    if not pdf_path.exists():
        return _result(f"Real PDF round-trip ({pdf_path.name})", False, "file not found")

    try:
        import numpy as np
        img, meta = load_engineering_drawing(pdf_path, pdf_dpi=150)

        checks = [
            ("returns ndarray", isinstance(img, np.ndarray)),
            ("3-channel RGB", img.ndim == 3 and img.shape[2] == 3),
            ("non-empty image", img.size > 0),
            ("metadata filename matches", meta.filename == pdf_path.name),
            ("metadata source_format == pdf", meta.source_format == "pdf"),
            ("metadata dpi set", meta.dpi == (150, 150)),
        ]

        all_ok = True
        for label, ok in checks:
            all_ok = _result(f"  Real-PDF -- {label}", ok) and all_ok

        if all_ok:
            h, w = img.shape[:2]
            print(f"    {INFO} Image shape: {w}x{h} px  |  dtype: {img.dtype}")

        return all_ok

    except Exception:
        _result(f"Real-PDF round-trip ({pdf_path.name})", False, traceback.format_exc(limit=3))
        return False


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--pdf",
        metavar="PATH",
        type=Path,
        default=None,
        help="Optional path to a real PDF drawing for round-trip validation.",
    )
    args = parser.parse_args(argv)

    print("\n=============================================")
    print("  Engineering Drawing -- PDF Support Validator")
    print("=============================================\n")

    results: list[bool] = []

    print("-- Environment ------------------------------")
    pdf2image_ok = check_pdf2image_importable()
    results.append(pdf2image_ok)
    poppler_ok = check_poppler_available()
    results.append(poppler_ok)

    print("\n-- Error-handling guards --------------------")
    results.append(check_missing_file_raises())
    results.append(check_dpi_too_low_raises())
    results.append(check_dpi_too_high_raises())
    results.append(check_dpi_boundary_values_accepted())
    results.append(check_corrupt_pdf_raises(poppler_available=poppler_ok))

    print("\n-- Round-trip validation --------------------")
    results.append(check_real_pdf_roundtrip(args.pdf, poppler_available=poppler_ok))

    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n=== Results: {passed}/{total} checks passed ", end="")
    if passed == total:
        print("PASS ===\n")
        return 0
    else:
        failed = total - passed
        print(f"-- {failed} FAILED ===\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
