import re
import time
import html
from typing import Dict, List
import feedparser
from playwright.sync_api import sync_playwright

from utils import settings
from utils.console import print_step, print_substep
from utils.videos import check_done

# Safely import sanitize_text to prevent missing module crashes
try:
    from utils.videos import sanitize_text
except ImportError:
    def sanitize_text(text):
        return text

REDDIT_RSS_BASE = "https://www.reddit.com"

def _fetch_rss_via_browser(url: str) -> str:
    try:
        import os

        user_data_dir = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir,
                channel="chrome",
                headless=False,
                args=[
                    "--profile-directory=Default",
                    "--no-first-run",
                    "--disable-session-crashed-bubble",
                    "--disable-infobars",
                ],
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            response = page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            print(f"DEBUG: status={response.status if response else 'None'}, final_url={page.url}")
            body_text = response.text() if response else ""
            print(f"DEBUG: response body length={len(body_text)}, first 300 chars={body_text[:300]}")
            browser.close()
            return body_text
    except Exception as error:
        print(f"RSS browser fetch error: {type(error).__name__}: {error}")
        raise

def _extract_post_id_from_link(link: str) -> str:
    match = re.search(r"/comments/([a-zA-Z0-9]+)/", link)
    if not match:
        return "unknown"
    return match.group(1)

def _clean_html(raw_html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _fetch_feed_with_retry(url: str, retries: int = 3, delay: float = 2.0):
    for attempt in range(retries):
        try:
            raw_xml = _fetch_rss_via_browser(url)
            feed = feedparser.parse(raw_xml)
        except Exception as error:
            print(f"RSS retry wrapper error on attempt {attempt + 1}: {type(error).__name__}: {error}")
            raise
        if not feed.bozo and feed.entries:
            return feed
        if feed.bozo:
            print(f"RSS parse error: {type(feed.bozo_exception).__name__}: {feed.bozo_exception}")
        time.sleep(delay)
    raise ConnectionError(f"Failed to fetch RSS feed from {url}. Check your internet connection.")

def get_subreddit_threads(POST_ID: str = None):
    print_step("Getting subreddit threads via RSS (Ultimate JSON API bypass)")

    subreddit_name = settings.config["reddit"]["thread"]["subreddit"]
    
    if POST_ID:
        post_id = POST_ID
        post_feed_url = f"{REDDIT_RSS_BASE}/comments/{post_id}/.rss"
        post_feed = _fetch_feed_with_retry(post_feed_url)

        if not post_feed.entries:
            raise ValueError(f"No entries found for post id {post_id}")

        top_entry = post_feed.entries[0]
        thread_title = top_entry.title
        thread_link = top_entry.link
        
        thread_body_html = getattr(top_entry, "content", [{"value": ""}])[0]["value"]
        thread_body = _clean_html(thread_body_html)
        comment_entries = post_feed.entries[1:]

    else:
        listing_url = f"{REDDIT_RSS_BASE}/r/{subreddit_name}/top/.rss"
        listing_feed = _fetch_feed_with_retry(listing_url)

        if not listing_feed.entries:
            raise ValueError(f"No entries found for r/{subreddit_name}")

        chosen = None
        for candidate in listing_feed.entries:
            candidate_id = _extract_post_id_from_link(candidate.link)
            candidate_object = {"thread_id": candidate_id}
            if check_done(candidate_object) is not None:
                chosen = candidate
                break
        if chosen is None:
            raise RuntimeError("All posts in the top RSS listing have already been generated.")
        thread_link = chosen.link
        thread_title = chosen.title
        post_id = _extract_post_id_from_link(thread_link)

        comments_feed_url = f"{REDDIT_RSS_BASE}/comments/{post_id}/.rss"
        comments_feed = _fetch_feed_with_retry(comments_feed_url)
        comment_entries = comments_feed.entries[1:] if comments_feed.entries else []

        thread_body_html = getattr(chosen, "content", [{"value": ""}])[0]["value"]
        thread_body = _clean_html(thread_body_html)

    print_substep(f"Selected post: {thread_title} (id: {post_id})")

    max_comments = settings.config["reddit"]["thread"]["max_comments_to_read"]
    min_comments = settings.config["reddit"]["thread"]["min_comments_to_read"]
    max_length = settings.config.get("reddit", {}).get("thread", {}).get("max_comment_length", 500)
    min_length = settings.config.get("reddit", {}).get("thread", {}).get("min_comment_length", 10)

    comments: List[Dict] = []
    
    for entry in comment_entries:
        if len(comments) >= max_comments:
            break
            
        author = entry.author if hasattr(entry, "author") else "u/unknown"
        
        # Safely parse the body content
        if hasattr(entry, "content"):
            raw_body = entry.content[0].value
        else:
            raw_body = entry.get("summary", "")
            
        body_text = _clean_html(raw_body)
        body_text = sanitize_text(body_text) # removes blocked words
        
        if not body_text:
            continue
            
        if len(body_text) > max_length or len(body_text) < min_length:
            continue

        # ULTIMATE FIX: Extracting the exact, pure Comment ID for Playwright
        raw_link = entry.link.rstrip('/')
        extracted_comment_id = raw_link.split('/')[-1]
        
        # Failsafe: If for some reason the feed returns the post link instead of the deep comment link
        if extracted_comment_id == post_id:
            continue

        comments.append(
            {
                "comment_id": extracted_comment_id,
                "comment_url": entry.link,
                "comment_body": body_text,
                "comment_author": author.replace("u/", ""),
            }
        )

    if len(comments) < min_comments:
        print_substep(
            f"Warning: Found {len(comments)} usable comments (below min limit). Proceeding anyway.",
            style="bold yellow"
        )

    reddit_obj = {
        "thread_id": post_id,
        "thread_title": thread_title,
        "thread_url": thread_link,
        "thread_post": thread_body,
        "is_nsfw": False,
        "comments": comments,
    }

    return reddit_obj