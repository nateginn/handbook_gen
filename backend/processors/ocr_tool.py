import base64
from openai import OpenAI
from PIL import Image
import io
import os
import json
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
                {"type": "text", "text": "Please transcribe the text from this image accurately, preserving the structure and layout as much as possible. For each word or phrase, provide a confidence score between 0 and 1. Return the result as a JSON object with 'text' and 'confidence' keys for each segment."},
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

def parse_ocr_result(ocr_result):
    try:
        result_json = json.loads(ocr_result)
        return result_json
    except json.JSONDecodeError:
        # If the result is not in JSON format, we'll create a basic structure
        return {
            "segments": [
                {
                    "text": ocr_result,
                    "confidence": 0.5  # Default confidence if not provided
                }
            ]
        }

def save_to_text_file(content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

def process_image(input_image_path, output_text_path):
    base64_image = compress_image(input_image_path)
    ocr_result = perform_ocr(base64_image)
    parsed_result = parse_ocr_result(ocr_result)
    save_to_text_file(parsed_result, output_text_path)
    print(f"Processed text with confidence scores saved to {output_text_path}")
    return parsed_result

# New function to get segments with low confidence
def get_low_confidence_segments(parsed_result, threshold=0.7):
    low_confidence_segments = []
    for segment in parsed_result.get('segments', []):
        if segment['confidence'] < threshold:
            low_confidence_segments.append(segment)
    return low_confidence_segments

# Example usage
if __name__ == "__main__":
    input_image = "path/to/your/image.jpg"
    output_file = "path/to/your/output.json"
    result = process_image(input_image, output_file)
    
    low_confidence = get_low_confidence_segments(result)
    print("Segments with low confidence:")
    for segment in low_confidence:
        print(f"Text: {segment['text']}, Confidence: {segment['confidence']}")