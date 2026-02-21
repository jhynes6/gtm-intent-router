import json

import requests


def post_to_slack(webhook_url: str, payload: dict) -> None:
    r = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    r.raise_for_status()


def slack_payload(lead: dict) -> dict:
    return {
        "text": (
            f"🔥 New {lead['priority']} lead: {lead.get('name', '')} @ {lead.get('company', '')} "
            f"(score={lead['score']}) -> owner: {lead['owner']}\n"
            f"Reasons: {', '.join(lead.get('score_reasons', []))}"
        )
    }
