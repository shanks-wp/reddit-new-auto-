import requests

from utils.console import print_step


LATEST_RELEASE_URL = (
    "https://api.github.com/repos/elebumm/RedditVideoMakerBot/releases/latest"
)


def checkversion(__VERSION__: str):
    """Report the upstream version without making startup depend on GitHub."""
    try:
        response = requests.get(
            LATEST_RELEASE_URL,
            timeout=10,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        latestversion = response.json().get("tag_name")
        if not latestversion:
            raise ValueError("GitHub release response did not contain tag_name")
    except (requests.RequestException, ValueError, TypeError) as error:
        print_step(f"Skipping version check: {error}")
        return False

    if __VERSION__ == latestversion:
        print_step(f"You are using the newest version ({__VERSION__}) of the bot")
        return True
    elif __VERSION__ < latestversion:
        print_step(
            f"You are using an older version ({__VERSION__}) of the bot. Download the newest version ({latestversion}) from https://github.com/elebumm/RedditVideoMakerBot/releases/latest"
        )
    else:
        print_step(
            f"Welcome to the test version ({__VERSION__}) of the bot. Thanks for testing and feel free to report any bugs you find."
        )
    return False
