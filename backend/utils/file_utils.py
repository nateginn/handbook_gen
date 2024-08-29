import os

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_file_extension(filename):
    return os.path.splitext(filename)[1]

def is_valid_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions