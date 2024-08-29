# crew.py

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Import custom tools
from tools.whisper_tool import WhisperTool
from tools.ocr_tool import OCRTool
from tools.merge_tool import MergeTool

# Load environment variables
load_dotenv()

# Configure the ChatOpenAI to use Groq
groq_llm = ChatOpenAI(
    model_name=os.getenv("OPENAI_MODEL_NAME", "llama-3.1-8b-instant"),
    openai_api_key=os.getenv("GROQ_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.groq.com/openai/v1")
)

# Initialize tools
whisper_tool = WhisperTool()
ocr_tool = OCRTool()
merge_tool = MergeTool()

# Initialize agents
whisper_transcriber = Agent(
    role='Audio Transcriber',
    goal='Accurately transcribe an audio file into text, identifying and differentiating between different speakers.',
    backstory='You are a highly skilled transcriber with expertise in audio analysis.',
    tools=[whisper_tool.transcribe_audio],
    llm=groq_llm
)

ocr_transcriber = Agent(
    role='Handwritten Notes Transcriber',
    goal='Convert handwritten notes into clear and accurate text.',
    backstory='With years of experience in optical character recognition, you excel at deciphering handwritten notes.',
    tools=[ocr_tool.transcribe_handwritten_notes],
    llm=groq_llm
)

report_merger = Agent(
    role='Report Merger and Summarizer',
    goal='Merge transcripts from audio and handwritten notes into a single comprehensive report.',
    backstory='A synthesis expert, you bring together various pieces of information to create coherent and insightful reports.',
    tools=[merge_tool.merge_and_summarize],
    llm=groq_llm
)

# Initialize tasks
audio_transcription_task = Task(
    description='Transcribe the provided audio file into a text script, identifying each speaker. Save the transcription to a file.',
    expected_output='A message confirming where the transcription was saved and the transcription text.',
    agent=whisper_transcriber,
)

ocr_transcription_task = Task(
    description='Convert the provided handwritten notes into clear and readable text.',
    expected_output='A text file containing the transcribed handwritten notes.',
    agent=ocr_transcriber,
)

report_merging_task = Task(
    description='Merge the transcripts from the audio and handwritten notes into a comprehensive report, summarizing key points.',
    expected_output='A single document combining the transcriptions with a detailed summary of the major points.',
    agent=report_merger,
)

# Create the crew
crew = Crew(
    agents=[whisper_transcriber, ocr_transcriber, report_merger],
    tasks=[audio_transcription_task, ocr_transcription_task, report_merging_task],
    process=Process.sequential  # Executes tasks sequentially
)