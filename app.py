import streamlit as st
import yt_dlp
from io import BytesIO
from urllib.parse import urlparse, parse_qs
import tempfile
import os
import shutil

def normalize_youtube_url(url):
    """Convert youtu.be to full youtube.com URL"""
    if "youtu.be" in url:
        video_id = urlparse(url).path.strip("/")
        return f"https://www.youtube.com/watch?v={video_id}"
    elif "youtube.com" in url:
        query = parse_qs(urlparse(url).query)
        video_id = query.get("v", [None])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    return url

def download_youtube_content(url, audio_only=False):
    temp_dir = tempfile.mkdtemp()
    ext = "mp3" if audio_only else "mp4"
    output_path = os.path.join(temp_dir, f"%(title)s.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best' if audio_only else 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,
        'prefer_ffmpeg': True,
        'merge_output_format': 'mp4' if not audio_only else None,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio' if audio_only else 'FFmpegVideoConvertor',
            'preferredcodec': 'mp3' if audio_only else 'mp4',
            'preferredquality': '192'
        }] if audio_only else []
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'download')
        filename = f"{title}.{ext}"
        file_path = os.path.join(temp_dir, filename)

        # Fallback in case expected filename doesn't exist
        if not os.path.exists(file_path):
            for f in os.listdir(temp_dir):
                if f.endswith(ext):
                    file_path = os.path.join(temp_dir, f)
                    break

        with open(file_path, "rb") as f:
            content = f.read()

    shutil.rmtree(temp_dir)  # Clean up all temp files
    return BytesIO(content), filename, f"audio/{ext}" if audio_only else f"video/{ext}"

# -------------------- Streamlit UI --------------------

st.title("🎬 YouTube Downloader (Stream to User)")

url = st.text_input("🔗 Enter YouTube Video URL")
choice = st.radio("What do you want to download?", ["Video (MP4)", "Audio (MP3)"])

if st.button("Download"):
    if not url:
        st.warning("Please enter a YouTube URL.")
    else:
        normalized_url = normalize_youtube_url(url)
        with st.spinner("Downloading... Please wait."):
            try:
                is_audio = choice == "Audio (MP3)"
                buffer, filename, mime = download_youtube_content(normalized_url, audio_only=is_audio)

                st.success("✅ Download ready!")
                st.download_button(
                    label=f"📥 Click to download {filename}",
                    data=buffer,
                    file_name=filename,
                    mime=mime
                )
            except yt_dlp.utils.DownloadError as e:
                st.error("🚫 This video is not available in your region or is age-restricted.")
            except Exception as e:
                st.error(f"🚨 Unexpected error: {str(e)}")
