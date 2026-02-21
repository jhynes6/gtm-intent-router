from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Optional

import requests


@dataclass
class AIPersonalization:
    subject: str
    first_line: str
    cta: str
    body: str
    confidence: float
    notes: str


def _clean(s: Any) -> str:
    if s is None or (isinstance(s, float) and (s != s)):  # NaN check
        return ""
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _clamp(n: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, n))


def _build_prompt(lead: Dict[str, Any]) -> str:
    """
    Keep this deterministic + enterprise friendly:
    - no creepy personal info
    - no claims that imply browsing
    - rely only on lead fields provided
    """
    name = _clean(lead.get("name", ""))
    title = _clean(lead.get("title", ""))
    company = _clean(lead.get("company", ""))
    industry = _clean(lead.get("industry", ""))
    employees = lead.get("employees")
    intent = _clean(lead.get("intent_signal", ""))

    return f"""
You are an expert B2B GTM copywriter. Write a safe, non-creepy, high-converting outbound email personalization.

Context (only use this info; do NOT invent facts or claim you browsed):
- Prospect name: {name or "Unknown"}
- Prospect title: {title or "Unknown"}
- Company: {company or "Unknown"}
- Industry: {industry or "Unknown"}
- Company size (employees): {employees or "Unknown"}
- Observed intent signal: {intent or "Unknown"}

Task:
Return a JSON object with keys:
- subject: string (<= 7 words)
- first_line: string (1 sentence, personalized but not creepy)
- cta: string (1 sentence, low-friction ask)
- body: string (<= 90 words total, including first_line + 1-2 value points + cta; professional, direct)
- confidence: number between 0 and 1 (how confident you are given limited data)
- notes: string (1 sentence explaining what you used)

Constraints:
- Do NOT mention tracking, surveillance, or that you saw their activity.
- Do NOT invent company facts (no funding, tech stack, recent news, etc.).
- Keep tone: concise, technical, respectful.
- Value prop: "We help GTM teams automate enrichment, scoring, routing, and AI personalization to increase qualified pipeline."
""".strip()


def _mock_personalization(lead: Dict[str, Any]) -> AIPersonalization:
    name = _clean(lead.get("name")) or "there"
    title = _clean(lead.get("title")) or "your team"
    company = _clean(lead.get("company")) or "your company"
    intent = _clean(lead.get("intent_signal"))

    intent_hint = ""
    if intent:
        intent_hint = f" If you're exploring {intent},"

    first_line = f"Hi {name} - saw you're leading {title} at {company}.{intent_hint}"
    first_line = re.sub(r"\.\s*If", ". If", first_line).strip()

    cta = "Open to a 12-minute chat next week to see if this could help?"
    body = (
        f"{first_line}\n\n"
        "We help GTM teams automate enrichment, scoring, routing, and AI-driven personalization "
        "so reps spend less time on ops and more time closing.\n\n"
        f"{cta}"
    )

    return AIPersonalization(
        subject="Automating your lead workflow",
        first_line=first_line,
        cta=cta,
        body=body,
        confidence=0.55,
        notes="Mock mode using provided title/company/intent signal only.",
    )


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Try to extract a JSON object even if the model wraps it in prose.
    """
    text = (text or "").strip()
    if not text:
        return None

    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None

    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def personalize_with_openai(
    lead: Dict[str, Any],
    *,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    timeout_s: int = 30,
) -> AIPersonalization:
    """
    Uses OpenAI Chat Completions API over HTTP (no openai python package required).

    Env vars supported:
    - OPENAI_API_KEY
    - OPENAI_MODEL (optional)
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", model)

    if not api_key:
        return _mock_personalization(lead)

    prompt = _build_prompt(lead)

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
        r.raise_for_status()
        data = r.json()

        text_out = ""
        try:
            text_out = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            text_out = json.dumps(data)

        parsed = _extract_json(text_out)
        if not parsed:
            return _mock_personalization(lead)

        subject = _clean(parsed.get("subject", "")) or "Quick question"
        first_line = _clean(parsed.get("first_line", "")) or "Hi - quick question."
        cta = _clean(parsed.get("cta", "")) or "Worth a quick chat?"
        body = (parsed.get("body") or "").strip() or f"{first_line}\n\n{cta}"
        confidence = _clamp(float(parsed.get("confidence", 0.6)))
        notes = _clean(parsed.get("notes", "")) or "Generated with OpenAI from provided fields."

        return AIPersonalization(
            subject=subject,
            first_line=first_line,
            cta=cta,
            body=body,
            confidence=confidence,
            notes=notes,
        )
    except Exception:
        # Never fail the full pipeline if personalization errors.
        return _mock_personalization(lead)


def personalize(
    lead: Dict[str, Any],
    provider: str = "openai",
    **kwargs: Any,
) -> AIPersonalization:
    """
    Provider router. Keep this simple and extensible for public repos.
    """
    provider = (provider or "openai").lower()
    if provider == "openai":
        return personalize_with_openai(lead, **kwargs)
    return _mock_personalization(lead)
