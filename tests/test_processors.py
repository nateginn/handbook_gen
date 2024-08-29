import unittest
from processors.audio_processor import AudioProcessor
from processors.image_processor import ImageProcessor
from processors.youtube_processor import YouTubeProcessor
from processors.text_processor import TextProcessor

class TestProcessors(unittest.TestCase):
    def test_audio_processor(self):
        processor = AudioProcessor()
        result = processor.process('test_audio.wav')
        self.assertIsNotNone(result)

    def test_image_processor(self):
        processor = ImageProcessor()
        result = processor.process('test_image.jpg')
        self.assertIsInstance(result, str)

    def test_youtube_processor(self):
        processor = YouTubeProcessor()
        result = processor.process('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        self.assertTrue(result.endswith('.wav'))

    def test_text_processor(self):
        processor = TextProcessor()
        test_text = "This is a test text."
        result = processor.process(test_text)
        self.assertEqual(result, test_text)

if __name__ == '__main__':
    unittest.main()