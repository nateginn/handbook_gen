# you_tube_transcription

import yt_dlp
import moviepy.editor as mp
import whisper
import os
import re
from datetime import datetime
from config import Config
from logger import logger
from utils import is_valid_url, get_safe_filename
from staging_manager import staging_manager
from cleanup_manager import cleanup_manager

# Uncomment when integrating with database
# from database.db_handler import DatabaseHandler

def get_ffmpeg_path():
    ffmpeg_path = Config.FFMPEG_PATH
    if not os.path.exists(ffmpeg_path):
        logger.error(f"FFmpeg not found at {ffmpeg_path}")
        raise FileNotFoundError(f"FFmpeg not found at {ffmpeg_path}")
    return ffmpeg_path

def get_best_format(url):
    ydl_opts = {'listformats': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info['formats']
            best_video = max((f for f in formats if f['vcodec'] != 'none'), key=lambda f: f.get('height', 0))
            best_audio = max((f for f in formats if f['acodec'] != 'none'), key=lambda f: f.get('abr', 0))
            return f"{best_video['format_id']}+{best_audio['format_id']}"
        except Exception as e:
            logger.error(f"Error getting best format: {str(e)}")
            raise

def download_video(url, save_path, format_id, ffmpeg_path):
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'ffmpeg_location': ffmpeg_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            clean_name = get_safe_filename(os.path.basename(filename))
            new_path = os.path.join(save_path, clean_name)
            os.rename(filename, new_path)
            return clean_name, new_path
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise

def extract_audio(video_path, audio_path):
    try:
        video = mp.VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    try:
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise

def edit_transcription(transcription):
    print("\nTranscription result:")
    print(transcription)
    if input("\nWould you like to edit this transcription? (yes/no): ").lower() == 'yes':
        print("Enter your edited transcription (press Enter twice to finish):")
        return "\n".join(iter(input, ""))
    return transcription

def main():
    try:
        ffmpeg_path = get_ffmpeg_path()
        video_url = input("Enter the YouTube video URL: ")
        
        if not is_valid_url(video_url):
            logger.error(f"Invalid YouTube URL: {video_url}")
            raise ValueError(f"Invalid YouTube URL: {video_url}")

        working_dir = Config.TEMP_DIR
        os.makedirs(working_dir, exist_ok=True)

        format_id = get_best_format(video_url)
        video_name, video_path = download_video(video_url, working_dir, format_id, ffmpeg_path)
        logger.info(f"Video downloaded: {video_path}")

        audio_path = os.path.join(working_dir, f"{os.path.splitext(video_name)[0]}.mp3")
        extract_audio(video_path, audio_path)
        logger.info(f"Audio extracted: {audio_path}")

        transcription = transcribe_audio(audio_path)
        edited_transcription = edit_transcription(transcription)

        # Stage the transcription result
        staged_path = staging_manager.stage_file(video_path, "youtube_transcription", edited_transcription)
        logger.info(f"Transcription staged at: {staged_path}")

        # Uncomment when integrating with database
        # db_handler = DatabaseHandler()
        # try:
        #     topic_id = db_handler.get_or_create_topic("YouTube Transcriptions")
        #     source_id = db_handler.add_source(topic_id, "youtube", video_url)
        #     content_id = db_handler.add_content(source_id, "text", edited_transcription)
        #     logging.info(f"Transcription saved to database. Content ID: {content_id}")
        # except Exception as e:
        #     logging.error(f"Error saving to database: {str(e)}")

        # Clean up working files
        os.remove(video_path)
        os.remove(audio_path)
        logging.info("Working files cleaned up")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()