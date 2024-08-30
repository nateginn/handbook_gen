import os
import shutil
from datetime import datetime, timedelta
from config import Config
from logger import logger

class CleanupManager:
    def __init__(self):
        self.temp_dir = Config.TEMP_DIR
        self.output_dir = Config.OUTPUT_DIR
        self.max_age_days = 7  # Maximum age of files to keep

    def cleanup_temp_files(self):
        """
        Remove all files in the temporary directory.
        """
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    logger.info(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {str(e)}")

    def cleanup_old_files(self, directory):
        """
        Remove files older than max_age_days in the specified directory.
        """
        try:
            now = datetime.now()
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if now - file_modified > timedelta(days=self.max_age_days):
                        os.unlink(file_path)
                        logger.info(f"Removed old file: {file_path}")
        except Exception as e:
            logger.error(f"Error during old file cleanup in {directory}: {str(e)}")

    def cleanup_empty_directories(self, directory):
        """
        Remove empty subdirectories in the specified directory.
        """
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        logger.info(f"Removed empty directory: {dir_path}")
        except Exception as e:
            logger.error(f"Error during empty directory cleanup in {directory}: {str(e)}")

    def perform_cleanup(self):
        """
        Perform all cleanup operations.
        """
        self.cleanup_temp_files()
        self.cleanup_old_files(self.output_dir)
        self.cleanup_empty_directories(self.output_dir)
        logger.info("Cleanup operations completed")

cleanup_manager = CleanupManager()