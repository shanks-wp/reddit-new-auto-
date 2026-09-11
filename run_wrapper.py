import subprocess
import sys
import os

os.chdir(r"d:\RedditVideoMakerBot-master")
log_path = r"d:\RedditVideoMakerBot-master\bot_output.log"

with open(log_path, "w") as log:
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=r"d:\RedditVideoMakerBot-master",
    )
    proc.wait()

print(f"Bot exited with code {proc.returncode}")
print(f"Log saved to: {log_path}")

