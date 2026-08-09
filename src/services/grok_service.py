"""Alternative Grok API service. Compatible with OpenAI-compatible endpoints."""
import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an engineering drawing analysis assistant.
You receive ONLY structured information extracted by computer vision.
Use ONLY the supplied information. NEVER invent:
- equipment tags, pipe tags, valve tags
- dimensions, services, connections
If information is missing or uncertain, say so explicitly.
Reference object IDs and detected text whenever possible.
Distinguish: 1) detected facts 2) inferred relationships 3) uncertain information"""


class GrokService:
    """Semantic reasoning layer via OpenAI-compatible API. Never performs CV tasks."""

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

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def _chat(self, messages: list[dict[str, str]], temperature: float = 0.1) -> dict[str, Any]:
        """Internal chat completion call with automatic retry on 429 rate limits."""
        import asyncio
        max_retries = 5
        backoff = 4.0

        for attempt in range(max_retries):
            try:
                response = await self.client.post(
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
                    await asyncio.sleep(backoff * (attempt + 1))
                else:
                    raise

    async def classify_text(self, text: str) -> dict:
        """Classify ambiguous engineering text via Grok."""
        classifier_system_prompt = (
            SYSTEM_PROMPT + "\n\nClassify the given text into exactly one category:\n"
            "- PIPE_TAG, EQUIPMENT_TAG, INSTRUMENT_TAG, LINE_NUMBER, PIPE_SIZE, SERVICE, "
            "DIMENSION, ANNOTATION, DRAWING_REFERENCE, GRID_LABEL, UNKNOWN\n"
            "Respond ONLY with valid JSON: {\"classification\": \"CATEGORY\", \"confidence\": 0.0-1.0}"
        )
        messages = [
            {"role": "system", "content": classifier_system_prompt},
            {"role": "user", "content": f"Classify this engineering text: '{text}'"},
        ]
        response = await self._chat(messages, temperature=0.0)
        content = response["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        return json.loads(content)

    async def analyze_drawing(self, context: dict) -> dict:
        """Full drawing structural analysis via Grok."""
        trimmed_context = {
            "drawing": context.get("drawing"),
            "statistics": context.get("statistics"),
            "sample_texts": context.get("texts", [])[:20],
            "sample_objects": context.get("objects", [])[:15],
            "sample_connections": context.get("connections", [])[:15],
        }
        summary_prompt = (
            "Analyze the following structured P&ID metadata and return a JSON summary:\n"
            "{\"summary\": \"...\", \"key_components\": [...], \"recommendations\": [...]}\n\n"
            f"Context: {json.dumps(trimmed_context, indent=2)}"
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": summary_prompt},
        ]
        response = await self._chat(messages, temperature=0.1)
        content = response["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        try:
            return json.loads(content)
        except Exception:
            return {"raw_analysis": content}

    async def summarize_drawing(self, context: dict) -> str:
        """Produce a concise 3-sentence drawing scope summary."""
        trimmed_context = {
            "drawing": context.get("drawing"),
            "statistics": context.get("statistics"),
            "sample_texts": context.get("texts", [])[:15],
            "sample_objects": context.get("objects", [])[:10],
        }
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Provide a concise 3-sentence summary of the engineering drawing scope based ONLY on this context:\n{json.dumps(trimmed_context, indent=2)}",
            },
        ]
        response = await self._chat(messages, temperature=0.2)
        return response["choices"][0]["message"]["content"].strip()

    async def reason_about_relationships(self, relationships: list[dict]) -> dict:
        """Interpret and validate connectivity and flow relationships."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Interpret these extracted spatial relationships and identify key process flow paths:\n{json.dumps(relationships, indent=2)}",
            },
        ]
        response = await self._chat(messages, temperature=0.1)
        content = response["choices"][0]["message"]["content"].strip()
        return {"interpretation": content}

    async def answer_question(self, question: str, context: dict) -> str:
        """Answer question using ONLY relevant subset of context matching query keywords."""
        # Retrieve relevant subset of context
        q_lower = question.lower()
        sub_objects = []
        sub_texts = []
        sub_connections = []

        # Find matching texts
        matching_text_ids = set()
        for t in context.get("texts", []):
            txt_str = t.get("text", "").lower()
            txt_id = t.get("id", "")
            if any(term in txt_str for term in q_lower.split()) or txt_id.lower() in q_lower:
                sub_texts.append(t)
                matching_text_ids.add(txt_id)

        # Find matching objects
        matching_obj_ids = set()
        for o in context.get("objects", []):
            o_id = o.get("id", "")
            o_type = o.get("type", "").lower()
            assoc_txt = (o.get("associated_text") or {}).get("text", "").lower()
            if o_id.lower() in q_lower or o_type in q_lower or any(term in assoc_txt for term in q_lower.split()):
                sub_objects.append(o)
                matching_obj_ids.add(o_id)

        # Find matching connections
        relevant_ids = matching_text_ids | matching_obj_ids
        for conn in context.get("connections", []):
            if conn.get("from_id") in relevant_ids or conn.get("to_id") in relevant_ids:
                sub_connections.append(conn)

        # Fallback if no specific subset matched
        if not sub_objects and not sub_texts:
            sub_objects = context.get("objects", [])[:15]
            sub_texts = context.get("texts", [])[:25]
            sub_connections = context.get("connections", [])[:20]

        # Cap items to prevent HTTP 413 Payload Too Large
        sub_context = {
            "drawing_stats": context.get("statistics", {}),
            "relevant_objects": sub_objects[:15],
            "relevant_texts": sub_texts[:20],
            "relevant_connections": sub_connections[:20],
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nRelevant Context Subset:\n{json.dumps(sub_context, indent=2)}",
            },
        ]
        response = await self._chat(messages, temperature=0.1)
        return response["choices"][0]["message"]["content"].strip()

    async def close(self):
        await self.client.aclose()