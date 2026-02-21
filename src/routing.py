def route_owner(lead: dict) -> str:
    """
    Simple territory routing example.
    Replace with your org rules (geo, segment, vertical, round-robin, etc.)
    """
    country = (lead.get("country") or "US").upper()
    employees = int(lead.get("employees") or 0)

    if country in ["US", "CA"]:
        if employees >= 500:
            return "enterprise@company.com"
        return "amer-smb@company.com"

    if country in ["GB", "IE", "DE", "FR", "NL"]:
        return "emea@company.com"

    return "row@company.com"
