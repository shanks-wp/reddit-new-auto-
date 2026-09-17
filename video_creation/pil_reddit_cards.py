import os
import textwrap

from PIL import Image, ImageDraw, ImageFont


FONT_DIR = "fonts"


def _wrap_and_measure(draw, text, font, wrap_width):
    lines = textwrap.wrap(text, width=wrap_width) or [""]
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        height = bbox[3] - bbox[1]
        line_heights.append(height)
        total_height += height
    return lines, line_heights, total_height


def render_post_card(
    subreddit,
    author,
    title_text,
    output_path,
    width=1000,
    wrap_width=40,
):
    padding = 40
    title_font = ImageFont.truetype(os.path.join(FONT_DIR, "Roboto-Bold.ttf"), 44)
    meta_font = ImageFont.truetype(os.path.join(FONT_DIR, "Roboto-Bold.ttf"), 26)

    dummy = Image.new("RGB", (width, 100))
    draw = ImageDraw.Draw(dummy)
    lines, line_heights, title_height = _wrap_and_measure(
        draw, title_text, title_font, wrap_width
    )

    meta_height = 40
    total_height = padding * 3 + meta_height + title_height + (len(lines) - 1) * 10

    image = Image.new("RGB", (width, total_height), color="#1A1A1B")
    draw = ImageDraw.Draw(image)
    draw.text(
        (padding, padding),
        f"r/{subreddit}  •  Posted by u/{author}",
        font=meta_font,
        fill="#818384",
    )

    y = padding + meta_height
    for line, height in zip(lines, line_heights):
        draw.text((padding, y), line, font=title_font, fill="#D7DADC")
        y += height + 10

    image.save(output_path)


def render_comment_card(
    author,
    body_text,
    output_path,
    width=1000,
    wrap_width=45,
):
    padding = 35
    author_font = ImageFont.truetype(os.path.join(FONT_DIR, "Roboto-Bold.ttf"), 28)
    body_font = ImageFont.truetype(os.path.join(FONT_DIR, "Roboto-Bold.ttf"), 32)

    dummy = Image.new("RGB", (width, 100))
    draw = ImageDraw.Draw(dummy)
    lines, line_heights, body_height = _wrap_and_measure(
        draw, body_text, body_font, wrap_width
    )

    author_height = 40
    total_height = padding * 3 + author_height + body_height + (len(lines) - 1) * 8

    image = Image.new("RGB", (width, total_height), color="#1A1A1B")
    draw = ImageDraw.Draw(image)
    draw.text((padding, padding), f"u/{author}", font=author_font, fill="#4FBCFF")

    y = padding + author_height
    for line, height in zip(lines, line_heights):
        draw.text((padding, y), line, font=body_font, fill="#D7DADC")
        y += height + 8

    image.save(output_path)
