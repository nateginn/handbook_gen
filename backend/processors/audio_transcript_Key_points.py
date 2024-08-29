import os
import requests
from typing import List, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv()

class AudioTranscriptKeyPoints:
    def __init__(self):
        self.input_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_files_audio"
        self.output_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\output_key_points"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_base = "https://api.groq.com/openai/v1"
        self.groq_model = "llama-3.1-70b-versatile"
        
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.gpt_model = "gpt-4o-mini"

        self.use_groq = True  # Set to False to use GPT-4o mini
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

    def generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.2) -> str:
        if self.use_groq:
            return self.groq_generate(prompt, max_tokens, temperature)
        else:
            return self.gpt_generate(prompt, max_tokens, temperature)

    def groq_generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.2) -> str:
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

    def extract_key_points(self, transcript: str) -> Tuple[str, int]:
        prompt = f"""Please analyze the following audio transcript and extract key points with their corresponding direct quotes. 
        Follow these guidelines:
        1. First, review the entire transcript to understand the context and main themes.
        2. Then, go through the transcript line by line and identify key points related to personal injury case management.
        3. For each key point, provide a brief description followed by extensive quotes from the transcript that support or elaborate on that point.
        4. Include more content directly from the transcript, providing context and detailed explanations for each key point.
        5. Focus on content related to personal injury case management, legal considerations, and best practices.
        6. Use the exact language from the transcript for quotes. Do not summarize or paraphrase.
        7. Organize the key points under relevant headings or categories.
        8. Include any important definitions, examples, or case studies mentioned in the transcript, with full context and explanation.
        9. If there's a Q&A section, include relevant questions and answers as separate key points, providing full context and detailed responses.
        10. Do not add any information that is not explicitly stated in the transcript.
        11. Aim to be comprehensive and verbose, capturing as much relevant information as possible from the transcript.
        12. For each quote, provide additional context from the transcript to explain its significance, relevance, or implications. This context should help readers understand the full meaning and importance of each quote within the larger discussion.

        Audio Transcript:
        {transcript}

        Please provide the extracted key points with their corresponding extensive quotes:"""

        response = self.generate(prompt, max_tokens=7500, temperature=0.2)
        tokens_used = self.count_tokens(prompt) + self.count_tokens(response)
        return response, tokens_used

    def get_file_list(self) -> List[str]:
        return [f for f in os.listdir(self.input_dir) if f.endswith('.txt')]

    def user_select_file(self, file_list: List[str]) -> str:
        print("\nAvailable audio transcript files:")
        for idx, file in enumerate(file_list, 1):
            print(f"{idx}. {file}")
        while True:
            choice = input("Enter the number of the file you want to process: ")
            if choice.isdigit() and 0 < int(choice) <= len(file_list):
                return file_list[int(choice) - 1]
            print("Invalid choice. Please try again.")

    def save_output(self, content: str, input_file_name: str) -> str:
        day = input_file_name.split('Day_')[1].split('.')[0]
        output_file_name = f"Day_{day}_key_points.txt"
        file_path = os.path.join(self.output_dir, output_file_name)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Key points saved to: {file_path}")
        return file_path

    def process_file(self) -> str:
        file_list = self.get_file_list()
        if not file_list:
            print("No audio transcript files found in the input directory.")
            return ""

        selected_file = self.user_select_file(file_list)
        file_path = os.path.join(self.input_dir, selected_file)
        transcript = self.get_file_content(file_path)

        if not transcript:
            print(f"Error: Unable to read the content of {selected_file}")
            return ""

        key_points, tokens_used = self.extract_key_points(transcript)
        output_content = f"{key_points}\n\nTokens used: {tokens_used}"
        return self.save_output(output_content, selected_file)