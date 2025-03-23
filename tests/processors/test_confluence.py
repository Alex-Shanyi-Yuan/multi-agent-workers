import unittest
from pathlib import Path
import os
import tempfile
from unittest.mock import patch, MagicMock
from processors.confluence import ConfluenceProcessor
from datetime import datetime

class TestConfluenceProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'CONFLUENCE_URL': 'https://example.atlassian.net',
            'CONFLUENCE_USERNAME': 'test@example.com',
            'CONFLUENCE_API_TOKEN': 'test-token'
        })
        self.env_patcher.start()
        
        self.confluence_processor = ConfluenceProcessor(cache_dir=self.temp_dir)
        
    def tearDown(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
        self.env_patcher.stop()
        
    @patch('processors.confluence.Confluence')
    def test_search(self, mock_confluence_class):
        # Setup mock instance
        mock_confluence = MagicMock()
        mock_confluence_class.return_value = mock_confluence
        """Test Confluence search functionality"""
        # Mock search results
        mock_confluence.cql.return_value = {
            'results': [
                {
                    'content': {
                        'id': '12345',
                        'title': 'Test Page',
                        'type': 'page',
                        'space': {'key': 'TEST', 'name': 'Test Space'},
                        '_links': {'webui': '/pages/12345'}
                    },
                    'excerpt': 'This is a test page',
                    'lastModified': '2025-03-22T10:00:00Z',
                    'score': 1.0
                }
            ]
        }
        
        # Perform search
        results = self.confluence_processor.search('test query')
        
        # Verify search was called correctly
        mock_confluence.cql.assert_called_once_with(
            'text ~ "test query" AND status != archived',
            limit=50
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Page')
        
    @patch('processors.confluence.Confluence')
    def test_get_page_content(self, mock_confluence_class):
        # Setup mock instance
        mock_confluence = MagicMock()
        mock_confluence_class.return_value = mock_confluence
        """Test page content retrieval"""
        # Mock page content
        mock_confluence.get_page_by_id.return_value = {
            'id': '12345',
            'title': 'Test Page',
            'space': {'key': 'TEST'},
            'body': {'storage': {'value': 'Test content'}},
            'version': {'number': 1},
            'history': {
                'lastUpdated': {'when': '2025-03-22T10:00:00Z'},
                'createdBy': {'displayName': 'Test User'}
            },
            'metadata': {'labels': [{'name': 'test-label'}]}
        }
        
        # Get page content
        content = self.confluence_processor.get_page_content('12345', use_cache=False)
        
        # Verify content
        self.assertIsNotNone(content)
        self.assertEqual(content['title'], 'Test Page')
        self.assertEqual(content['content'], 'Test content')
        
    @patch('processors.confluence.Confluence')
    def test_get_space_content(self, mock_confluence_class):
        # Setup mock instance
        mock_confluence = MagicMock()
        mock_confluence_class.return_value = mock_confluence
        """Test space content retrieval"""
        # Mock space content
        mock_confluence.get_space_content.return_value = {
            'results': [
                {
                    'content': {
                        'id': '12345',
                        'title': 'Test Page',
                        'type': 'page',
                        'space': {'key': 'TEST', 'name': 'Test Space'},
                        '_links': {'webui': '/pages/12345'}
                    }
                }
            ]
        }
        
        # Get space content
        content = self.confluence_processor.get_space_content('TEST')
        
        # Verify content
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['title'], 'Test Page')
        
    def test_cache_management(self):
        """Test cache management functionality"""
        # Create a mock cached page
        cache_data = {
            'id': '12345',
            'title': 'Test Page',
            'content': 'Test content',
            'cached_at': datetime.now().isoformat()
        }
        
        cache_file = Path(self.temp_dir) / 'page_12345.json'
        import json
        with cache_file.open('w') as f:
            json.dump(cache_data, f)
            
        # Verify cache is valid
        self.assertTrue(self.confluence_processor._is_cache_valid(cache_data))
        
        # Test cache invalidation
        old_cache_data = cache_data.copy()
        old_cache_data['cached_at'] = '2024-03-22T10:00:00Z'
        self.assertFalse(self.confluence_processor._is_cache_valid(old_cache_data))
        
    def test_process_search_result(self):
        """Test search result processing"""
        raw_result = {
            'content': {
                'id': '12345',
                'title': 'Test Page',
                'type': 'page',
                'space': {'key': 'TEST', 'name': 'Test Space'},
                '_links': {'webui': '/pages/12345'}
            },
            'excerpt': 'This is a test page',
            'lastModified': '2025-03-22T10:00:00Z',
            'score': 1.0
        }
        
        processed = self.confluence_processor._process_search_result(raw_result)
        
        self.assertEqual(processed['id'], '12345')
        self.assertEqual(processed['title'], 'Test Page')
        self.assertEqual(processed['space_key'], 'TEST')
        self.assertEqual(processed['excerpt'], 'This is a test page')
        
if __name__ == '__main__':
    unittest.main()
