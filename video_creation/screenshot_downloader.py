import re
from pathlib import Path
from typing import Final

from utils import settings
from utils.console import print_step
from utils.imagenarator import imagemaker
from video_creation.pil_reddit_cards import render_comment_card, render_post_card

__all__ = ["get_screenshots_of_reddit_posts"]


def get_screenshots_of_reddit_posts(reddit_object: dict, screenshot_num: int):
    """Render Reddit post and comment cards locally with PIL."""
    bgcolor = (33, 33, 36, 255)
    txtcolor = (240, 240, 240)
    transparent = False
    storymode: Final[bool] = settings.config["settings"]["storymode"]

    if settings.config["settings"]["theme"] == "transparent" and storymode:
        bgcolor = (0, 0, 0, 0)
        txtcolor = (255, 255, 255)
        transparent = True

    if storymode and settings.config["settings"]["storymodemethod"] == 1:
        print_step("Generating images...")
        return imagemaker(
            theme=bgcolor,
            reddit_obj=reddit_object,
            txtclr=txtcolor,
            transparent=transparent,
        )

    print_step("Rendering Reddit cards with PIL...")
    reddit_id = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
    output_dir = Path(f"assets/temp/{reddit_id}/png")
    output_dir.mkdir(parents=True, exist_ok=True)

    subreddit = settings.config["reddit"]["thread"]["subreddit"]
    author = reddit_object.get("thread_author", "unknown")
    render_post_card(
        subreddit=subreddit,
        author=author,
        title_text=reddit_object["thread_title"],
        output_path=str(output_dir / "title.png"),
    )

    if storymode:
        render_post_card(
            subreddit=subreddit,
            author=author,
            title_text=reddit_object.get("thread_post", ""),
            output_path=str(output_dir / "story_content.png"),
        )
    else:
        for index, comment in enumerate(reddit_object["comments"][:screenshot_num]):
            render_comment_card(
                author=comment.get("comment_author", "unknown"),
                body_text=comment.get("comment_body", ""),
                output_path=str(output_dir / f"comment_{index}.png"),
            )

    print_step("Reddit cards rendered successfully.")
