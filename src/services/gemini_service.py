"""AI reasoning service for P&ID connection analysis.

Uses the same Groq/Grok LLM provider (OpenAI-compatible API) to analyze
structured CV pipeline data and produce a rich JSON explaining which
components connect, how they connect, and why.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import numpy as np
from dotenv import load_dotenv

from src.models.schemas import AIConnection, AIConnectionComponent, AIReasoning, ProcessFlow

load_dotenv()

# System prompt that forces structured JSON output with engineering reasoning
REASONING_SYSTEM_PROMPT = """You are an expert P&ID (Piping and Instrumentation Diagram) analyst.

You will receive structured data extracted by computer vision from a P&ID drawing, including:
- Detected text labels (equipment tags, instrument tags, pipe tags, line numbers)
- Detected symbols/objects (valves, pumps, tanks, instruments) with positions
- Detected line segments (pipes, signal lines) with coordinates
- Spatial relationships (which objects are connected, annotated, or near each other)

Your task is to analyze this data and produce a STRUCTURED JSON explaining:
- What components exist and how they connect
- WHY each connection exists (engineering reasoning)
- The overall process flow paths

Rules:
- Use the CV-extracted data (object IDs, text tags, line IDs) as your primary reference
- When you see a component, reference its ID (e.g., "OBJ-001") and tag (e.g., "V-100")
- Explain connections in engineering terms (e.g., "discharge line", "instrument signal", "drain line")
- Identify flow direction when possible from the data
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


def _build_context_text(
    texts: list[dict],
    objects: list[dict],
    lines: list[dict],
    relationships: list[dict],
) -> str:
    """Build a rich text summary of CV pipeline data for the prompt."""
    parts = []

    # Summarize detected texts (limit to most important, prioritizing non-unknown)
    if texts:
        # Sort so tags and spec references come first
        sorted_texts = sorted(
            texts,
            key=lambda x: 0 if x.get("classification") in ("EQUIPMENT_TAG", "INSTRUMENT_TAG", "PIPE_TAG", "LINE_NUMBER") else 1
        )
        text_summary = []
        for t in sorted_texts[:300]:
            cls = t.get("classification", "UNKNOWN")
            text_summary.append(f"  - {t.get('id')}: \"{t.get('text')}\" [{cls}]")
        parts.append("DETECTED TEXT:\n" + "\n".join(text_summary))

    # Summarize detected symbols/objects (up to 200)
    if objects:
        obj_summary = []
        for o in objects[:200]:
            assoc = o.get("associated_text", {})
            tag = assoc.get("text", "no-tag") if assoc else "no-tag"
            bbox = o.get("bbox", {})
            center = f"({bbox.get('x', 0) + bbox.get('width', 0) / 2:.0f}, {bbox.get('y', 0) + bbox.get('height', 0) / 2:.0f})"
            obj_summary.append(f"  - {o.get('id')}: {o.get('type')} tag=\"{tag}\" at {center}")
        parts.append("DETECTED SYMBOLS:\n" + "\n".join(obj_summary))

    # Summarize lines (up to 150 likely pipes)
    if lines:
        pipe_lines = [l for l in lines if l.get("line_type") == "LIKELY_PIPE"]
        parts.append(f"DETECTED LINES: {len(lines)} total, {len(pipe_lines)} likely pipes")
        line_summary = []
        for l in pipe_lines[:150]:
            line_summary.append(
                f"  - {l.get('id')}: {l.get('orientation')} "
                f"({l.get('start', [0, 0])} → {l.get('end', [0, 0])}) "
                f"len={l.get('length', 0):.0f}px"
            )
        if line_summary:
            parts.append("KEY PIPE LINES:\n" + "\n".join(line_summary))

    # Summarize existing spatial relationships (up to 200 connections)
    if relationships:
        conn_rels = [r for r in relationships if r.get("relationship") == "connected_to"]
        anno_rels = [r for r in relationships if r.get("relationship") == "annotated_by"]
        parts.append(
            f"SPATIAL RELATIONSHIPS: {len(relationships)} total "
            f"({len(conn_rels)} connections, {len(anno_rels)} annotations)"
        )
        rel_summary = []
        for r in conn_rels[:200]:
            rel_summary.append(f"  - {r.get('from_id')} → {r.get('to_id')} (dist={r.get('distance', 0):.1f}px)")
        if rel_summary:
            parts.append("KEY CONNECTIONS:\n" + "\n".join(rel_summary))

    return "\n\n".join(parts)


class GeminiReasoningService:
    """AI reasoning layer for P&ID analysis using Groq/Grok LLM.

    Uses the same OpenAI-compatible API as GrokService (same API key,
    base URL, and model) to analyze structured CV pipeline data and
    produce engineering reasoning about component connections and
    process flows.
    """

    def __init__(self):
        self.api_key = os.getenv("GROK_API_KEY")
        self.base_url = os.getenv("GROK_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROK_MODEL", "llama-3.3-70b-versatile")

        if not self.api_key:
            raise EnvironmentError(
                "GROK_API_KEY not found in environment. Set it in .env"
            )

        if not self.base_url.endswith("/"):
            self.base_url += "/"

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=90.0,
        )

    def _chat(self, messages: list[dict[str, str]], temperature: float = 0.1) -> dict[str, Any]:
        """Synchronous chat completion call with retry on 429 rate limits."""
        max_retries = 5
        backoff = 4.0

        for attempt in range(max_retries):
            try:
                response = self._client.post(
                    "chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                    },
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = backoff * (attempt + 1)
                    print(f"[AI Reasoning] Rate limited, waiting {wait_time:.0f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise

    def reason_about_connections(
        self,
        image: np.ndarray,
        texts: list[dict],
        objects: list[dict],
        lines: list[dict],
        relationships: list[dict],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Analyze structured P&ID CV data and return reasoning JSON.

        Parameters
        ----------
        image : np.ndarray
            The preprocessed P&ID drawing image (kept for interface compatibility).
        texts : list[dict]
            Classified text detections from the CV pipeline.
        objects : list[dict]
            Detected symbols/objects with associated text.
        lines : list[dict]
            Detected line segments.
        relationships : list[dict]
            Spatial relationships from the relationship engine.
        max_retries : int
            Number of retries on transient errors.

        Returns
        -------
        dict
            Structured AI reasoning JSON with connections, flows, and explanations.
        """
        # Build context from CV data
        context_text = _build_context_text(texts, objects, lines, relationships)

        user_prompt = (
            "Analyze the following structured data extracted by computer vision "
            "from a P&ID engineering drawing.\n\n"
            f"{context_text}\n\n"
            "Using this CV data, identify all component connections, explain WHY "
            "each connection exists (engineering reasoning), and trace the major "
            "process flow paths. Output valid JSON only."
        )

        messages = [
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Retry loop
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._chat(messages, temperature=0.1)
                raw_text = response["choices"][0]["message"]["content"].strip()

                # Strip markdown code fences if present
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0]

                result = json.loads(raw_text)

                # Add metadata
                result["ai_model"] = self.model
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
                    ai_model=self.model,
                    timestamp=result["timestamp"],
                )

                return validated.model_dump(mode="json")

            except json.JSONDecodeError as exc:
                last_error = exc
                print(f"[AI Reasoning] JSON parse error on attempt {attempt + 1}: {exc}")
            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()
                if "429" in error_str or "rate" in error_str:
                    wait_time = 10 * (attempt + 1)
                    print(f"[AI Reasoning] Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"[AI Reasoning] Error on attempt {attempt + 1}: {exc}")
                    if attempt == max_retries - 1:
                        break
                    time.sleep(2)

        # Return a fallback structure if all retries failed
        print(f"[AI Reasoning] All {max_retries} attempts failed. Last error: {last_error}")
        return AIReasoning(
            drawing_summary=f"AI reasoning failed after {max_retries} attempts: {last_error}",
            ai_model=self.model,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump(mode="json")
