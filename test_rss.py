import feedparser
import sys

url = "https://www.reddit.com/comments/1fcu8k4/.rss"
print(f"Fetching: {url}")
feed = feedparser.parse(url)
print(f"Bozo: {feed.bozo}")
print(f"Entries count: {len(feed.entries)}")
if feed.entries:
    print(f"First entry title: {feed.entries[0].title}")
    print(f"First entry link: {feed.entries[0].link}")
    if len(feed.entries) > 1:
        print(f"Second entry title: {feed.entries[1].title}")
else:
    print("No entries found!")
    if feed.bozo:
        print(f"Bozo exception: {feed.bozo_exception}")
sys.exit(0)
