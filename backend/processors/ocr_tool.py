import base64
from openai import OpenAI
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def compress_image(image_path):
    with Image.open(image_path) as img:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", optimize=True, quality=70)
        compressed_binary_data = buffer.getvalue()
        return base64.b64encode(compressed_binary_data).decode('utf-8')

def perform_ocr(base64_image):
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Please transcribe the text from this image accurately, preserving the structure and layout as much as possible."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1000,
        temperature=0.3
    )

    return response.choices[0].message.content

def save_to_text_file(content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_image(input_image_path, output_text_path):
    base64_image = compress_image(input_image_path)
    ocr_result = perform_ocr(base64_image)
    save_to_text_file(ocr_result, output_text_path)
    print(f"Processed text saved to {output_text_path}")
    return ocr_result