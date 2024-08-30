# processors/ocr_tool

import base64
import os
import io
import re
from PIL import Image
from openai import OpenAI
from config import Config
from logger import logger
from utils import is_valid_file, get_file_extension
from staging_manager import staging_manager
from cleanup_manager import cleanup_manager

# Uncomment when integrating with database
# from database.db_handler import DatabaseHandler

client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Uncomment when integrating with database
# db_handler = DatabaseHandler()

def process_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if not is_valid_file(image_path, Config.ALLOWED_IMAGE_EXTENSIONS):
        logger.error(f"Invalid image file format: {image_path}")
        raise ValueError(f"Invalid image file format: {image_path}")

    try:
        with Image.open(image_path) as img:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=70)
            compressed_binary_data = buffer.getvalue()
            base64_string = base64.b64encode(compressed_binary_data).decode('utf-8')

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe the text in this image accurately, preserving all formatting and line breaks."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"}}
                ]
            }
        ]

        response = client.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=messages,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        text_match = re.search(r'```(?:txt|text)?\n(.*?)\n```', content, re.DOTALL)
        if text_match:
            text_content = text_match.group(1)
        else:
            text_content = content

        # Stage the OCR result
        staged_path = staging_manager.stage_file(image_path, "ocr", text_content)
        logger.info(f"OCR result staged at: {staged_path}")

        return text_content
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

def user_verify_content(content: str) -> str:
    print("\nOCR Result:")
    print(content)
    print("\nDo you want to make any corrections? (yes/no)")
    if input().lower() == 'yes':
        print("Enter the corrected text (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        return "\n".join(lines)
    return content

def save_to_file(content: str, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Content saved to {output_path}")

    # Uncomment when integrating with database
    # try:
    #     topic_id = db_handler.get_or_create_topic("OCR Results")
    #     source_id = db_handler.add_source(topic_id, "image", output_path)
    #     db_handler.add_content(source_id, "text", content)
    #     logger.info(f"OCR result saved to database. Source ID: {source_id}")
    # except Exception as e:
    #     logger.error(f"Error saving OCR result to database: {str(e)}")

def process_files(file_paths: List[str], output_directory: str):
    for file_path in file_paths:
        logger.info(f"Processing: {file_path}")
        try:
            content = process_image(file_path)
            verified_content = user_verify_content(content)

            # Save to file
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(output_directory, f"{file_name}_ocr.txt")
            save_to_file(verified_content, output_path)

            # Cleanup temporary files
            cleanup_manager.cleanup_temp_files()

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")

def main():
    file_path = input("Enter the path to the image file: ")
    output_directory = input("Enter the output directory: ")
    process_files([file_path], output_directory)

if __name__ == "__main__":
    main()