import os
import shutil
from datetime import datetime
from config import Config
from logger import logger
from utils import ensure_dir, get_safe_filename

class StagingManager:
    def __init__(self):
        self.staging_dir = os.path.join(Config.BASE_DIR, 'staging')
        ensure_dir(self.staging_dir)

    def stage_file(self, source_path, file_type):
        """
        Stage a file by copying it to the staging area.
        Returns the path of the staged file.
        """
        try:
            filename = get_safe_filename(os.path.basename(source_path))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            staged_filename = f"{timestamp}_{file_type}_{filename}"
            staged_path = os.path.join(self.staging_dir, staged_filename)

            shutil.copy2(source_path, staged_path)
            logger.info(f"File staged: {staged_path}")
            return staged_path
        except Exception as e:
            logger.error(f"Error staging file {source_path}: {str(e)}")
            return None

    def get_staged_files(self):
        """
        Return a list of all files in the staging area.
        """
        return [f for f in os.listdir(self.staging_dir) if os.path.isfile(os.path.join(self.staging_dir, f))]

    def clear_staging_area(self):
        """
        Remove all files from the staging area.
        """
        for filename in os.listdir(self.staging_dir):
            file_path = os.path.join(self.staging_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    logger.info(f"Removed staged file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing staged file {file_path}: {str(e)}")

    def remove_staged_file(self, filename):
        """
        Remove a specific file from the staging area.
        """
        file_path = os.path.join(self.staging_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                logger.info(f"Removed staged file: {file_path}")
            else:
                logger.warning(f"Staged file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error removing staged file {file_path}: {str(e)}")

staging_manager = StagingManager()