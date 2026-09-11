import importlib
import shutil
import sys

lines = []
lines.append(f"python: {sys.version}")
for mod in (
    "gtts",
    "rich",
    "playwright",
    "translators",
    "yt_dlp",
    "flask",
    "tomlkit",
    "moviepy",
    "praw",
    "prawcore",
    "pyttsx3",
    "spacy",
    "requests",
    "toml",
):
    try:
        importlib.import_module(mod)
        lines.append(f"{mod}: OK")
    except Exception as e:
        lines.append(f"{mod}: FAIL {e}")
lines.append(f"ffmpeg_on_path: {shutil.which('ffmpeg')}")
lines.append(f"ffmpeg_local: {shutil.which('ffmpeg.exe') is not None}")

with open("diag_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
