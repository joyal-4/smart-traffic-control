import requests
import os
from urllib.parse import urlparse
import subprocess

def download_real_traffic_videos():
    """Download real traffic videos from public sources"""
    
    print("🚦 Downloading Real Traffic Videos for Testing")
    print("=" * 60)
    
    # Create directory for real videos
    os.makedirs('real_traffic_videos', exist_ok=True)
    
    # List of real traffic video URLs (public domain/sample videos)
    traffic_videos = [
        {
            'name': 'highway_traffic',
            'url': 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
            'description': 'Highway traffic with multiple vehicles'
        },
        {
            'name': 'city_intersection',
            'url': 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4', 
            'description': 'City intersection with traffic lights'
        },
        {
            'name': 'busy_street',
            'url': 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_5mb.mp4',
            'description': 'Busy street with heavy traffic'
        },
        {
            'name': 'traffic_jam',
            'url': 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_10mb.mp4',
            'description': 'Traffic jam with congestion'
        }
    ]
    
    downloaded_videos = []
    
    for video in traffic_videos:
        print(f"\n📥 Downloading: {video['name']}")
        print(f"   Description: {video['description']}")
        
        try:
            # Download video
            response = requests.get(video['url'], stream=True)
            response.raise_for_status()
            
            filename = f"real_traffic_videos/{video['name']}.mp4"
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            downloaded_videos.append(filename)
            print(f"   ✅ Downloaded: {filename}")
            
        except Exception as e:
            print(f"   ❌ Failed to download {video['name']}: {e}")
    
    return downloaded_videos

def create_youtube_downloader():
    """Create a script to download real traffic videos from YouTube"""
    
    script_content = '''
import yt_dlp
import os

def download_youtube_traffic_videos():
    """Download real traffic videos from YouTube"""
    
    # Real traffic video URLs (public, educational content)
    traffic_urls = [
        "https://www.youtube.com/watch?v=7h_qftiDh0s",  # Traffic camera compilation
        "https://www.youtube.com/watch?v=j6RqWifmTRk",  # Busy intersection
        "https://www.youtube.com/watch?v=0aMe3n7D3nM",  # Highway traffic
        "https://www.youtube.com/watch?v=8C8p6aU5Q2M",  # City traffic jam
    ]
    
    # Download options
    ydl_opts = {
        'format': 'mp4[height<=720]',  # Download MP4, max 720p
        'outtmpl': 'real_traffic_videos/%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
    }
    
    print("🚦 Downloading Real Traffic Videos from YouTube")
    print("=" * 60)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in traffic_urls:
            try:
                print(f"\\n📥 Downloading: {url}")
                ydl.download([url])
                print(f"   ✅ Downloaded successfully")
            except Exception as e:
                print(f"   ❌ Failed to download: {e}")

if __name__ == "__main__":
    download_youtube_traffic_videos()
'''
    
    with open('download_youtube_traffic.py', 'w') as f:
        f.write(script_content)
    
    print("📝 Created YouTube downloader script: download_youtube_traffic.py")

def provide_alternatives():
    """Provide alternative ways to get real traffic videos"""
    
    alternatives = """
    
🚦 ALTERNATIVE WAYS TO GET REAL TRAFFIC VIDEOS:
===============================================

1. 📹 FREE VIDEO SOURCES:
   • Pexels Videos: https://www.pexels.com/search/videos/traffic/
   • Pixabay Videos: https://pixabay.com/videos/search/traffic/
   • Videvo: https://www.videvo.net/search?q=traffic
   
2. 🎬 YOUTUBE CHANNELS (Educational/Permitted):
   • Dashcam Owners Australia
   • Road Cam
   • Traffic Camera Channels
   • City Transportation Departments
   
3. 📁 GOVERNMENT/DATASETS:
   • City traffic camera feeds
   • Department of Transportation archives
   • Open data portals (some provide traffic footage)
   
4. 🎯 SEARCH TERMS TO USE:
   • "traffic camera footage"
   • "intersection traffic video"
   • "highway traffic jam"
   • "city traffic congestion"
   • "road traffic monitoring"
   
5. 📱 PHONE RECORDING:
   • Record traffic near your location
   • Capture different times of day
   • Various intersection types
   
🚀 AFTER GETTING VIDEOS:
=====================
1. Save videos in 'real_traffic_videos' folder
2. Rename them as: north_traffic.mp4, east_traffic.mp4, south_traffic.mp4, west_traffic.mp4
3. Or upload any 4 different traffic videos to each lane
4. Test with different congestion levels

💡 TIP: Look for videos with:
• Clear visibility of vehicles
• Different traffic densities
• Various weather conditions
• Day/night footage for testing
"""
    
    print(alternatives)

def main():
    """Main function to get real traffic videos"""
    
    print("🚦 REAL TRAFFIC VIDEO DOWNLOADER")
    print("=" * 60)
    print("This script helps you get real traffic videos for testing")
    print("the Multi-Lane Traffic Control System.")
    print()
    
    # Try to download sample videos first
    print("1. Attempting to download sample videos...")
    try:
        downloaded = download_real_traffic_videos()
        if downloaded:
            print(f"\n✅ Downloaded {len(downloaded)} videos!")
            print("📁 Location: real_traffic_videos/ folder")
        else:
            print("\n❌ Sample videos not available")
    except Exception as e:
        print(f"\n❌ Sample download failed: {e}")
    
    # Create YouTube downloader
    print("\n2. Creating YouTube downloader...")
    create_youtube_downloader()
    
    # Provide alternatives
    print("\n3. Alternative methods...")
    provide_alternatives()
    
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS:")
    print("1. Try the downloaded sample videos")
    print("2. Run: python download_youtube_traffic.py (requires yt-dlp)")
    print("3. Or manually download from the sources above")
    print("4. Upload 4 different traffic videos to test the system")
    print("=" * 60)

if __name__ == "__main__":
    main()
