# GTM Intent Router (Enrich → Score → Route)

A small GTM engineering demo: ingest leads, enrich firmographics, score intent, route ownership, and notify Slack.
Designed to mimic real RevOps workflows (lifecycle automation, routing, and signal-based selling).

## What it does

- **Ingest** leads from CSV or webhook JSON
- **Enrich** leads (mock enrichment by default; supports Clearbit-style enrichment)
- **Score** leads based on ICP fit + intent signal
- **Route** leads to an owner based on territory rules
- **AI personalization** — generates first-line, CTA, and email body (OpenAI or mock)
- **Output** to Slack (and optionally CRM)

## Quickstart

1. Create a virtual env and install deps:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Copy env template:

```bash
cp .env.example .env
```

3. Run on sample data:

```bash
python -m src.main --csv sample_data/leads.csv
```

4. (Optional) Save enriched output to a CSV:

```bash
python -m src.main --csv sample_data/leads.csv -o output/enriched_leads.csv
```

## Notes

- Enrichment is mocked by default so the repo runs without API keys.
- AI personalization uses OpenAI if `OPENAI_API_KEY` is set; otherwise falls back to a safe mock.
- Add your own enrichment + CRM writeback in `src/sinks.py`.
