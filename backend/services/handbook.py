import os
import tiktoken
from typing import List, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()

class HandbookCreator:
    def __init__(self):
        self.summary_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\summary_files"
        self.handbook_dir = r"C:\Users\nginn\SE Programs\PYTHON\Note_Crew\handbook_files"
        os.makedirs(self.handbook_dir, exist_ok=True)

        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_base = "https://api.groq.com/openai/v1"
        self.groq_model = "llama-3.1-70b-versatile"

        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.gpt_model = "gpt-4o-mini"

        self.use_groq = False
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

    def gpt_generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.3) -> str:
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

    def create_handbook(self, content: List[str]) -> Tuple[str, int]:
        combined_content = "\n\n".join(content)
        prompt = f"""Create a comprehensive "How to" Handbook for personal injury case management based on the following content. 
        Follow these guidelines:

        1. Structure and Content Organization:
        a. Begin with a detailed table of contents.
        b. Create main topics based on the key points in the content.
        c. For each main topic:
            - Provide a concise list of do's and don'ts in bullet point format.
            - Following the concise section, provide detailed explanations with examples and quotes if available.

        2. Content Coverage:
        a. Include all key concepts, points, and best practices from the provided content.
        b. Ensure no important information is omitted; err on the side of including too much rather than too little.
        c. Use direct quotes from the content to emphasize key points, attributing them properly.

        3. Formatting:
        a. Use clear headings and subheadings for easy navigation.
        b. In the concise sections, use bullet points for easy scanning.
        c. In the detailed sections, use paragraphs to provide context and explanations.

        4. Additional Sections:
        a. Include a Q&A section at the end, extracting and answering important questions from the content.
        b. Conclude with a summary of key takeaways.

        5. Specific Topics to Cover:
        a. Personal Injury Case Busters (e.g., gaps in care, social media considerations)
        b. Documentation Best Practices
        c. Treatment Approaches and Plans
        d. Multidisciplinary Care
        e. Coordination with Other Healthcare Providers
        f. Managing Pre-existing Conditions
        g. Legal Considerations and Insurance Nuances

        Content:
        {combined_content}

        Please provide the comprehensive "How to" Handbook:"""

        handbook_content = self.generate(prompt, max_tokens=7500, temperature=0.3)
        tokens_used = self.count_tokens(prompt) + self.count_tokens(handbook_content)
        return handbook_content, tokens_used

    def save_handbook(self, content: str, file_name: str) -> str:
        file_path = os.path.join(self.handbook_dir, f"{file_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Handbook saved to: {file_path}")
        return file_path

    def get_file_list(self) -> List[str]:
        return [f for f in os.listdir(self.summary_dir) if f.endswith('.txt')]

    def user_select_files(self, file_list: List[str]) -> List[str]:
        selected_files = []
        print("\nAvailable summary files:")
        for idx, file in enumerate(file_list, 1):
            print(f"{idx}. {file}")
        while True:
            choice = input("Enter the number of a file to include (or 0 to finish): ")
            if choice == '0':
                break
            if choice.isdigit() and 0 < int(choice) <= len(file_list):
                selected_files.append(file_list[int(choice) - 1])
            else:
                print("Invalid choice. Please try again.")
        return selected_files

    def process_files(self):
        file_list = self.get_file_list()
        if not file_list:
            print("No summary files found in the input directory.")
            return

        selected_files = self.user_select_files(file_list)
        if not selected_files:
            print("No files selected. Exiting handbook creation.")
            return

        summary_contents = []
        for file in selected_files:
            file_path = os.path.join(self.summary_dir, file)
            content = self.get_file_content(file_path)
            if content:
                summary_contents.append(content)
            else:
                print(f"Warning: Skipping file {file} due to reading error.")

        if not summary_contents:
            print("Error: No valid summary contents found.")
            return

        handbook_content, tokens_used = self.create_handbook(summary_contents)
        if handbook_content:
            file_name = input("Enter a name for the handbook file: ")
            self.save_handbook(handbook_content, file_name)
            print(f"Handbook created successfully. Tokens used: {tokens_used}")
        else:
            print("Failed to generate handbook content.")

if __name__ == "__main__":
    handbook_creator = HandbookCreator()
    handbook_creator.process_files()