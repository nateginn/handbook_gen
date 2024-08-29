import unittest
import os
from utils.file_utils import ensure_dir, get_file_extension, is_valid_file

class TestUtils(unittest.TestCase):
    def test_ensure_dir(self):
        test_dir = 'test_directory'
        ensure_dir(test_dir)
        self.assertTrue(os.path.exists(test_dir))
        os.rmdir(test_dir)

    def test_get_file_extension(self):
        self.assertEqual(get_file_extension('test.txt'), '.txt')
        self.assertEqual(get_file_extension('test.tar.gz'), '.gz')
        self.assertEqual(get_file_extension('test'), '')

    def test_is_valid_file(self):
        allowed_extensions = {'txt', 'pdf', 'doc'}
        self.assertTrue(is_valid_file('test.txt', allowed_extensions))
        self.assertFalse(is_valid_file('test.jpg', allowed_extensions))
        self.assertFalse(is_valid_file('test', allowed_extensions))

if __name__ == '__main__':
    unittest.main()