# Reddit Video Maker Bot - Testing Guide

## Summary of Changes

All requested fixes have been implemented:

### ✅ 1. FFmpeg Binaries
**Status**: Download script created, manual installation required
- Created `download_ffmpeg.py` for automated download
- **Action Required**: Run the script or manually download FFmpeg (see below)

### ✅ 2. videos.json Initialized
**Status**: Complete
- File created at: `D:\RedditVideoMakerBot-master\video_creation\data\videos.json`
- Initialized with empty array: `[]`

### ✅ 3. config.toml Updated
**Status**: Complete
- Dummy credentials configured (satisfies all length checks)
- TTS settings configured:
  - `voice_choice = "googletranslate"`
  - `random_voice = true`

### ✅ 4. reddit/subreddit.py - PRAW Bypass
**Status**: Complete
- Removed PRAW dependency and Reddit login requirement
- Now uses direct Reddit JSON API: `https://www.reddit.com/comments/<post_id>.json`
- Supports both post IDs and full Reddit URLs
- No authentication required for public posts

### ✅ 5. screenshot_downloader.py - Login Bypass
**Status**: Complete
- Removed Reddit login flow (lines 99-129)
- Now accesses public posts directly without authentication
- Maintains all screenshot functionality

---

## FFmpeg Installation (Required)

### Option 1: Automated Download (Recommended)
```powershell
cd D:\RedditVideoMakerBot-master
python download_ffmpeg.py
```
*Note: This downloads ~70MB and may take several minutes*

### Option 2: Manual Download
1. Visit: https://www.gyan.dev/ffmpeg/builds/
2. Download "ffmpeg-release-essentials.zip"
3. Extract and copy from `bin` folder:
   - `ffmpeg.exe` → `D:\RedditVideoMakerBot-master\`
   - `ffprobe.exe` → `D:\RedditVideoMakerBot-master\`

### Verify Installation
```powershell
cd D:\RedditVideoMakerBot-master
.\ffmpeg.exe -version
.\ffprobe.exe -version
```

---

## Testing with a Direct Reddit Thread URL

### Method 1: Using config.toml (Easiest)

1. **Edit config.toml** and set the `post_id` field:
   ```toml
   [reddit.thread]
   post_id = "https://www.reddit.com/r/AskReddit/comments/abc123/example_post/"
   ```
   
   Or use just the post ID:
   ```toml
   [reddit.thread]
   post_id = "abc123"
   ```

2. **Run the bot**:
   ```powershell
   cd D:\RedditVideoMakerBot-master
   python main.py
   ```

### Method 2: Using Command Line

Create a test script `test_render.py`:

```python
import sys
from main import main

# Replace with your Reddit post URL or ID
POST_URL = "https://www.reddit.com/r/AskReddit/comments/abc123/example_post/"

if __name__ == "__main__":
    print(f"Testing with post: {POST_URL}")
    main(POST_ID=POST_URL)
```

Run it:
```powershell
python test_render.py
```

### Method 3: Interactive Testing

Modify `main.py` temporarily to accept command-line arguments:

```python
if __name__ == "__main__":
    # ... existing code ...
    
    # Add this before the try block:
    if len(sys.argv) > 1:
        post_url = sys.argv[1]
        print(f"Using post URL from command line: {post_url}")
        main(POST_ID=post_url)
    else:
        # ... existing main() call ...
```

Then run:
```powershell
python main.py "https://www.reddit.com/r/AskReddit/comments/abc123/example_post/"
```

---

## Example Reddit URLs to Test

Here are some example URLs you can use for testing:

```
https://www.reddit.com/r/AskReddit/comments/1234567/example_title/
https://www.reddit.com/r/funny/comments/abcdef/another_example/
https://www.reddit.com/comments/abc123/
```

**To get a real post ID:**
1. Go to any Reddit post
2. Copy the URL from your browser
3. The post ID is the alphanumeric string after `/comments/`
4. Example: `https://www.reddit.com/r/AskReddit/comments/xyz789/what_is_your_favorite/`
   - Post ID: `xyz789`

---

## Troubleshooting

### Error: "No post_id specified"
- Make sure you set `post_id` in `config.toml` or pass it as a parameter
- The bot no longer fetches random posts from subreddits (PRAW bypass)

### Error: "Failed to fetch Reddit data"
- Check your internet connection
- The Reddit post may be private, deleted, or NSFW
- Try a different public post

### Error: "FFmpeg is not installed"
- Run `python download_ffmpeg.py` or manually install FFmpeg
- Verify with `.\ffmpeg.exe -version`

### Error: "Invalid Reddit response format"
- The post may not exist or may be private
- Try a different public Reddit post

---

## What Changed

### Before (PRAW-based):
- Required valid Reddit API credentials
- Required Reddit login for screenshots
- Used PRAW library to fetch posts
- Could browse subreddit hot/new/top posts

### After (Direct JSON API):
- No Reddit API credentials needed (dummy values work)
- No login required for screenshots
- Uses public Reddit JSON endpoint
- Requires specific post ID or URL
- Faster and simpler authentication flow

---

## Next Steps

1. Install FFmpeg (see above)
2. Choose a public Reddit post URL
3. Set it in `config.toml` under `[reddit.thread]` → `post_id`
4. Run: `python main.py`
5. The bot will:
   - Fetch post data via JSON API
   - Generate TTS audio (Google Translate)
   - Download screenshots
   - Render the final video

Enjoy your Reddit video maker bot! 🎥