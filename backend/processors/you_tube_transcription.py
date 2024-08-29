import yt_dlp
import moviepy.editor as mp
import whisper
import os
from datetime import datetime
import re
import shutil

def get_best_format(url):
    ydl_opts = {
        'listformats': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)
        formats = result.get('formats', [])
        
        best_video_format = max(
            (f for f in formats if f.get('vcodec') != 'none' and f.get('height') is not None),
            key=lambda f: f.get('height', 0)
        )
        
        best_audio_format = max(
            (f for f in formats if f.get('acodec') != 'none' and f.get('abr') is not None),
            key=lambda f: f.get('abr', 0)
        )
        
        return f"{best_video_format['format_id']}+{best_audio_format['format_id']}"

def sanitize_title(title):
    # Remove invalid characters and limit the length of the title
    title = re.sub(r'[\\/*?:"<>|]', "", title)  # Remove invalid characters 
    title = title[:50]  # Limit to 50 characters
    title = title.strip() # Remove leading and trailing spaces
    return title

def download_video(url, save_path, format_id):
    try:
        with yt_dlp.YoutubeDL({
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'format': format_id,
        }) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'downloaded_video')
            sanitized_title = sanitize_title(video_title)
            print(f"Download completed! Title: {sanitized_title}")
            # Rename the downloaded file to match the sanitized title
            original_video_path = ydl.prepare_filename(info_dict)
            new_video_path = os.path.join(save_path, f"{sanitized_title}.mp4")
            os.rename(original_video_path, new_video_path)
            return sanitized_title, new_video_path
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None, None

def extract_audio(video_path, audio_path):
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)

def transcribe_audio(audio_path, output_file):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    with open(output_file, "w") as file:
        file.write(result["text"])

def main():
    video_url = input("Enter the YouTube video URL: ")
    final_txt_path = input("Enter the path for the folder to place final txt product: ")
    base_path = r"C:\Users\nginn\SE Programs\PYTHON\YOU_TUBE_CONTENT\video_to_text"

    # Download the video
    format_id = get_best_format(video_url)
    video_title, new_video_path = download_video(video_url, base_path, format_id)
    if not video_title:
        print("Failed to download video.")
        return

    # Create a directory named after the sanitized video title
    folder_path = os.path.join(base_path, video_title)
    os.makedirs(folder_path, exist_ok=True)
    print(f"Created folder: {folder_path}")

    # Move the video file to the new folder
    final_video_path = os.path.join(folder_path, f"{video_title}.mp4")
    os.rename(new_video_path, final_video_path)

    # Paths for audio and transcription
    audio_path = os.path.join(folder_path, f"{video_title}.mp3")
    date_str = datetime.now().strftime("%m.%d.%Y")
    output_file = os.path.join(folder_path, f"{video_title}.{date_str}.txt")

    # Extract audio from the video
    extract_audio(final_video_path, audio_path)
    print(f"Audio extracted to {audio_path}")

    # Transcribe the audio
    transcribe_audio(audio_path, output_file)
    print(f"Transcription saved to {output_file}")
    
    #Copy txt file into designated folder
    destination_path = os.path.join(final_txt_path, os.path.basename(output_file))
    shutil.copy(output_file, destination_path)
    print(f"Transcription file copied to {destination_path}")

if __name__ == "__main__":
    main()
