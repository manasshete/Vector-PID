#!/usr/bin/env python3
"""Step 11: Grok Integration & Reasoning Analysis."""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.grok_service import GrokService


async def main_async():
    out_dir = Path("data/outputs")
    final_path = out_dir / "final_analysis.json"

    if not final_path.exists():
        # Try loading individual output files to assemble context
        ocr_path = out_dir / "classified_text.json"
        obj_path = out_dir / "objects.json"
        rel_path = out_dir / "relationships.json"

        if not (ocr_path.exists() and obj_path.exists() and rel_path.exists()):
            print("[*] Intermediate JSON outputs missing. Run previous steps first.")
            sys.exit(1)

        context = {
            "texts": json.loads(ocr_path.read_text()),
            "objects": json.loads(obj_path.read_text()),
            "connections": json.loads(rel_path.read_text()),
            "statistics": {"total_texts": len(json.loads(ocr_path.read_text()))},
        }
    else:
        context = json.loads(final_path.read_text())

    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        print("[!] GROK_API_KEY not set in environment or .env file.")
        print("[!] Demonstrating Grok query subset retrieval structure with mock responses.\n")

    questions = [
        "What is the main process line or service described in this drawing?",
        "List all detected equipment and instrument tags with their coordinates.",
        "Trace connections for compressor or inlet header equipment.",
        "What annotations or notes are referenced on the drawing?",
        "Summarize the process flow between inlet header and export compressor.",
    ]

    print("================================================================================")
    print("  GROK REASONING & QA TEST")
    print("================================================================================\n")

    if api_key:
        grok = GrokService()
        try:
            summary = await grok.summarize_drawing(context)
            print(f"[+] Drawing Scope Summary:\n{summary}\n")

            for i, q in enumerate(questions, 1):
                print(f"[Q{i}] {q}")
                ans = await grok.answer_question(q, context)
                print(f"[A{i}] {ans}\n" + "-" * 60)
                await asyncio.sleep(2.5)

        finally:
            await grok.close()
    else:
        # Mock dry run mode when API key is absent
        print("[+] Drawing Scope Summary (Dry Run):")
        print("This process drawing details the 3rd Stage HP Gas Export Compressor system, including inlet headers, instrument transmitters (PIT-9087), and associated process piping.\n")

        for i, q in enumerate(questions, 1):
            print(f"[Q{i}] {q}")
            print(f"[A{i}] [Mock Grok Response] Retrieved relevant sub-context for query '{q}'. (Set GROK_API_KEY to test live LLM endpoint).\n" + "-" * 60)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
