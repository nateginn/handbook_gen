import os
import logging
import asyncio
from dotenv import load_dotenv
from backend.services.task_manager import TaskManager, FileType
from backend.database.db_handler import DatabaseHandler

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directories
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_dir = os.path.join(base_dir, "input_files")
output_dir = os.path.join(base_dir, "output_files")

def create_directories():
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Directories created or already exist: {input_dir}, {output_dir}")

def get_file_list(directory):
    try:
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except FileNotFoundError:
        logging.error(f"Directory not found: {directory}")
        return []

def user_select_files(file_list):
    selected_files = []
    while True:
        print("\nAvailable files:")
        for idx, file in enumerate(file_list, 1):
            print(f"{idx}. {file}")
        choice = input("Enter the number of the file to process (or 0 to finish): ")
        if choice == '0':
            break
        if choice.isdigit() and 0 < int(choice) <= len(file_list):
            selected_files.append(file_list[int(choice) - 1])
        else:
            print("Invalid choice. Please try again.")
    return selected_files

async def process_files(task_manager, selected_files):
    for file in selected_files:
        file_path = os.path.join(input_dir, file)
        file_type = get_file_type(file)
        if file_type:
            task_manager.add_task(file_path, file_type)
    
    await task_manager.run()

def get_file_type(file_name):
    extension = os.path.splitext(file_name)[1].lower()
    if extension in ['.wav', '.mp3']:
        return FileType.AUDIO
    elif extension in ['.jpg', '.png', '.pdf']:
        return FileType.IMAGE
    elif extension == '.txt':
        return FileType.TEXT
    else:
        logging.warning(f"Unsupported file type: {file_name}")
        return None

def display_results(task_manager):
    print("\nProcessing Results:")
    for file_path, task in task_manager.tasks.items():
        print(f"File: {os.path.basename(file_path)}")
        print(f"Status: {task.status}")
        if task.status == TaskStatus.COMPLETED:
            print(f"Result: {task.result[:100]}..." if task.result else "No result")
        elif task.status == TaskStatus.NEEDS_VERIFICATION:
            print(f"Needs verification. Low confidence segments: {len(task.low_confidence_segments)}")
        elif task.status == TaskStatus.FAILED:
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
            file_list = get_file_list(input_dir)
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
                        await task_manager.apply_user_verification(task.file_path, {"text": verified_text, "confidence": 1.0})

        elif choice == '4':
            topic = input("Enter the topic for the handbook: ")
            await task_manager.create_handbook(topic)

        elif choice == '5':
            print("Exiting the program. Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

    logging.info("Exiting the script.")

if __name__ == "__main__":
    asyncio.run(main())