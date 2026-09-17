import json
import re
import textwrap
from pathlib import Path
from typing import Dict, Final

import translators
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import ViewportSize, sync_playwright
from rich.progress import track

from utils import settings
from utils.console import print_step, print_substep
from utils.imagenarator import imagemaker
from utils.playwright import clear_cookie_by_name
from utils.videos import save_data

__all__ = ["get_screenshots_of_reddit_posts"]


def _render_comment_card(comment: dict, output_path: str) -> None:
    width = 900
    padding = 40
    author_font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 32)
    body_font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 40)
    body_lines = textwrap.wrap(comment["comment_body"], width=35) or [""]
    draw_probe = ImageDraw.Draw(Image.new("RGB", (width, 1)))
    author = comment["comment_author"]
    _, _, _, author_height = draw_probe.textbbox((0, 0), author, font=author_font)
    line_heights = [
        draw_probe.textbbox((0, 0), line, font=body_font)[3] for line in body_lines
    ]
    height = padding + author_height + 30 + sum(line_heights) + padding
    image = Image.new("RGB", (width, height), "#1a1a1b")
    draw = ImageDraw.Draw(image)
    draw.text((padding, padding), author, font=author_font, fill="#d7dadc")
    y = padding + author_height + 30
    for line, line_height in zip(body_lines, line_heights):
        draw.text((padding, y), line, font=body_font, fill="#ffffff")
        y += line_height
    image.save(output_path)


def get_screenshots_of_reddit_posts(reddit_object: dict, screenshot_num: int):
    """Downloads screenshots of reddit posts as seen on the web. Downloads to assets/temp/png

    Args:
        reddit_object (Dict): Reddit object received from reddit/subreddit.py
        screenshot_num (int): Number of screenshots to download
    """
    W: Final[int] = int(settings.config["settings"]["resolution_w"])
    H: Final[int] = int(settings.config["settings"]["resolution_h"])
    lang: Final[str] = settings.config["reddit"]["thread"]["post_lang"]
    storymode: Final[bool] = settings.config["settings"]["storymode"]

    print_step("Downloading screenshots of reddit posts...")
    reddit_id = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
    Path(f"assets/temp/{reddit_id}/png").mkdir(parents=True, exist_ok=True)

    if settings.config["settings"]["theme"] == "dark":
        cookie_file = open("./video_creation/data/cookie-dark-mode.json", encoding="utf-8")
        bgcolor = (33, 33, 36, 255)
        txtcolor = (240, 240, 240)
        transparent = False
    elif settings.config["settings"]["theme"] == "transparent":
        if storymode:
            bgcolor = (0, 0, 0, 0)
            txtcolor = (255, 255, 255)
            transparent = True
            cookie_file = open("./video_creation/data/cookie-dark-mode.json", encoding="utf-8")
        else:
            cookie_file = open("./video_creation/data/cookie-dark-mode.json", encoding="utf-8")
            bgcolor = (33, 33, 36, 255)
            txtcolor = (240, 240, 240)
            transparent = False
    else:
        cookie_file = open("./video_creation/data/cookie-light-mode.json", encoding="utf-8")
        bgcolor = (255, 255, 255, 255)
        txtcolor = (0, 0, 0)
        transparent = False

    if storymode and settings.config["settings"]["storymodemethod"] == 1:
        print_substep("Generating images...")
        return imagemaker(theme=bgcolor, reddit_obj=reddit_object, txtclr=txtcolor, transparent=transparent)

    screenshot_num: int
    with sync_playwright() as p:
        print_substep("Launching Headless Browser...")
        browser = p.chromium.launch(headless=True, channel="chrome")
        dsf = (W // 600) + 1

        context = browser.new_context(
            locale="en-US",
            color_scheme="dark",
            viewport=ViewportSize(width=W, height=H),
            device_scale_factor=dsf,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            extra_http_headers={
                "Dnt": "1",
                "Sec-Ch-Ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            },
        )
        cookies = json.load(cookie_file)
        cookie_file.close()
        context.add_cookies(cookies)

        print_substep("Skipping Reddit login (using public access)...")
        page = context.new_page()

        page.goto(reddit_object["thread_url"], timeout=0)
        page.set_viewport_size(ViewportSize(width=W, height=H))
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(15000)
        print(f"DEBUG: navigating to {page.url}")
        page.screenshot(path=f"debug_page_{reddit_id}.png", full_page=True)
        print(f"DEBUG: page title = {page.title()}")
        print(f"DEBUG: page content first 500 chars = {page.content()[:500]}")
        print(f"DEBUG: js_challenge present = {'js_challenge' in page.url}")

        if page.locator("#t3_12hmbug > div > div._3xX726aBn29LDbsDtzr_6E._1Ap4F5maDtT1E1YuCiaO0r.D3IL3FD0RFy_mkKLPwL4 > div > div > button").is_visible():
            print_substep("Post is NSFW. You are spicy...")
            page.locator("#t3_12hmbug > div > div._3xX726aBn29LDbsDtzr_6E._1Ap4F5maDtT1E1YuCiaO0r.D3IL3FD0RFy_mkKLPwL4 > div > div > button").click()
            page.wait_for_load_state()

        if page.locator("#SHORTCUT_FOCUSABLE_DIV > div:nth-child(7) > div > div > div > header > div > div._1m0iFpls1wkPZJVo38-LSh > button > i").is_visible():
            page.locator("#SHORTCUT_FOCUSABLE_DIV > div:nth-child(7) > div > div > div > header > div > div._1m0iFpls1wkPZJVo38-LSh > button > i").click()

        if lang:
            print_substep("Translating post...")
            texts_in_tl = translators.translate_text(reddit_object["thread_title"], to_language=lang, translator="google")
            page.evaluate("tl_content => document.querySelector('[data-adclicklocation=\"title\"] > div > div > h1').textContent = tl_content", texts_in_tl)
        else:
            print_substep("Skipping translation...")

        postcontentpath = f"assets/temp/{reddit_id}/png/title.png"
        try:
            try:
                page.wait_for_selector("shreddit-app, #AppRouter-appHTMLShell, main", timeout=20000)
            except Exception:
                pass
            try:
                page.wait_for_selector("shreddit-post, [data-test-id='post-content']", timeout=15000)
            except Exception:
                pass
            if page.locator("shreddit-post").count() > 0:
                post_locator = page.locator("shreddit-post").first
            else:
                post_locator = page.locator('[data-test-id="post-content"]').first

            if settings.config["settings"]["zoom"] != 1:
                zoom = settings.config["settings"]["zoom"]
                page.evaluate("document.body.style.zoom=" + str(zoom))
                location = post_locator.bounding_box()
                for i in location:
                    location[i] = float("{:.2f}".format(location[i] * zoom))
                page.screenshot(clip=location, path=postcontentpath)
            else:
                post_locator.screenshot(path=postcontentpath)
        except Exception as e:
            print_substep("Something went wrong!", style="red")
            save_data("", "", "skipped", reddit_id, "")
            print_substep("The post is automatically skipped because its screenshot could not be created.", "yellow")
            raise RuntimeError(f"Unable to create the title screenshot for post {reddit_id}") from e

        if storymode:
            page.locator('[data-click-id="text"]').first.screenshot(path=f"assets/temp/{reddit_id}/png/story_content.png")
        else:
            for idx, comment in enumerate(track(reddit_object["comments"][:screenshot_num], "Downloading screenshots...")):
                if idx >= screenshot_num:
                    break
                _render_comment_card(comment, f"assets/temp/{reddit_id}/png/comment_{idx}.png")

        browser.close()

    print_substep("Screenshots downloaded Successfully.", style="bold green")
