from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .ai_personalizer import personalize
from .config import load_config
from .enrich import enrich
from .routing import route_owner
from .scoring import bucket
from .scoring import score_lead
from .sinks import post_to_slack
from .sinks import slack_payload


def run(csv_path: str | None = None, output_path: str | None = None) -> None:
    load_dotenv()
    cfg = load_config()

    if not csv_path:
        raise ValueError("Please provide --csv path")

    df = pd.read_csv(csv_path)
    leads = df.to_dict(orient="records")

    out = []
    for lead in leads:
        lead = enrich(lead, cfg.enrich_provider, cfg.clearbit_api_key)

        score, reasons = score_lead(lead)
        lead["score"] = score
        lead["score_reasons"] = reasons
        lead["priority"] = bucket(score)
        lead["owner"] = route_owner(lead)

        p = personalize(lead)  # Uses OPENAI_API_KEY if set; otherwise mock fallback.
        lead["ai_subject"] = p.subject
        lead["ai_first_line"] = p.first_line
        lead["ai_cta"] = p.cta
        lead["ai_body"] = p.body
        lead["ai_confidence"] = p.confidence

        # Notify Slack only for top priorities
        if cfg.slack_webhook_url and lead["priority"] in ["P0", "P1"]:
            post_to_slack(cfg.slack_webhook_url, slack_payload(lead))

        out.append(lead)

    out_df = pd.DataFrame(out)[
        [
            "name",
            "email",
            "company",
            "employees",
            "industry",
            "intent_signal",
            "score",
            "priority",
            "owner",
            "ai_subject",
            "ai_first_line",
        ]
    ]
    sorted_df = out_df.sort_values(["priority", "score"], ascending=[True, False])
    print(sorted_df.to_string(index=False))

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sorted_df.to_csv(output_path, index=False)
        print(f"\nSaved enriched output to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Input CSV path")
    parser.add_argument("-o", "--output", help="Output CSV path for enriched results")
    args = parser.parse_args()
    run(args.csv, args.output)
