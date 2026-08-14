"""Gemini Vision AI reasoning service for P&ID connection analysis.

Uses Google Gemini 2.5 Flash to analyze engineering drawings with both
vision (the actual image) and structured CV data, producing a rich JSON
explaining which components connect, how they connect, and why.
"""
from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from dotenv import load_dotenv

from src.models.schemas import AIConnection, AIConnectionComponent, AIReasoning, ProcessFlow

load_dotenv()

# System prompt that forces structured JSON output with engineering reasoning
REASONING_SYSTEM_PROMPT = """You are an expert P&ID (Piping and Instrumentation Diagram) analyst.

You will receive:
1. An image of a P&ID engineering drawing
2. Structured data extracted by computer vision (detected text, symbols, lines, and spatial relationships)

Your task is to analyze the drawing and produce a STRUCTURED JSON explaining:
- What components exist and how they connect
- WHY each connection exists (engineering reasoning)
- The overall process flow paths

Rules:
- Use the CV-extracted data (object IDs, text tags, line IDs) as your primary reference
- When you see a component, reference its ID (e.g., "OBJ-001") and tag (e.g., "V-100")
- Explain connections in engineering terms (e.g., "discharge line", "instrument signal", "drain line")
- Identify flow direction when visible from the drawing
- If uncertain about a connection, say so and lower the confidence score
- NEVER invent component IDs or tags not present in the CV data

Output ONLY valid JSON matching this exact schema:
{
  "drawing_summary": "Brief description of what this P&ID shows",
  "connections": [
    {
      "from_component": { "id": "OBJ-xxx", "tag": "detected tag text", "type": "VALVE|PUMP|TANK|..." },
      "to_component": { "id": "OBJ-yyy", "tag": "detected tag text", "type": "VALVE|PUMP|TANK|..." },
      "connection_type": "pipe|signal|instrument|electrical|tubing",
      "flow_direction": "from → to",
      "reason": "Detailed engineering explanation of WHY these are connected and what purpose the connection serves",
      "confidence": 0.0-1.0,
      "line_ids": ["LINE-xxx", "LINE-yyy"]
    }
  ],
  "process_flows": [
    {
      "flow_name": "Name of the process flow",
      "path": ["Component A (Tag)", "Component B (Tag)", "..."],
      "description": "What this flow does in the process"
    }
  ]
}"""


def _resize_for_gemini(image: np.ndarray, max_dim: int = 2048) -> np.ndarray:
    """Resize image so the longest dimension is at most max_dim pixels.

    Gemini accepts large images but processing is faster and more reliable
    with a reasonable size. 2048px preserves enough detail for P&ID analysis.
    """
    h, w = image.shape[:2]
    if max(h, w) <= max_dim:
        return image
    scale = max_dim / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _image_to_base64(image: np.ndarray) -> str:
    """Encode a numpy image array to base64 JPEG string."""
    success, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not success:
        raise RuntimeError("Failed to encode image to JPEG")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def _build_context_text(
    texts: list[dict],
    objects: list[dict],
    lines: list[dict],
    relationships: list[dict],
) -> str:
    """Build a concise text summary of CV pipeline data for the prompt."""
    parts = []

    # Summarize detected texts (limit to most important)
    if texts:
        text_summary = []
        for t in texts[:40]:
            cls = t.get("classification", "UNKNOWN")
            text_summary.append(f"  - {t.get('id')}: \"{t.get('text')}\" [{cls}]")
        parts.append("DETECTED TEXT:\n" + "\n".join(text_summary))

    # Summarize detected symbols/objects
    if objects:
        obj_summary = []
        for o in objects[:30]:
            assoc = o.get("associated_text", {})
            tag = assoc.get("text", "no-tag") if assoc else "no-tag"
            bbox = o.get("bbox", {})
            center = f"({bbox.get('x', 0) + bbox.get('width', 0) / 2:.0f}, {bbox.get('y', 0) + bbox.get('height', 0) / 2:.0f})"
            obj_summary.append(f"  - {o.get('id')}: {o.get('type')} tag=\"{tag}\" at {center}")
        parts.append("DETECTED SYMBOLS:\n" + "\n".join(obj_summary))

    # Summarize lines
    if lines:
        pipe_lines = [l for l in lines if l.get("line_type") == "LIKELY_PIPE"]
        parts.append(f"DETECTED LINES: {len(lines)} total, {len(pipe_lines)} likely pipes")
        line_summary = []
        for l in pipe_lines[:20]:
            line_summary.append(
                f"  - {l.get('id')}: {l.get('orientation')} "
                f"({l.get('start', [0, 0])} → {l.get('end', [0, 0])}) "
                f"len={l.get('length', 0):.0f}px"
            )
        if line_summary:
            parts.append("KEY PIPE LINES:\n" + "\n".join(line_summary))

    # Summarize existing spatial relationships
    if relationships:
        conn_rels = [r for r in relationships if r.get("relationship") == "connected_to"]
        anno_rels = [r for r in relationships if r.get("relationship") == "annotated_by"]
        parts.append(
            f"SPATIAL RELATIONSHIPS: {len(relationships)} total "
            f"({len(conn_rels)} connections, {len(anno_rels)} annotations)"
        )
        rel_summary = []
        for r in conn_rels[:15]:
            rel_summary.append(f"  - {r.get('from_id')} → {r.get('to_id')} (dist={r.get('distance', 0):.1f}px)")
        if rel_summary:
            parts.append("KEY CONNECTIONS:\n" + "\n".join(rel_summary))

    return "\n\n".join(parts)


class GeminiReasoningService:
    """Gemini Vision AI reasoning layer for P&ID analysis.

    Sends the drawing image + structured CV data to Gemini 2.5 Flash
    and gets back structured JSON with engineering reasoning about
    component connections and process flows.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise EnvironmentError(
                "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/apikey "
                "and add it to your .env file."
            )

        from google import genai
        self._client = genai.Client(api_key=self.api_key)
        self._model = "gemini-2.5-flash"

    def reason_about_connections(
        self,
        image: np.ndarray,
        texts: list[dict],
        objects: list[dict],
        lines: list[dict],
        relationships: list[dict],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Analyze a P&ID image with CV context and return structured reasoning JSON.

        Parameters
        ----------
        image : np.ndarray
            The preprocessed P&ID drawing image (BGR or grayscale).
        texts : list[dict]
            Classified text detections from the CV pipeline.
        objects : list[dict]
            Detected symbols/objects with associated text.
        lines : list[dict]
            Detected line segments.
        relationships : list[dict]
            Spatial relationships from the relationship engine.
        max_retries : int
            Number of retries on rate-limit (429) or transient errors.

        Returns
        -------
        dict
            Structured AI reasoning JSON with connections, flows, and explanations.
        """
        from google import genai
        from google.genai import types

        # Prepare image for Gemini
        resized = _resize_for_gemini(image)
        img_b64 = _image_to_base64(resized)

        # Build context from CV data
        context_text = _build_context_text(texts, objects, lines, relationships)

        user_prompt = (
            "Analyze this P&ID engineering drawing. Here is the structured data "
            "extracted by computer vision from this same drawing:\n\n"
            f"{context_text}\n\n"
            "Using BOTH the image and the CV data above, identify all component "
            "connections, explain WHY each connection exists (engineering reasoning), "
            "and trace the major process flow paths. Output valid JSON only."
        )

        # Build the multimodal request
        image_part = types.Part.from_bytes(
            data=base64.b64decode(img_b64),
            mime_type="image/jpeg",
        )
        text_part = types.Part.from_text(text=user_prompt)

        # Retry loop for rate limits
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[image_part, text_part],
                        ),
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=REASONING_SYSTEM_PROMPT,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )

                # Parse the JSON response
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0]

                result = json.loads(raw_text)

                # Add metadata
                result["ai_model"] = self._model
                result["timestamp"] = datetime.now(timezone.utc).isoformat()

                # Validate through Pydantic
                validated = AIReasoning(
                    drawing_summary=result.get("drawing_summary", ""),
                    connections=[
                        AIConnection(
                            from_component=AIConnectionComponent(**c.get("from_component", {})),
                            to_component=AIConnectionComponent(**c.get("to_component", {})),
                            connection_type=c.get("connection_type", ""),
                            flow_direction=c.get("flow_direction", ""),
                            reason=c.get("reason", ""),
                            confidence=min(max(float(c.get("confidence", 0.5)), 0.0), 1.0),
                            line_ids=c.get("line_ids", []),
                        )
                        for c in result.get("connections", [])
                    ],
                    process_flows=[
                        ProcessFlow(
                            flow_name=f.get("flow_name", ""),
                            path=f.get("path", []),
                            description=f.get("description", ""),
                        )
                        for f in result.get("process_flows", [])
                    ],
                    ai_model=self._model,
                    timestamp=result["timestamp"],
                )

                return validated.model_dump(mode="json")

            except json.JSONDecodeError as exc:
                last_error = exc
                print(f"[Gemini] JSON parse error on attempt {attempt + 1}: {exc}")
            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()
                if "429" in error_str or "rate" in error_str or "quota" in error_str:
                    wait_time = 10 * (attempt + 1)
                    print(f"[Gemini] Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"[Gemini] Error on attempt {attempt + 1}: {exc}")
                    if attempt == max_retries - 1:
                        break
                    time.sleep(2)

        # Return a fallback structure if all retries failed
        print(f"[Gemini] All {max_retries} attempts failed. Last error: {last_error}")
        return AIReasoning(
            drawing_summary=f"AI reasoning failed after {max_retries} attempts: {last_error}",
            ai_model=self._model,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump(mode="json")
