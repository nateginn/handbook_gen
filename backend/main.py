import os
import asyncio
from typing import List
from config import Config
from logger import logger
from utils import is_valid_file, get_file_extension
from database.db_handler import DatabaseHandler
from services.task_manager import TaskManager, FileType
from staging_manager import staging_manager
from cleanup_manager import cleanup_manager

def create_directories():
    os.makedirs(Config.INPUT_DIR, exist_ok=True)
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    logger.info(f"Directories created or already exist: {Config.INPUT_DIR}, {Config.OUTPUT_DIR}")

def get_file_list(directory: str) -> List[str]:
    try:
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except FileNotFoundError:
        logger.error(f"Directory not found: {directory}")
        return []

def user_select_files(file_list: List[str]) -> List[str]:
    selected_files = []
    while True:
        print("\nAvailable files:")
        for idx, file in enumerate(file_list, 1):
            print(f"{idx}. {file}")
        choice = input("Enter the number of the file to process (or 0 to finish): ")
        if choice == '0':
            break
        try:
            choice = int(choice)
            if 0 < choice <= len(file_list):
                selected_files.append(file_list[choice - 1])
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    return selected_files

async def process_files(task_manager: TaskManager, selected_files: List[str]):
    for file in selected_files:
        file_path = os.path.join(Config.INPUT_DIR, file)
        file_type = get_file_type(file)
        if file_type:
            staged_path = staging_manager.stage_file(file_path, file_type.name)
            if staged_path:
                task_manager.add_task(staged_path, file_type)
            else:
                logger.error(f"Failed to stage file: {file_path}")

    await task_manager.run()

def get_file_type(file_name: str) -> FileType:
    extension = get_file_extension(file_name).lower()
    if extension in ['.wav', '.mp3']:
        return FileType.AUDIO
    elif extension in ['.jpg', '.png', '.pdf']:
        return FileType.IMAGE
    elif extension == '.txt':
        return FileType.TEXT
    elif extension == '.mp4':
        return FileType.YOUTUBE
    else:
        logger.warning(f"Unsupported file type: {file_name}")
        return None

def display_results(task_manager: TaskManager):
    print("\nProcessing Results:")
    for file_path, task in task_manager.tasks.items():
        print(f"File: {os.path.basename(file_path)}")
        print(f"Status: {task.status}")
        if task.status == task_manager.TaskStatus.COMPLETED:
            print(f"Result: {task.result[:100]}..." if task.result else "No result")
        elif task.status == task_manager.TaskStatus.NEEDS_VERIFICATION:
            print(f"Needs verification. Low confidence segments: {len(task.low_confidence_segments)}")
        elif task.status == task_manager.TaskStatus.FAILED:
            print(f"Error: {task.error}")
        print()

async def main():
    create_directories()
    db_handler = DatabaseHandler()
    task_manager = TaskManager()

    while True:
        print("\nNote Crew 2 - Backend Testing")
        print("1. Process Files")
        print("2. Display Task Status")
        print("3. Verify OCR Results")
        print("4. Generate Handbook")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            file_list = get_file_list(Config.INPUT_DIR)
            selected_files = user_select_files(file_list)
            await process_files(task_manager, selected_files)
            display_results(task_manager)

        elif choice == '2':
            status = task_manager.get_status()
            print("\nCurrent Task Status:")
            for key, value in status.items():
                print(f"{key}: {value}")

        elif choice == '3':
            tasks_needing_verification = task_manager.get_tasks_needing_verification()
            if not tasks_needing_verification:
                print("No tasks need verification.")
            else:
                for task in tasks_needing_verification:
                    print(f"\nFile: {os.path.basename(task.file_path)}")
                    print("Low confidence segments:")
                    for segment in task.low_confidence_segments:
                        print(f"- {segment['text']} (Confidence: {segment['confidence']})")
                    verified_text = input("Enter the corrected text (or press Enter to skip): ")
                    if verified_text:
                        await task_manager.apply_user_verification(task.file_path, verified_text)

        elif choice == '4':
            topic = input("Enter the topic for the handbook: ")
            await task_manager.create_handbook(topic)

        elif choice == '5':
            print("Exiting the program. Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

    cleanup_manager.perform_cleanup()
    logger.info("Exiting the script.")

if __name__ == "__main__":
    asyncio.run(main())