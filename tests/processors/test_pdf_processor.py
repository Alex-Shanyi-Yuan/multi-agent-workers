import unittest
from pathlib import Path
import os
import tempfile
from processors.pdf_processor import PDFProcessor
from datetime import datetime

class TestPDFProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_processor = PDFProcessor(cache_dir=self.temp_dir)
        self.assets_dir = Path(__file__).parent.parent.parent / 'assets'
        
    def tearDown(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_search_with_cache(self):
        """Test PDF search with caching"""
        # First search - should extract and cache
        results = self.pdf_processor.search(
            query="test",
            pdf_dir=str(self.assets_dir),
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
        cached_results = self.pdf_processor.search(
            query="test",
            pdf_dir=str(self.assets_dir),
            use_cache=True
        )
        
        # Results should be the same
        self.assertEqual(len(results), len(cached_results))
        
    def test_extract_text(self):
        """Test PDF text extraction"""
        # Find a PDF file in assets
        pdf_files = list(Path(self.assets_dir).glob('**/*.pdf'))
        if pdf_files:
            pdf_path = str(pdf_files[0])
            content = self.pdf_processor.extract_text(pdf_path)
            
            # Verify content structure
            self.assertIsNotNone(content)
            self.assertIn('pages', content)
            self.assertIn('metadata', content)
            self.assertIn('page_count', content)
            
    def test_get_metadata(self):
        """Test PDF metadata extraction"""
        # Find a PDF file in assets
        pdf_files = list(Path(self.assets_dir).glob('**/*.pdf'))
        if pdf_files:
            pdf_path = str(pdf_files[0])
            metadata = self.pdf_processor.get_metadata(pdf_path)
            
            # Verify metadata structure
            self.assertIsNotNone(metadata)
            self.assertIn('page_count', metadata)
            self.assertIn('file_size', metadata)
            self.assertIn('last_modified', metadata)
            
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        # Create some cache entries
        pdf_files = list(Path(self.assets_dir).glob('**/*.pdf'))
        if pdf_files:
            pdf_path = str(pdf_files[0])
            self.pdf_processor.extract_text(pdf_path, use_cache=True)
            
            # Verify cache was created
            cache_files = list(Path(self.temp_dir).glob('*.json'))
            self.assertGreater(len(cache_files), 0)
            
            # Clear cache
            self.pdf_processor.clear_cache()
            
            # Verify cache was cleared
            cache_files = list(Path(self.temp_dir).glob('*.json'))
            self.assertEqual(len(cache_files), 0)
            
    def test_find_matches(self):
        """Test pattern matching in PDF content"""
        import re
        
        # Create test content
        content = {
            "pages": [
                {"page_number": 1, "text": "This is a test document"},
                {"page_number": 2, "text": "Another test page"}
            ]
        }
        
        pattern = re.compile("test", re.IGNORECASE)
        matches = self.pdf_processor._find_matches(content, pattern)
        
        # Verify matches
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["match"], "test")
        self.assertIn("context", matches[0])
        self.assertIn("page_number", matches[0])
        
if __name__ == '__main__':
    unittest.main()
