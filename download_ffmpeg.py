import requests
import zipfile
import os
import shutil

# Use GyanD essentials build (smaller, faster download)
url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
zip_file = 'ffmpeg.zip'

print('Downloading FFmpeg essentials build from gyan.dev...')
print('This may take a few minutes...')

# Stream download for better progress
with requests.get(url, stream=True, timeout=600) as r:
    r.raise_for_status()
    total_size = int(r.headers.get('content-length', 0))
    downloaded = 0
    
    with open(zip_file, 'wb') as f:
        for chunk in r.iter_chunked(8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size:
                percent = (downloaded / total_size) * 100
                print(f'\rDownloading: {percent:.1f}% ({downloaded}/{total_size} bytes)', end='', flush=True)

print('\nDownload complete!')
print('Extracting...')

with zipfile.ZipFile(zip_file, 'r') as z:
    z.extractall('.')
os.remove(zip_file)

# Find the extracted folder
folders = [d for d in os.listdir('.') if d.startswith('ffmpeg-') and os.path.isdir(d)]
if not folders:
    print('ERROR: Could not find extracted FFmpeg folder')
    exit(1)
    
folder = folders[0]
print(f'Found folder: {folder}')

# Copy binaries to root
shutil.copy(os.path.join(folder, 'bin', 'ffmpeg.exe'), '.')
shutil.copy(os.path.join(folder, 'bin', 'ffprobe.exe'), '.')
print('Copied ffmpeg.exe and ffprobe.exe to project root')

# Clean up
shutil.rmtree(folder)
print('Cleanup complete!')
print('FFmpeg binaries installed successfully!')
