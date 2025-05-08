"""
This is a simple YouTube downloader app built with Streamlit.
It allows users to download videos and audio from YouTube.

"""

from io import BytesIO
from urllib.parse import urlparse, parse_qs
import tempfile
import os
import streamlit as st
import yt_dlp


# --- Normalize shortened YouTube URLs ---
def normalize_youtube_url(url):
    parsed = urlparse(url)
    if "youtu.be" in url:
        video_id = parsed.path.strip("/")
        return f"https://www.youtube.com/watch?v={video_id}"
    elif "youtube.com" in url:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [None])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    return url


# --- Download function ---
def download_youtube_content(url, audio_only=False):
    ext = "mp3" if audio_only else "mp4"
    mime = f"audio/{ext}" if audio_only else f"video/{ext}"

    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best" if audio_only else "bestvideo+bestaudio/best",
            "outtmpl": output_template,
            "merge_output_format": "mp4" if not audio_only else None,
            "postprocessors": (
                [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
                if audio_only
                else [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ]
            ),
            "postprocessor_args": (
                ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
                if not audio_only
                else []
            ),
            "prefer_ffmpeg": True,
            "noplaylist": True,
            "quiet": True,
            "geo_bypass": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "download")
            filename = f"{title}.{ext}"
            file_path = os.path.join(temp_dir, filename)

            with open(file_path, "rb") as f:
                content = f.read()

        return BytesIO(content), filename, mime


# -------------------- Streamlit UI --------------------

st.title("🎬 YouTube Downloader (Stream to User)")

url = st.text_input("🔗 Enter YouTube Video URL")
choice = st.radio("Choose download type:", ["Video (MP4)", "Audio (MP3)"])

if st.button("Download"):
    if not url:
        st.warning("⚠️ Please enter a YouTube URL.")
    else:
        normalized_url = normalize_youtube_url(url)
        with st.spinner("⬇️ Downloading... Please wait."):
            try:
                is_audio = choice == "Audio (MP3)"
                buffer, filename, mime = download_youtube_content(
                    normalized_url, audio_only=is_audio
                )

                st.success("✅ Download complete!")
                st.download_button(
                    label=f"📥 Download {filename}",
                    data=buffer,
                    file_name=filename,
                    mime=mime,
                )
            except Exception as e:
                st.error(f"🚨 Error: {str(e)}")
