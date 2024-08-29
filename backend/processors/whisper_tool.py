# whisper_tool.py

import whisper
from pydub import AudioSegment
import numpy as np
import os
import logging
import torch

class WhisperTool:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            self.model = whisper.load_model("base").to(self.device)
            logging.info(f"Whisper model loaded successfully on {self.device}")
        except Exception as e:
            logging.error(f"Error loading Whisper model: {str(e)}")
            raise

    def transcribe_audio(self, audio_file: str) -> str:
        """
        Transcribe the given audio file using Whisper and return the text.
        
        Args:
            audio_file (str): Path to the audio file to be transcribed.
        
        Returns:
            str: The transcribed text from the audio.
        """
        if not os.path.exists(audio_file):
            logging.error(f"Audio file not found: {audio_file}")
            return f"Error: Audio file not found at {audio_file}"

        try:
            logging.info(f"Loading audio file: {audio_file}")
            audio = AudioSegment.from_wav(audio_file)
            audio = audio.set_channels(1)  # Convert to mono
            audio = audio.get_array_of_samples()
            audio = np.array(audio).astype(np.float32) / 32768.0  # Normalize to [-1.0, 1.0]
            logging.info(f"Audio file loaded successfully")

            logging.info(f"Starting transcription of loaded audio on {self.device}")
            result = self.model.transcribe(audio)
            transcription = result['text']
            logging.info("Transcription completed successfully")
            return transcription
        except Exception as e:
            logging.error(f"Error during transcription: {str(e)}")
            return f"Error during transcription: {str(e)}"