# whisper_tool.py

import os
import whisper
import torch
import numpy as np
from pydub import AudioSegment
from typing import Optional
import tempfile
from config import Config
from logger import logger
from utils import is_valid_file, get_file_extension
from staging_manager import staging_manager
from cleanup_manager import cleanup_manager

# Uncomment when integrating with database
# from database.db_handler import DatabaseHandler

class WhisperTool:
    def __init__(self, model_name: str = Config.WHISPER_MODEL_NAME):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model(model_name).to(self.device)
        logger.info(f"Whisper model loaded successfully on {self.device}")
        
        # Uncomment when integrating with database
        # self.db_handler = DatabaseHandler()

    def preprocess_audio(self, audio_file: str, duration: Optional[int] = None) -> np.ndarray:
        logger.info(f"Loading audio file: {audio_file}")
        try:
            audio = AudioSegment.from_file(audio_file)
            if duration:
                audio = audio[:duration * 1000]  # pydub works in milliseconds
            audio = audio.set_channels(1)  # Convert to mono
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            samples = samples / 32768.0  # Normalize to [-1.0, 1.0]
            logger.info(f"Audio file preprocessed successfully")
            return samples
        except Exception as e:
            logger.error(f"Error preprocessing audio file: {str(e)}")
            raise

    def transcribe_audio(self, audio_file: str, test_mode: bool = False) -> str:
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        if not is_valid_file(audio_file, Config.ALLOWED_AUDIO_EXTENSIONS):
            logger.error(f"Invalid audio file format: {audio_file}")
            raise ValueError(f"Invalid audio file format: {audio_file}")

        try:
            duration = 5 * 60 if test_mode else None  # 5 minutes for test mode
            audio = self.preprocess_audio(audio_file, duration)

            logger.info(f"Starting transcription of loaded audio on {self.device}")
            result = self.model.transcribe(audio)
            transcription = result["text"]
            logger.info("Transcription completed successfully")
            
            # Stage the transcription result
            staged_path = staging_manager.stage_file(audio_file, "transcription", transcription)
            logger.info(f"Transcription staged at: {staged_path}")
            
            return transcription
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            raise

    def edit_transcription(self, transcription: str) -> str:
        print("\nTranscription result:")
        print(transcription)
        print("\nWould you like to edit this transcription? (yes/no)")
        if input().lower() == 'yes':
            print("Enter your edited transcription (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            return "\n".join(lines)
        return transcription

    def save_to_file(self, content: str, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Transcription saved to {output_path}")

        # Uncomment when integrating with database
        # try:
        #     topic_id = self.db_handler.get_or_create_topic("Audio Transcriptions")
        #     source_id = self.db_handler.add_source(topic_id, "audio", output_path)
        #     self.db_handler.add_content(source_id, "text", content)
        #     logger.info(f"Transcription saved to database. Source ID: {source_id}")
        # except Exception as e:
        #     logger.error(f"Error saving transcription to database: {str(e)}")

    def process_audio(self, audio_file: str, output_directory: str, test_mode: bool = False):
        try:
            transcription = self.transcribe_audio(audio_file, test_mode)
            edited_transcription = self.edit_transcription(transcription)

            # Save to file
            file_name = os.path.splitext(os.path.basename(audio_file))[0]
            output_path = os.path.join(output_directory, f"{file_name}_transcription.txt")
            self.save_to_file(edited_transcription, output_path)

            # Cleanup temporary files
            cleanup_manager.cleanup_temp_files()

        except Exception as e:
            logger.error(f"Error processing {audio_file}: {str(e)}")

def main():
    whisper_tool = WhisperTool()
    audio_file = input("Enter the path to the audio file: ")
    output_directory = input("Enter the output directory: ")
    whisper_tool.process_audio(audio_file, output_directory)

if __name__ == "__main__":
    main()