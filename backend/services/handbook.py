# handbook.py

import os
import tiktoken
from typing import List, Tuple, Optional
from config import Config
from logger import logger
from utils import ensure_dir, get_safe_filename
import requests
from openai import OpenAI
from staging_manager import staging_manager
from cleanup_manager import cleanup_manager

# Uncomment when integrating with database
# from database.db_handler import DatabaseHandler

class HandbookCreator:
    def __init__(self):
        self.summary_dir = os.path.join(Config.BASE_DIR, "summary_files")
        self.handbook_dir = Config.OUTPUT_DIR
        ensure_dir(self.handbook_dir)

        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.llm_choice = None

        # Uncomment when integrating with database
        # self.db_handler = DatabaseHandler()

    def list_llm_options(self):
        return [
            {"name": "Groq", "description": "Fast and cost-effective LLM"},
            {"name": "GPT-4o-mini", "description": "Powerful OpenAI model"},
            {"name": "Local LLM", "description": "Offline model for privacy"}
        ]

    def set_llm(self, choice: str):
        options = {"1": "groq", "2": "gpt", "3": "local"}
        if choice in options:
            self.llm_choice = options[choice]
        else:
            raise ValueError("Invalid LLM choice. Use '1' for Groq, '2' for GPT, or '3' for Local LLM.")

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
        logger.error(f"Unable to read file {file_path} with any of the attempted encodings.")
        return ""

    def generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.3) -> Optional[str]:
        try:
            if self.llm_choice == "groq":
                return self.groq_generate(prompt, max_tokens, temperature)
            elif self.llm_choice == "gpt":
                return self.gpt_generate(prompt, max_tokens, temperature)
            elif self.llm_choice == "local":
                return self.local_generate(prompt, max_tokens, temperature)
            else:
                raise ValueError("LLM not selected. Please use set_llm() to choose an LLM.")
        except Exception as e:
            logger.error(f"Error in generate method: {str(e)}")
            return None

    def groq_generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.3) -> Optional[str]:
        url = f"{Config.GROQ_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": Config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.RequestException as e:
            logger.error(f"Error in GROQ API call: {str(e)}")
            return None

    def gpt_generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.3) -> Optional[str]:
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in GPT API call: {str(e)}")
            return None

    def local_generate(self, prompt: str, max_tokens: int = 7500, temperature: float = 0.3) -> Optional[str]:
        logger.warning("Local LLM generation not yet implemented.")
        return None

    def create_handbook(self, topic: str, summary_contents: List[str]) -> Tuple[Optional[str], int]:
        combined_content = "\n\n".join(summary_contents)
        prompt = f"""Create a comprehensive handbook on {topic} based on the following summary contents. 
        Follow these guidelines:

        1. Structure and Content Organization:
        a. Begin with a table of contents.
        b. Process each key point from the source material in order.
        c. Create main topics based on the key points encountered.
        d. If new information aligns with a previously discussed topic, integrate it into that existing section.
        e. For each main topic:
            - First, provide a concise list of key points in bullet point format.
            - Following the concise section, provide detailed explanations.

        2. Content Coverage:
        a. Include all key concepts, points, and best practices from the provided summaries.
        b. Ensure no important information is omitted; err on the side of including too much rather than too little.
        c. Eliminate redundancies, especially word-for-word repetitions, unless they are confirming quotes.

        3. Formatting:
        a. Use clear headings and subheadings for easy navigation.
        b. In the concise sections, use bullet points for easy scanning.
        c. In the detailed sections, use paragraphs to provide context and explanations.

        4. Language and Examples:
        a. Use clear, professional language suitable for the target audience.
        b. Define any technical terms or acronyms when first used.
        c. Include relevant examples to illustrate complex points in the detailed sections.
        d. Use direct quotes from the summaries to emphasize key points, attributing them properly if possible.

        5. Conclusion:
        Conclude with a summary of key takeaways.

        Remember to maintain a logical flow between topics and ensure that the detailed explanations provide context for the corresponding key points. Treat all source material equally, regardless of when it was added or its order in the input.

        Summary Contents:
        {combined_content}

        Please provide the comprehensive handbook on {topic}:"""

        handbook_content = self.generate(prompt, max_tokens=7500, temperature=0.3)
        tokens_used = self.count_tokens(prompt) + self.count_tokens(handbook_content) if handbook_content else 0
        return handbook_content, tokens_used

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
            try:
                choice = int(choice)
                if 0 < choice <= len(file_list):
                    selected_files.append(file_list[choice - 1])
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        return selected_files

    def save_handbook(self, content: str, file_name: str) -> str:
        safe_file_name = get_safe_filename(file_name)
        file_path = os.path.join(self.handbook_dir, f"{safe_file_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"Handbook saved to: {file_path}")

        # Uncomment when integrating with database
        # try:
        #     topic_id = self.db_handler.get_or_create_topic("Handbooks")
        #     source_id = self.db_handler.add_source(topic_id, "handbook", file_path)
        #     self.db_handler.add_content(source_id, "text", content)
        #     logger.info(f"Handbook saved to database. Source ID: {source_id}")
        # except Exception as e:
        #     logger.error(f"Error saving handbook to database: {str(e)}")

        return file_path

    def interactive_create_handbook(self):
        logger.info("Starting interactive handbook creation process")
        print("Welcome to the Handbook Creator!")

        # LLM Selection
        print("\nAvailable LLM options:")
        for idx, option in enumerate(self.list_llm_options(), 1):
            print(f"{idx}. {option['name']}: {option['description']}")

        while True:
            llm_choice = input("Select an LLM (1-3): ")
            try:
                self.set_llm(llm_choice)
                break
            except ValueError as e:
                print(str(e))

        # Topic Selection
        topic = input("\nEnter the topic for the handbook: ")

        # File Selection
        file_list = self.get_file_list()
        if not file_list:
            logger.warning("No summary files found in the input directory.")
            print("No summary files found in the input directory.")
            return

        selected_files = self.user_select_files(file_list)
        if not selected_files:
            logger.warning("No files selected. Exiting handbook creation.")
            print("No files selected. Exiting handbook creation.")
            return

        # Process Files
        summary_contents = []
        for file in selected_files:
            file_path = os.path.join(self.summary_dir, file)
            content = self.get_file_content(file_path)
            if content:
                summary_contents.append(content)
            else:
                logger.warning(f"Skipping file {file} due to reading error.")
                print(f"Warning: Skipping file {file} due to reading error.")

        if not summary_contents:
            logger.error("No valid summary contents found.")
            print("Error: No valid summary contents found.")
            return

        # Create Handbook
        print("\nGenerating handbook... This may take a few minutes.")
        handbook_content, tokens_used = self.create_handbook(topic, summary_contents)

        if handbook_content:
            print("\nHandbook generated successfully!")
            print(f"Tokens used: {tokens_used}")

            # Display preview
            preview_length = min(500, len(handbook_content))
            print(f"\nPreview of the handbook:\n\n{handbook_content[:preview_length]}...")

            # Save or retry
            while True:
                choice = input("\nDo you want to (S)ave this handbook, (R)etry with a different LLM, or (Q)uit? ").lower()
                if choice == 's':
                    file_name = input("Enter a name for the handbook file: ")
                    self.save_handbook(handbook_content, file_name)
                    print("Handbook saved successfully!")
                    break
                elif choice == 'r':
                    print("Retrying with a different LLM.")
                    self.interactive_create_handbook()
                    return
                elif choice == 'q':
                    print("Quitting without saving.")
                    break
                else:
                    print("Invalid choice. Please enter 'S' to save, 'R' to retry, or 'Q' to quit.")
        else:
            print("Failed to generate handbook content.")

        # Cleanup temporary files
        cleanup_manager.cleanup_temp_files()

def main():
    creator = HandbookCreator()
    creator.interactive_create_handbook()

if __name__ == "__main__":
    main()