import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv()

class MergeTool:
    def __init__(self):
        self.summary_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\summary_files"
        self.output_audio_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_files_audio"
        self.output_ocr_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_txt_files"
        self.output_key_points_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_key_points"
        os.makedirs(self.summary_dir, exist_ok=True)
        
        # GROQ setup
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_base = "https://api.groq.com/openai/v1"
        self.groq_model = "llama-3.1-70b-versatile"
        
        # GPT-4o mini setup
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.gpt_model = "gpt-4o-mini"

        # Set the default LLM to use
        self.use_groq = False  # Set to False to use GPT-4o mini

        # Token counter
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def get_file_content(self, file_path: str) -> str:
        encodings = ['utf-8', 'iso-8859-1', 'windows-1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        print(f"Error: Unable to read file {file_path} with any of the attempted encodings.")
        return ""

    def generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.3) -> str:
        if self.use_groq:
            return self.groq_generate(prompt, max_tokens, temperature)
        else:
            return self.gpt_generate(prompt, max_tokens, temperature)

    def groq_generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.3) -> str:
        url = f"{self.groq_api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"Error in GROQ API call: {response.text}")
            return None

    def gpt_generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.2) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in GPT-4o mini API call: {str(e)}")
            return None

    def enhance_content(self, notes_content: str, audio_content: str) -> str:
        prompt = f"""Enhance the following notes using information from the audio transcript. 
        Follow these guidelines:
        1. First priority - Preserve ALL of the original content from the notes, including ALL text, headings, and structure.
        2. Second priority - from the audio transcript - Add relevant details, explanations, or examples to expand on the existing points. The audio transcript should follow the note closely, look for details missed in the notes that were provided in the audio. Fill in the notes with pertinent detials from the audio.
        3. Incorporate the additional information from the audio transcript directly within the existing note structure, under the relevant sections.
        4. If the audio provides additional important points not in the notes, add them under the most relevant existing section.
        5. Ensure each point is substantive, informative, and directly related to personal injury case management.
        6. Use clear, concise, and professional language.
        7. Do not remove or alter any of the original content from the notes. DO not make up any information.
        8. Add a Q&A section at the end, extracting relevant questions AND answers discussed in the audio transcript. the q&A section is near the end. Ensure both questions and answers are included and are comprehensive.
        9. Aim to provide a robust and detailed summary that captures all important information from both the notes and the audio transcript, this takes priority over the Q&A section. Make sure that every concept in the notes is captured, make sure that every concept in the audio transcript that is relevant is captured. include any summarization provided by the audio transcript before the q&A section.
        10. Final step review the complete document and using the context from the notes combine the information from the audio transcript that is not already present in the notes and combine them in the same concept or content section in the note. Do the same with the Q&A section so that there is congruency and flow from concept to concept.

        Original Notes:
        {notes_content}

        Audio transcript:
        {audio_content}

        Please provide the enhanced content, maintaining the original structure and including ALL original text:"""

        response = self.generate(prompt, max_tokens=7500, temperature=0.2)
        tokens_used = self.count_tokens(prompt) + self.count_tokens(response)
        return response, tokens_used

    def merge_and_summarize(self, file_paths: List[str]) -> str:
        notes_content = ""
        audio_content = ""
        
        for file_path in file_paths:
            content = self.get_file_content(file_path)
            if content:
                if "Notes" in file_path:
                    notes_content += content + "\n\n"
                elif "transcription" in file_path:
                    audio_content += content + "\n\n"
            else:
                print(f"Warning: Skipping file {file_path} due to reading error.")

        if not notes_content or not audio_content:
            print("Error: Missing either notes or audio content.")
            return None

        enhanced_content, tokens_used = self.enhance_content(notes_content, audio_content)
        return enhanced_content, tokens_used

    def incorporate_key_points(self, summary_file_name: str, key_points_file_path: str) -> tuple[str, int]:
        summary_path = os.path.join(self.summary_dir, f"{summary_file_name}.txt")
        summary_content = self.get_file_content(summary_path)
        key_points_content = self.get_file_content(key_points_file_path)

        if not summary_content or not key_points_content:
            print("Error: Unable to read summary or key points file.")
            return None, 0

        prompt = f"""Incorporate the key points and their corresponding quotes into the existing summary. 
        Follow these guidelines:
        1. Maintain the structure and ALL content of the original summary.
        2. For each key point in the key points file, find the most relevant section in the summary.
        3. Insert the key point and its corresponding quote(s) into the appropriate section of the summary.
        4. If a key point doesn't fit into any existing section, add it to the end of the most relevant section.
        5. Ensure that the incorporation of key points enhances and complements the existing content without duplicating information.
        6. Maintain the original formatting and structure of the summary.
        7. Do not remove or significantly alter any of the original summary content.

        Original Summary:
        {summary_content}

        Key Points to Incorporate:
        {key_points_content}

        Please provide the updated summary with incorporated key points:"""

        updated_summary = self.generate(prompt, max_tokens=7500, temperature=0.2)
        tokens_used = self.count_tokens(prompt) + self.count_tokens(updated_summary)
        
        return updated_summary, tokens_used

    def process_files(self, file_paths: List[str], file_name: str, key_points_path: str = None):
        result, tokens_used = self.merge_and_summarize(file_paths)
        if result:
            self.save_output(result, file_name)
            print(f"Initial summary created. Tokens used: {tokens_used}")
            
            if key_points_path:
                updated_summary, additional_tokens = self.incorporate_key_points(file_name, key_points_path)
                if updated_summary:
                    self.save_output(updated_summary, f"{file_name}_with_key_points")
                    print(f"Updated summary with key points created. Additional tokens used: {additional_tokens}")
                else:
                    print("Failed to incorporate key points into summary")
        else:
            print("Failed to generate initial summary")
        
    def save_output(self, content: str, file_name: str):
        file_path = os.path.join(self.summary_dir, f"{file_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Summary saved to: {file_path}")

    def update_summary_with_key_points(self, summary_file_name: str, key_points_path: str):
        updated_summary, tokens_used = self.incorporate_key_points(summary_file_name, key_points_path)
        if updated_summary:
            self.save_output(updated_summary, f"{summary_file_name}_with_key_points")
            print(f"Updated summary with key points created. Additional tokens used: {tokens_used}")
        else:
            print("Failed to incorporate key points into summary")