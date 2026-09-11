#!/usr/bin/env python3
"""Fail fast if config.toml is missing or TTS engine is interactive."""
import sys
import tomllib
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config.toml"
ZERO_AUTH_ENGINES = {"streamlabspolly", "googletranslate", "pyttsx"}
def fail(msg: str) -> None:
    print(f"PREFLIGHT FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if not CONFIG.is_file():
        fail("config.toml missing from repo root!")

    raw = CONFIG.read_text(encoding="utf-8")
    try:
        cfg = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        fail(f"config.toml is not valid TOML: {exc}")

    tts = cfg.get("settings", {}).get("tts", {})
    engine = str(tts.get("voice_choice", "")).strip().lower()
    if engine not in ZERO_AUTH_ENGINES:
        fail(f"voice_choice={engine!r} needs interactive login; use one of {sorted(ZERO_AUTH_ENGINES)}")
    if engine == "streamlabspolly" and not str(tts.get("streamlabs_polly_voice", "")).strip():
        fail("streamlabs_polly_voice is empty")

    thread = cfg.get("reddit", {}).get("thread", {})
    if not str(thread.get("subreddit", "")).strip():
        fail("reddit.thread.subreddit is empty")

    settings = cfg.get("settings", {})
    if (settings.get("resolution_w"), settings.get("resolution_h")) != (1080, 1920):
        fail(f"expected 1080x1920, got {settings.get('resolution_w')}x{settings.get('resolution_h')}")

    print(f"PREFLIGHT OK: tts={engine} subreddit={thread['subreddit']} 1080x1920")


if __name__ == "__main__":
    main()
