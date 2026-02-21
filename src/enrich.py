from __future__ import annotations

import math
import requests


def _or_default(val, default):
    """Treat None and NaN as missing."""
    if val is None:
        return default
    if isinstance(val, float) and math.isnan(val):
        return default
    if val == "":
        return default
    return val


def enrich_mock(lead: dict) -> dict:
    """
    Mock enrichment so the repo runs without API keys.
    """
    domain = (lead.get("email") or "").split("@")[-1].lower()
    company = domain.split(".")[0].title() if domain else "Unknown"

    # Simple fake firmographics based on domain patterns
    employees = 50 if "studio" in domain else 250
    industry = "B2B SaaS" if domain else "Unknown"

    return {
        **lead,
        "company": _or_default(lead.get("company"), company),
        "domain": _or_default(lead.get("domain"), domain),
        "employees": _or_default(lead.get("employees"), employees),
        "industry": _or_default(lead.get("industry"), industry),
        "country": _or_default(lead.get("country"), "US"),
    }


def enrich_clearbit(lead: dict, api_key: str) -> dict:
    """
    Example Clearbit-style enrichment (you can swap providers).
    WARNING: do not hardcode keys; use env vars.
    """
    email = lead.get("email")
    if not email:
        return lead

    url = "https://person.clearbit.com/v2/combined/find"
    r = requests.get(url, params={"email": email}, auth=(api_key, ""), timeout=30)
    if r.status_code != 200:
        return lead

    data = r.json()
    company = (data.get("company") or {}) if isinstance(data.get("company"), dict) else {}
    person = (data.get("person") or {}) if isinstance(data.get("person"), dict) else {}

    return {
        **lead,
        "company": lead.get("company") or company.get("name"),
        "domain": lead.get("domain") or company.get("domain"),
        "employees": lead.get("employees") or company.get("metrics", {}).get("employees"),
        "title": lead.get("title") or person.get("employment", {}).get("title"),
        "country": lead.get("country") or (company.get("geo") or {}).get("country"),
        "industry": lead.get("industry") or company.get("category", {}).get("industry"),
    }


def enrich(lead: dict, provider: str, clearbit_api_key: str | None) -> dict:
    if provider == "clearbit" and clearbit_api_key:
        return enrich_clearbit(lead, clearbit_api_key)
    return enrich_mock(lead)
