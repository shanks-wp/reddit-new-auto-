import json
import random
import re
import subprocess
from pathlib import Path
from random import randrange
from typing import Any, Dict, Tuple

import yt_dlp
from moviepy import AudioFileClip, VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

from utils import settings
from utils.console import print_step, print_substep


def load_background_options():
    _background_options = {}
    with open("./utils/background_videos.json") as json_file:
        _background_options["video"] = json.load(json_file)
    with open("./utils/background_audios.json") as json_file:
        _background_options["audio"] = json.load(json_file)

    del _background_options["video"]["__comment"]
    del _background_options["audio"]["__comment"]

    for name in list(_background_options["video"].keys()):
        pos = _background_options["video"][name][3]
        if pos != "center":
            _background_options["video"][name][3] = lambda t: ("center", pos + t)

    return _background_options


def get_start_and_end_times(video_length: int, length_of_clip: int) -> Tuple[int, int]:
    """Generate a valid random interval from a background asset."""
    initial_value = 180
    while int(length_of_clip) <= int(video_length + initial_value):
        if initial_value == initial_value // 2:
            raise Exception("Your background is too short for this video length")
        initial_value //= 2
    random_time = randrange(initial_value, int(length_of_clip) - int(video_length))
    return random_time, random_time + video_length


def get_background_config(mode: str):
    try:
        choice = str(settings.config["settings"]["background"][f"background_{mode}"]).casefold()
    except AttributeError:
        print_substep("No background selected. Picking random background'")
        choice = None

    if not choice or choice not in background_options[mode]:
        choice = random.choice(list(background_options[mode].keys()))
    return background_options[mode][choice]


def _generate_placeholder_video(path: Path) -> None:
    """Create a deterministic local fallback when no downloaded video exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x1a1a2e:s=1080x1920:d=180",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def _generate_placeholder_audio(path: Path) -> None:
    """Create a deterministic silent local fallback when no audio exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-t",
            "180",
            "-codec:a",
            "libmp3lame",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def download_background_video(background_config: Tuple[str, str, str, Any]):
    """Ensure a local background video exists without depending on YouTube."""
    _, filename, credit, _ = background_config
    path = Path(f"assets/backgrounds/video/{credit}-{filename}")
    if path.is_file():
        return
    print_substep(f"Background video missing; generating placeholder at {path}")
    _generate_placeholder_video(path)


def download_background_audio(background_config: Tuple[str, str, str]):
    """Ensure a local background audio track exists without depending on YouTube."""
    _, filename, credit = background_config
    path = Path(f"assets/backgrounds/audio/{credit}-{filename}")
    if path.is_file():
        return
    print_substep(f"Background audio missing; generating placeholder at {path}")
    _generate_placeholder_audio(path)


def chop_background(background_config: Dict[str, Tuple], video_length: int, reddit_object: dict):
    """Create temporary background audio/video clips for the requested video."""
    thread_id = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
    temp_dir = Path(f"assets/temp/{thread_id}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    if settings.config["settings"]["background"]["background_audio_volume"] == 0:
        print_step("Volume was set to 0. Skipping background audio creation . . .")
    else:
        print_step("Finding a spot in the backgrounds audio to chop...✂️")
        audio_choice = f"{background_config['audio'][2]}-{background_config['audio'][1]}"
        audio_path = Path(f"assets/backgrounds/audio/{audio_choice}")
        with AudioFileClip(str(audio_path)) as source_audio:
            start_time_audio, end_time_audio = get_start_and_end_times(
                video_length, source_audio.duration
            )
            clipped_audio = source_audio.subclipped(start_time_audio, end_time_audio)
            try:
                clipped_audio.write_audiofile(str(temp_dir / "background.mp3"))
            finally:
                clipped_audio.close()

    print_step("Finding a spot in the backgrounds video to chop...✂️")
    video_choice = f"{background_config['video'][2]}-{background_config['video'][1]}"
    video_path = Path(f"assets/backgrounds/video/{video_choice}")
    with VideoFileClip(str(video_path)) as video:
        start_time_video, end_time_video = get_start_and_end_times(
            video_length, video.duration
        )
        try:
            new = video.subclipped(start_time_video, end_time_video)
            try:
                new.write_videofile(str(temp_dir / "background.mp4"), logger=None)
            finally:
                new.close()
        except (OSError, IOError):
            print_substep("FFMPEG issue. Trying again...")
            ffmpeg_extract_subclip(
                str(video_path),
                start_time_video,
                end_time_video,
                outputfile=str(temp_dir / "background.mp4"),
            )
    print_substep("Background video chopped successfully!", style="bold green")
    return background_config["video"][2]


background_options = load_background_options()
