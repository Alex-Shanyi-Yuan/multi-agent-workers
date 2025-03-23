import unittest
from pathlib import Path
import os
import tempfile
from processors.docx_processor import DocxProcessor
from datetime import datetime

class TestDocxProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.docx_processor = DocxProcessor(cache_dir=self.temp_dir)
        self.assets_dir = Path(__file__).parent.parent.parent / 'assets'
        
    def tearDown(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_search_with_cache(self):
        """Test Word document search with caching"""
        # First search - should extract and cache
        results = self.docx_processor.search(
            query="test",
            docx_dir=str(self.assets_dir),
            use_cache=True
        )
        
        # Verify results structure
        if results:
            result = results[0]
            self.assertIn('file_path', result)
            self.assertIn('title', result)
            self.assertIn('matches', result)
            self.assertIn('metadata', result)
            
        # Second search - should use cache
        cached_results = self.docx_processor.search(
            query="test",
            docx_dir=str(self.assets_dir),
            use_cache=True
        )
        
        # Results should be the same
        self.assertEqual(len(results), len(cached_results))
        
    def test_extract_text(self):
        """Test Word document text extraction"""
        # Find a Word document in assets
        docx_files = list(Path(self.assets_dir).glob('**/*.docx'))
        if docx_files:
            docx_path = str(docx_files[0])
            content = self.docx_processor.extract_text(docx_path)
            
            # Verify content structure
            self.assertIsNotNone(content)
            self.assertIn('paragraphs', content)
            self.assertIn('metadata', content)
            self.assertIn('paragraph_count', content)
            
    def test_get_metadata(self):
        """Test Word document metadata extraction"""
        # Find a Word document in assets
        docx_files = list(Path(self.assets_dir).glob('**/*.docx'))
        if docx_files:
            docx_path = str(docx_files[0])
            metadata = self.docx_processor.get_metadata(docx_path)
            
            # Verify metadata structure
            self.assertIsNotNone(metadata)
            self.assertIn('core_properties', metadata)
            self.assertIn('paragraph_count', metadata)
            self.assertIn('file_size', metadata)
            
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        # Create some cache entries
        docx_files = list(Path(self.assets_dir).glob('**/*.docx'))
        if docx_files:
            docx_path = str(docx_files[0])
            self.docx_processor.extract_text(docx_path, use_cache=True)
            
            # Verify cache was created
            cache_files = list(Path(self.temp_dir).glob('*.json'))
            self.assertGreater(len(cache_files), 0)
            
            # Clear cache
            self.docx_processor.clear_cache()
            
            # Verify cache was cleared
            cache_files = list(Path(self.temp_dir).glob('*.json'))
            self.assertEqual(len(cache_files), 0)
            
    def test_find_matches(self):
        """Test pattern matching in Word document content"""
        import re
        
        # Create test content
        content = {
            "paragraphs": [
                {
                    "index": 0,
                    "text": "This is a test document",
                    "style": "Normal",
                    "level": None
                },
                {
                    "index": 1,
                    "text": "Another test paragraph",
                    "style": "Heading 1",
                    "level": "1"
                }
            ]
        }
        
        pattern = re.compile("test", re.IGNORECASE)
        matches = self.docx_processor._find_matches(content, pattern)
        
        # Verify matches
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["match"], "test")
        self.assertIn("context", matches[0])
        self.assertIn("paragraph_index", matches[0])
        self.assertIn("style", matches[0])
        
    def test_style_preservation(self):
        """Test preservation of document styles"""
        docx_files = list(Path(self.assets_dir).glob('**/*.docx'))
        if docx_files:
            docx_path = str(docx_files[0])
            content = self.docx_processor.extract_text(docx_path)
            
            if content and content['paragraphs']:
                para = content['paragraphs'][0]
                self.assertIn('style', para)
                self.assertIn('level', para)
                
if __name__ == '__main__':
    unittest.main()
