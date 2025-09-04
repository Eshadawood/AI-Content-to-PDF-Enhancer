# app/llm.py
import os
import json
import re
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set in environment.")

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Default model (can be overridden in .env)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def build_system_prompt() -> str:
    return (
        "You are an assistant that enhances and validates web articles.\n"
        "Tasks:\n"
        "1) Provide a concise summary.\n"
        "2) Expand with extra neutral context and background information.\n"
        "3) If validation is requested, list main claims and provide reasoning/evidence "
        "(state 'Likely true', 'Uncertain', or 'Likely false').\n"
        "Output format: JSON with keys 'summary', 'expanded', 'validation' (validation optional).\n"
        "Be factual, do not hallucinate sources. If you cannot verify, say so."
    )


def call_openai_enhance(
    article_text: str,
    url: str,
    mode: str = "both",
    level: str = "detailed",
    validate: bool = True,
) -> Dict:
    """
    Call OpenAI to enhance article text with summarization, expansion,
    and optional claim validation.
    """
    prompt = (
        f"Source URL: {url}\n"
        f"Detail level: {level}\n"
        f"Mode: {mode}\n"
        f"Validate: {'yes' if validate else 'no'}\n\n"
        "Article text:\n"
        f"{article_text[:30000]}"  # safety cutoff
    )

    system = build_system_prompt()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    # Call Chat Completions API (new style)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=1500,
    )

    text = resp.choices[0].message.content

    # Try to extract JSON from response
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Fallback: return text wrapped in dict
    return {
        "summary": text if mode in ("summarize", "both") else "",
        "expanded": text if mode in ("expand", "both") else "",
        "validation": (
            "Validation requested but not returned." if validate else ""
        ),
    }
