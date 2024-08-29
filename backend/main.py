import os
import logging
from tools.whisper_tool import WhisperTool
from tools.ocr_tool import process_image
from tools.merge_tool import MergeTool
from tools.audio_transcript_Key_points import AudioTranscriptKeyPoints
from tools.handbook import HandbookCreator
from tools.db_handler import DatabaseHandler
import openai

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directories
input_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\input_files"
output_audio_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_files_audio"
output_ocr_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_txt_files"
output_key_points_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_key_points"

def create_directories():
    directories = [input_dir, output_audio_dir, output_ocr_dir, output_key_points_dir]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Directory created or already exists: {directory}")

def get_file_list(directory, extension):
    try:
        return [f for f in os.listdir(directory) if f.endswith(extension)]
    except FileNotFoundError:
        print(f"Error: Directory not found: {directory}")
        return []

def user_select_file(file_list, file_type):
    if not file_list:
        print(f"No {file_type} files found.")
        return None
    print(f"\nAvailable {file_type} files:")
    for idx, file in enumerate(file_list, 1):
        print(f"{idx}. {file}")
    choice = input(f"Enter the number of the {file_type} file you want to process (or 0 to skip): ")
    if choice.isdigit() and 0 < int(choice) <= len(file_list):
        return file_list[int(choice) - 1]
    return None

def user_select_multiple_files(file_list, file_type):
    selected_files = []
    while file_list:
        print(f"\nAvailable {file_type} files:")
        for idx, file in enumerate(file_list, 1):
            print(f"{idx}. {file}")
        choice = input(f"Enter the number of the {file_type} file you want to include (or 0 to finish): ")
        if choice == '0':
            break
        if choice.isdigit() and 0 < int(choice) <= len(file_list):
            selected_file = file_list[int(choice) - 1]
            selected_files.append(selected_file)
            file_list.remove(selected_file)
        else:
            print("Invalid choice. Please try again.")
    return selected_files

def transcribe_audio(file_path, output_path):
    whisper_tool = WhisperTool()
    transcription = whisper_tool.transcribe_audio(file_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(transcription)
    logging.info(f"Audio transcription saved to {output_path}")

def process_transcriptions():
    processed_files = []

    while True:
        # Process audio files
        remaining_wav_files = get_file_list(input_dir, '.wav')
        if remaining_wav_files:
            print("\nAudio Transcription:")
            selected_wav = user_select_file(remaining_wav_files, 'audio')
            if selected_wav:
                wav_output_path = os.path.join(output_audio_dir, f"{os.path.splitext(selected_wav)[0]}.txt")
                transcribe_audio(os.path.join(input_dir, selected_wav), wav_output_path)
                processed_files.append(f"Audio: {selected_wav}")
                remaining_wav_files.remove(selected_wav)

        # Process image files
        remaining_jpg_files = get_file_list(input_dir, '.jpg')
        while remaining_jpg_files:
            print("\nImage OCR:")
            selected_jpg = user_select_file(remaining_jpg_files, 'image')
            if selected_jpg:
                jpg_input_path = os.path.join(input_dir, selected_jpg)
                jpg_output_path = os.path.join(output_ocr_dir, f"{os.path.splitext(selected_jpg)[0]}.txt")
                try:
                    process_image(jpg_input_path, jpg_output_path)
                    processed_files.append(f"Image: {selected_jpg}")
                except openai.OpenAIError as e:
                    logging.error(f"An error occurred during OCR processing: {str(e)}")
                    print(f"Error: {str(e)}")

                remaining_jpg_files.remove(selected_jpg)

                if remaining_jpg_files:
                    another = input("Do you want to transcribe another image? (yes/no): ").strip().lower()
                    if another != 'yes':
                        break
            else:
                break

        if not remaining_wav_files and not remaining_jpg_files:
            print("\nNo more files to process.")
            break

        rerun = input("\nDo you want to process any remaining files? (yes/no): ").strip().lower()
        if rerun != 'yes':
            break

    return processed_files

def extract_key_points():
    key_points_extractor = AudioTranscriptKeyPoints()
    key_points_extractor.process_file()

def merge_files():
    merge_tool = MergeTool()

    print("\nSelect files for merging:")
    audio_files = get_file_list(output_audio_dir, '.txt')
    ocr_files = get_file_list(output_ocr_dir, '.txt')

    selected_audio = user_select_multiple_files(audio_files, 'audio transcript')
    selected_ocr = user_select_multiple_files(ocr_files, 'OCR transcript')

    if not selected_audio and not selected_ocr:
        print("No files selected for merging.")
        return

    selected_files = [os.path.join(output_audio_dir, f) for f in selected_audio] + \
                     [os.path.join(output_ocr_dir, f) for f in selected_ocr]

    # Select key points file
    key_points_files = get_file_list(output_key_points_dir, '.txt')
    if key_points_files:
        print("\nSelect a key points file to incorporate:")
        selected_key_points = user_select_file(key_points_files, 'key points')
        key_points_path = os.path.join(output_key_points_dir, selected_key_points) if selected_key_points else None
    else:
        print("No key points files found.")
        key_points_path = None

    summary_name = input("Enter a name for the summary file: ")

    merge_tool.process_files(selected_files, summary_name, key_points_path)

def create_handbook():
    handbook_creator = HandbookCreator()
    handbook_creator.process_files()

def create_handbook_with_db():
    try:
        db = DatabaseHandler()
        db.connect()
        db.create_tables()

        # Get list of files in output directories
        audio_files = get_file_list(output_audio_dir, '.txt')
        ocr_files = get_file_list(output_ocr_dir, '.txt')

        # User selection of files
        print("\nSelect audio transcript files to include:")
        selected_audio = user_select_multiple_files(audio_files, 'audio transcript')
        print("\nSelect OCR transcript files to include:")
        selected_ocr = user_select_multiple_files(ocr_files, 'OCR transcript')

        # Insert selected files into database
        for file in selected_audio:
            content = db.read_file_content(os.path.join(output_audio_dir, file))
            if content:
                db.insert_data("audio_transcriptions", file, content)
                print(f"Inserted {file} into audio_transcriptions")

        for file in selected_ocr:
            content = db.read_file_content(os.path.join(output_ocr_dir, file))
            if content:
                db.insert_data("handwritten_notes", file, content)
                print(f"Inserted {file} into handwritten_notes")

        # Retrieve all content from database
        all_content = db.retrieve_all_data()

        # Create handbook using all content
        handbook_creator = HandbookCreator()
        final_handbook, tokens_used = handbook_creator.create_handbook(all_content)

        # Save the final handbook
        file_name = input("Enter a name for the handbook file: ")
        handbook_creator.save_handbook(final_handbook, file_name)
        print(f"Handbook created successfully. Tokens used: {tokens_used}")

        # Clear the database
        db.clear_database()
    except Exception as e:
        print(f"An error occurred during handbook creation: {e}")
    finally:
        db.close_connection()

def print_instructions():
    print("\nWebinar Notes Processor - Instructions")
    print("1. Process Transcriptions: Transcribe audio files and perform OCR on images.")
    print("2. Extract Key Points: Analyze audio transcripts to identify key points.")
    print("3. Merge and Summarize: Combine multiple transcripts into a single summary.")
    print("4. Create Handbook: Generate a comprehensive handbook from processed files.")
    print("5. Create Handbook (Database-Assisted): Use a database to handle larger files more efficiently.")
    print("   - This option allows you to select specific files for processing.")
    print("   - It uses a database to manage content, potentially improving performance with large files.")
    print("6. Exit: Close the program.")

def main():
    create_directories()
    while True:
        print("\nWebinar Notes Processor")
        print("1. Process Transcriptions")
        print("2. Extract Key Points from Audio Transcript")
        print("3. Merge and Summarize Files")
        print("4. Create Handbook")
        print("5. Create Handbook (Database-Assisted)")
        print("6. Exit")
        print("7. Show Instructions")

        choice = input("Enter your choice (1-7): ")

        if choice == '1':
            processed_files = process_transcriptions()
            if processed_files:
                print("\nSummary of processed files:")
                for file in processed_files:
                    print(f"- {file}")
            else:
                print("\nNo files were processed.")
        elif choice == '2':
            extract_key_points()
        elif choice == '3':
            merge_files()
        elif choice == '4':
            create_handbook()
        elif choice == '5':
            create_handbook_with_db()
        elif choice == '6':
            print("Exiting the program. Goodbye!")
            break
        elif choice == '7':
            print_instructions()
        else:
            print("Invalid choice. Please try again.")

    logging.info("Exiting the script.")

if __name__ == "__main__":
    main()