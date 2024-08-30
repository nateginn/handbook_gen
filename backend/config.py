import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # General configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File paths
    INPUT_DIR = os.path.join(BASE_DIR, 'input_files')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'output_files')
    TEMP_DIR = os.path.join(BASE_DIR, 'temp_files')

    # API keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

    # Model settings
    WHISPER_MODEL = 'base'
    GPT_MODEL = 'gpt-4o-mini'
    GROQ_MODEL = 'llama-3.1-70b-versatile'

    # Processing settings
    MAX_FILES_PER_SESSION = 5
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'wav', 'mp3'}

    # Logging configuration
    LOG_FILE = os.path.join(BASE_DIR, 'app.log')
    LOG_LEVEL = 'INFO'