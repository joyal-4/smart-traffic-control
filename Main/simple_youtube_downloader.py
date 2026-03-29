import os
import subprocess
import sys

def install_yt_dlp():
    """Install yt-dlp for YouTube video downloading"""
    try:
        print("Installing yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        print("yt-dlp installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install yt-dlp")
        return False

def create_download_script():
    """Create a simple YouTube download script"""
    
    script_content = '''
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
'''
    
    with open('download_traffic.py', 'w') as f:
        f.write(script_content)
    
    print("Created download_traffic.py script")

def main():
    print("🚦 Real Traffic Video Downloader")
    print("=" * 50)
    
    # Create directory
    os.makedirs('real_traffic_videos', exist_ok=True)
    
    # Try to install yt-dlp
    if install_yt_dlp():
        # Create download script
        create_download_script()
        
        print("\nNext steps:")
        print("1. Run: python download_traffic.py")
        print("2. Or manually download from free video sites")
        print("3. Check real_traffic_guide.md for more options")
    else:
        print("\nManual download options:")
        print("1. Pexels: https://www.pexels.com/search/videos/traffic/")
        print("2. Pixabay: https://pixabay.com/videos/search/traffic/")
        print("3. Videvo: https://www.videvo.net/search?q=traffic")

if __name__ == "__main__":
    main()
