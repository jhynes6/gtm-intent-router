from dataclasses import dataclass
import os


@dataclass
class Config:
    enrich_provider: str = os.getenv("ENRICH_PROVIDER", "mock")
    clearbit_api_key: str | None = os.getenv("CLEARBIT_API_KEY") or None
    slack_webhook_url: str | None = os.getenv("SLACK_WEBHOOK_URL") or None


def load_config() -> Config:
    return Config()
