import json
from pathlib import Path

THREAD_TITLE = "What are some of the actual open secrets in Hollywood?"
THREAD_ID = "1wb3gwv"

COMMENTS = [
    ("corivscori", "And a lot of the rumors and blind gossip and even just social media are fueled by publicists. If they aren't outright creating them for them to be made, usually with more information or secrets they've picked up about actors that aren't theirs. If you see a sudden change in public opinion about someone, know that someone bigger is having something hidden."),
    ("CrazeMase", "As someone who's worked with horses. Horses get treated very well. Based on coat shine and ear placement, it's clear that even in scenes where the horses are 'distressed' that those horses are happy as can be. They do a trick, they get apple slices and pets."),
    ("FrancoisTruser", "Now i feel better about the one in the swamp of despair"),
    ("DrWeinerWrinkle", "As someone who was born and raised on a farm, stallions are one of the most terrifying animals on the planet when in heat, and studs even more so."),
    ("UntamedMegasloth", "To this day she can't eat a four foot long angry rigid sausage without flashbacks."),
]

reddit_obj = {
    "thread_id": THREAD_ID,
    "thread_title": THREAD_TITLE,
    "thread_url": f"https://new.reddit.com/r/AskReddit/comments/{THREAD_ID}/",
    "thread_post": "",
    "is_nsfw": False,
    "comments": [
        {
            "comment_id": f"manual_{i}",
            "comment_url": f"/r/AskReddit/comments/{THREAD_ID}/comment_{i}/",
            "comment_body": body,
            "comment_author": author,
        }
        for i, (author, body) in enumerate(COMMENTS)
    ],
}

Path("assets/temp").mkdir(parents=True, exist_ok=True)
out_path = Path("manual_reddit_obj.json")
out_path.write_text(json.dumps(reddit_obj, indent=2), encoding="utf-8")
print(f"Wrote {out_path.resolve()}")
