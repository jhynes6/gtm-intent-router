def score_lead(lead: dict) -> tuple[int, list[str]]:
    """
    Score = ICP fit + intent signal.
    Return (score, reasons).
    """
    score = 0
    reasons: list[str] = []

    def _val(x, default=""):
        v = lead.get(x)
        if v is None or (isinstance(v, float) and (v != v)):
            return default
        return v

    employees = _val("employees", 0) or 0
    industry = str(_val("industry", "")).lower()
    intent = str(_val("intent_signal", "")).lower()
    title = str(_val("title", "")).lower()

    # ICP fit (example rules)
    if 25 <= int(employees) <= 1000:
        score += 30
        reasons.append("ICP employee range")
    if "saas" in industry or "software" in industry:
        score += 20
        reasons.append("ICP industry match")
    if any(
        k in title
        for k in ["vp", "head", "director", "founder", "ceo", "cro", "revops", "growth"]
    ):
        score += 15
        reasons.append("Senior buyer title")

    # Intent signals (example)
    if any(k in intent for k in ["pricing", "demo", "competitor", "integration"]):
        score += 35
        reasons.append("High-intent signal")
    elif intent:
        score += 10
        reasons.append("Some intent signal")

    return score, reasons


def bucket(score: int) -> str:
    if score >= 70:
        return "P0"
    if score >= 45:
        return "P1"
    return "P2"
