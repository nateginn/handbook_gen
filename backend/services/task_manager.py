# backend/services/task_manager.py

import asyncio
import os
from typing import List, Dict, Any, Tuple
from enum import Enum
import wave
import numpy as np
import whisper
from backend.processors.ocr_tool import process_image, get_low_confidence_segments
from backend.database.db_handler import DatabaseHandler
from backend.services.handbook import HandbookCreator

class FileType(Enum):
    AUDIO = 1
    IMAGE = 2
    TEXT = 3
    YOUTUBE = 4

class TaskStatus(Enum):
    PENDING = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    FAILED = 4
    NEEDS_VERIFICATION = 5

class Task:
    def __init__(self, file_path: str, file_type: FileType):
        self.file_path = file_path
        self.file_type = file_type
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.confidence_scores = None
        self.low_confidence_segments = None

class TaskManager:
    def __init__(self, max_files_per_session: int = 5):
        self.max_files_per_session = max_files_per_session
        self.small_queue = asyncio.Queue()
        self.large_queue = asyncio.Queue()
        self.tasks: Dict[str, Task] = {}
        self.is_paused = False
        self.is_cancelled = False
        self.whisper_model = whisper.load_model("base")
        self.db_handler = DatabaseHandler()

    def add_task(self, file_path: str, file_type: FileType):
        if len(self.tasks) >= self.max_files_per_session:
            raise ValueError(f"Maximum number of files ({self.max_files_per_session}) reached for this session.")
        
        task = Task(file_path, file_type)
        self.tasks[file_path] = task

        file_size = os.path.getsize(file_path)
        if file_size <= 15 * 1024 * 1024:  # 15MB
            self.small_queue.put_nowait(task)
        else:
            self.large_queue.put_nowait(task)

    async def process_small_tasks(self):
        while not self.is_cancelled:
            if self.is_paused:
                await asyncio.sleep(1)
                continue

            try:
                task = self.small_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)
                continue

            await self._process_task(task)

    async def process_large_tasks(self):
        while not self.is_cancelled:
            if self.is_paused:
                await asyncio.sleep(1)
                continue

            try:
                task = self.large_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)
                continue

            await self._process_task(task)

    async def _process_task(self, task: Task):
        task.status = TaskStatus.IN_PROGRESS
        try:
            await self.process_file(task)
            if task.file_type == FileType.IMAGE and task.low_confidence_segments:
                task.status = TaskStatus.NEEDS_VERIFICATION
            else:
                task.status = TaskStatus.COMPLETED
            self.db_handler.update_task_status(task.file_path, task.status.value)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.db_handler.update_task_status(task.file_path, task.status.value, error=str(e))

    async def process_file(self, task: Task):
        if task.file_type == FileType.AUDIO:
            task.result = await self.process_audio(task.file_path)
        elif task.file_type == FileType.IMAGE:
            task.result, task.confidence_scores, task.low_confidence_segments = await self.process_image(task.file_path)
        elif task.file_type == FileType.TEXT:
            task.result = await self.process_text(task.file_path)
        elif task.file_type == FileType.YOUTUBE:
            task.result = await self.process_youtube(task.file_path)
        else:
            raise ValueError(f"Unknown file type: {task.file_type}")

        self.db_handler.save_processed_content(task.file_path, task.result, task.confidence_scores, task.low_confidence_segments)

    async def process_audio(self, file_path: str) -> str:
        with wave.open(file_path, 'rb') as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            rms = np.sqrt(np.mean(np.square(audio)))
            if rms < 500:  # Arbitrary threshold, adjust as needed
                print(f"Warning: Audio quality for {file_path} is poor. Results may vary.")

        result = self.whisper_model.transcribe(file_path)
        return result["text"]

    async def process_image(self, file_path: str) -> Tuple[Dict, Dict, List]:
        ocr_result = process_image(file_path, f"{file_path}_ocr_result.json")
        low_confidence_segments = get_low_confidence_segments(ocr_result)
        
        # Extract text and confidence scores
        text = " ".join([segment['text'] for segment in ocr_result.get('segments', [])])
        confidence_scores = {segment['text']: segment['confidence'] for segment in ocr_result.get('segments', [])}
        
        return text, confidence_scores, low_confidence_segments

    async def process_text(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    async def process_youtube(self, url: str) -> str:
        # Placeholder for YouTube processing
        return f"YouTube processing not implemented yet for URL: {url}"

    async def run(self):
        small_task_processor = asyncio.create_task(self.process_small_tasks())
        large_task_processor = asyncio.create_task(self.process_large_tasks())
        await asyncio.gather(small_task_processor, large_task_processor)

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def cancel(self):
        self.is_cancelled = True

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_tasks": len(self.tasks),
            "pending_small": self.small_queue.qsize(),
            "pending_large": self.large_queue.qsize(),
            "completed": sum(1 for task in self.tasks.values() if task.status == TaskStatus.COMPLETED),
            "needs_verification": sum(1 for task in self.tasks.values() if task.status == TaskStatus.NEEDS_VERIFICATION),
            "failed": sum(1 for task in self.tasks.values() if task.status == TaskStatus.FAILED),
            "is_paused": self.is_paused,
            "is_cancelled": self.is_cancelled
        }

    def get_tasks_needing_verification(self) -> List[Task]:
        return [task for task in self.tasks.values() if task.status == TaskStatus.NEEDS_VERIFICATION]

    async def apply_user_verification(self, file_path: str, verified_text: str):
        if file_path not in self.tasks:
            raise ValueError(f"No task found for file: {file_path}")
        
        task = self.tasks[file_path]
        if task.status != TaskStatus.NEEDS_VERIFICATION:
            raise ValueError(f"Task for file {file_path} is not in NEEDS_VERIFICATION status")
        
        task.result = verified_text
        task.status = TaskStatus.COMPLETED
        self.db_handler.update_verified_content(file_path, verified_text)

    async def process_batch(self, file_paths: List[str], file_types: List[FileType]):
        for file_path, file_type in zip(file_paths, file_types):
            self.add_task(file_path, file_type)
        await self.run()
        
    async def create_handbook(self, topic: str):
        handbook_creator = HandbookCreator()
        handbook_creator.set_llm(self.llm_choice)  # You'll need to add this attribute to TaskManager
        
        # Get all completed tasks
        completed_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.COMPLETED]
        
        # Prepare summary contents
        summary_contents = [task.result for task in completed_tasks if task.result]
        
        if not summary_contents:
            print("No completed tasks found to create a handbook.")
            return
        
        handbook_content, tokens_used = handbook_creator.create_handbook(topic, summary_contents)
        
        if handbook_content:
            file_name = f"{topic.replace(' ', '_')}_handbook"
            file_path = handbook_creator.save_handbook(handbook_content, file_name)
            print(f"Handbook created successfully. Saved to: {file_path}")
            print(f"Tokens used: {tokens_used}")
        else:
            print("Failed to generate handbook content.")

# Usage example
async def main():
    manager = TaskManager()
    
    # Add some sample tasks
    manager.add_task("small_file1.wav", FileType.AUDIO)
    manager.add_task("large_file1.wav", FileType.AUDIO)
    manager.add_task("small_file2.jpg", FileType.IMAGE)
    manager.add_task("document.txt", FileType.TEXT)
    
    # Run the task manager
    await manager.run()

    # Print results
    for file_path, task in manager.tasks.items():
        print(f"File: {file_path}")
        print(f"Status: {task.status}")
        print(f"Result: {task.result[:100]}..." if task.result else "No result")
        print(f"Error: {task.error}" if task.error else "No error")
        print(f"Needs Verification: {'Yes' if task.status == TaskStatus.NEEDS_VERIFICATION else 'No'}")
        print()

    # Process tasks needing verification
    tasks_needing_verification = manager.get_tasks_needing_verification()
    for task in tasks_needing_verification:
        # In a real application, this would be handled by a user interface
        verified_text = input(f"Please verify and correct the text for {task.file_path}: ")
        await manager.apply_user_verification(task.file_path, verified_text)

if __name__ == "__main__":
    asyncio.run(main())