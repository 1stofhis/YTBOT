# filepath: c:\Users\biqda\Desktop\YTBOT\ytbot-faceless-video\src\youtube_bot.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# ...existing code...
import os
import pickle
import requests
import urllib.request
from moviepy.editor import VideoFileClip, AudioFileClip
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config import CONFIG

def youtube_auth():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json',
                ['https://www.googleapis.com/auth/youtube.upload']
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def generate_voiceover(script):
    headers = {
        "xi-api-key": CONFIG["ELEVENLABS_API_KEY"],
        "Content-Type": "application/json"
    }
    data = {
        "text": script,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream"
    response = requests.post(url, headers=headers, json=data)
    with open("voiceover.mp3", "wb") as f:
        f.write(response.content)

def download_stock_video():
    headers = {"Authorization": CONFIG["PEXELS_API_KEY"]}
    response = requests.get(
        "https://api.pexels.com/videos/search?query=nature&per_page=1",
        headers=headers
    ).json()
    video_url = response["videos"][0]["video_files"][0]["link"]
    urllib.request.urlretrieve(video_url, "stock.mp4")

def build_video():
    videoclip = VideoFileClip("stock.mp4").subclip(0, 30)
    audioclip = AudioFileClip("voiceover.mp3")
    videoclip = videoclip.set_audio(audioclip)
    videoclip.write_videofile("final_video.mp4", fps=24)

def upload_video():
    youtube = youtube_auth()
    description = CONFIG["SCRIPT"] + f"\n\nAffiliate: https://amazon.com/?tag={CONFIG['AMAZON_TAG']}"
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": CONFIG["TITLE"],
                "description": description,
                "tags": CONFIG["TAGS"],
                "categoryId": CONFIG["CATEGORY"]
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload("final_video.mp4")
    )
    return request.execute()

if __name__ == "__main__":
    print("🎤 Creating Voiceover...")
    generate_voiceover(CONFIG["SCRIPT"])
    print("🎥 Downloading Stock Footage...")
    download_stock_video()
    print("🎬 Building Final Video...")
    build_video()
    print("📤 Uploading to YouTube...")
    result = upload_video()
    print(f"✅ Done: https://youtube.com/watch?v={result['id']}")