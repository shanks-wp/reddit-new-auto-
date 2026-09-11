#!/usr/bin/env python3
"""Generate a daily batch of videos and write a Drive-friendly manifest."""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
TRACKING_FILE = ROOT / "video_creation" / "data" / "videos.json"
MANIFEST_FILE = RESULTS_DIR / "daily_manifest.csv"
VIDEO_COUNT = 10


def sanitize_filename(title: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")
    return (cleaned or "reddit-video")[:180]


def load_tracking() -> list[dict]:
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TRACKING_FILE.exists():
        TRACKING_FILE.write_text("[]\n", encoding="utf-8")
    with TRACKING_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def find_output(record: dict, before: set[Path]) -> Path | None:
    original_name = record.get("filename", "")
    expected = RESULTS_DIR / record.get("subreddit", "") / original_name
    if expected.is_file():
        return expected

    candidates = [
        path
        for path in RESULTS_DIR.rglob("*.mp4")
        if path not in before and path.name != MANIFEST_FILE.name
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def append_manifest(row: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    needs_header = not MANIFEST_FILE.exists() or MANIFEST_FILE.stat().st_size == 0
    with MANIFEST_FILE.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["filename", "title", "subreddit", "date", "description"],
        )
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


def run_iteration(iteration: int, run_date: str) -> bool:
    before_files = set(RESULTS_DIR.rglob("*.mp4")) if RESULTS_DIR.exists() else set()
    before_tracking = {entry["id"] for entry in load_tracking()}
    command = [sys.executable, "main.py"]
    print(f"Starting video {iteration}/{VIDEO_COUNT}", flush=True)
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as error:
        print(f"Video {iteration}/{VIDEO_COUNT} failed with exit code {error.returncode}", flush=True)
        return False

    new_records = [entry for entry in load_tracking() if entry["id"] not in before_tracking]
    if not new_records:
        print(f"Video {iteration}/{VIDEO_COUNT} produced no new tracking record", flush=True)
        return False
    record = new_records[-1]
    output = find_output(record, before_files)
    if output is None:
        print(f"Video {iteration}/{VIDEO_COUNT} produced no MP4 output", flush=True)
        return False

    destination = output.with_name(f"{run_date}_{sanitize_filename(record['reddit_title'])}.mp4")
    if destination != output:
        destination.unlink(missing_ok=True)
        output.rename(destination)
    append_manifest(
        {
            "filename": destination.name,
            "title": record["reddit_title"],
            "subreddit": record["subreddit"],
            "date": run_date,
            "description": f"{record['reddit_title']} — a reddit stories compilation",
        }
    )
    print(f"Video {iteration}/{VIDEO_COUNT} succeeded: {destination.name}", flush=True)
    return True


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_date = date.today().isoformat()
    successes = 0
    for iteration in range(1, VIDEO_COUNT + 1):
        try:
            if run_iteration(iteration, run_date):
                successes += 1
        except Exception as error:
            print(f"Video {iteration}/{VIDEO_COUNT} failed: {type(error).__name__}: {error}", flush=True)
    print(f"Batch complete: {successes}/{VIDEO_COUNT} videos succeeded", flush=True)
    return 0 if successes else 1


if __name__ == "__main__":
    raise SystemExit(main())
