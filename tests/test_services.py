import unittest
from services.transcription_service import TranscriptionService
from services.summarization_service import SummarizationService
from services.handbook_service import HandbookService

class TestServices(unittest.TestCase):
    def test_transcription_service(self):
        result = TranscriptionService.transcribe('test_audio.wav')
        self.assertIsInstance(result, str)

    def test_summarization_service(self):
        test_text = "This is a long text that needs to be summarized. It contains multiple sentences and ideas that should be condensed into a shorter version while retaining the main points."
        result = SummarizationService.summarize(test_text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) < len(test_text))

    def test_handbook_service(self):
        test_summary = "This is a summary of a topic that needs to be expanded into a handbook."
        result = HandbookService.create_handbook(test_summary)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > len(test_summary))

if __name__ == '__main__':
    unittest.main()