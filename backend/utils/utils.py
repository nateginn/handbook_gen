import os
from config import Config

def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_file_extension(filename):
    """Get the file extension"""
    return os.path.splitext(filename)[1]

def is_valid_file(filename, allowed_extensions=Config.ALLOWED_EXTENSIONS):
    """Check if the file has a valid extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_safe_filename(filename):
    """Generate a safe filename"""
    return ''.join(c for c in filename if c.isalnum() or c in ('-', '_')).rstrip()

def create_temp_file(prefix, suffix, directory=Config.TEMP_DIR):
    """Create a temporary file and return its path"""
    ensure_dir(directory)
    temp_file = os.path.join(directory, f"{prefix}_{os.urandom(8).hex()}{suffix}")
    return temp_file

def clean_temp_files(directory=Config.TEMP_DIR):
    """Remove all files in the temporary directory"""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def get_file_size(file_path):
    """Get the size of a file in bytes"""
    return os.path.getsize(file_path)

def is_file_empty(file_path):
    """Check if a file is empty"""
    return os.path.getsize(file_path) == 0