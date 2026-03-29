
import yt_dlp
import os

# Real traffic video URLs (public, educational content)
traffic_videos = [
    "https://www.youtube.com/watch?v=7h_qftiDh0s",  # Traffic camera
    "https://www.youtube.com/watch?v=j6RqWifmTRk",  # Busy intersection  
    "https://www.youtube.com/watch?v=0aMe3n7D3nM",  # Highway traffic
    "https://www.youtube.com/watch?v=8C8p6aU5Q2M",  # City traffic
]

# Download options
ydl_opts = {
    'format': 'mp4[height<=720][filesize<=50M]',  # MP4, max 720p, max 50MB
    'outtmpl': 'real_traffic_videos/%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'max_downloads': 4,  # Limit to 4 videos
}

print("Downloading real traffic videos...")

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(traffic_videos)
    print("Download completed!")
    print("Videos saved in: real_traffic_videos/")
except Exception as e:
    print(f"Download failed: {e}")
    print("You can manually download videos from:")
    print("- Pexels Videos: https://www.pexels.com/search/videos/traffic/")
    print("- Pixabay Videos: https://pixabay.com/videos/search/traffic/")
