import os
import logging
from typing import Dict, List, Any, Optional
from atlassian import Confluence
from dotenv import load_dotenv
import json
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm

load_dotenv()
logger = logging.getLogger(__name__)

class ConfluenceProcessor:
    """Processor for searching and retrieving Confluence content."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the Confluence processor.
        
        Args:
            cache_dir: Directory for caching Confluence content
        """
        self.confluence_url = os.getenv('CONFLUENCE_URL')
        self.username = os.getenv('CONFLUENCE_USERNAME')
        self.api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if not all([self.confluence_url, self.username, self.api_token]):
            raise ValueError("Missing required Confluence credentials in environment variables")
            
        self.confluence = Confluence(
            url=self.confluence_url,
            username=self.username,
            password=self.api_token,
            cloud=True  # Set to False for server installation
        )
        
        # Setup caching
        self.cache_dir = cache_dir or os.getenv('DOCUMENT_CACHE_DIR', './cache/confluence')
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Cache for space and page metadata
        self.space_cache = {}
        self.page_cache = {}
        
    def search(
        self,
        query: str,
        spaces: Optional[List[str]] = None,
        max_results: int = 50,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """Search Confluence content.
        
        Args:
            query: Search query
            spaces: List of space keys to search in
            max_results: Maximum number of results to return
            include_archived: Whether to include archived content
            
        Returns:
            List of search results with metadata
        """
        try:
            # Prepare CQL query
            cql = f'text ~ "{query}"'
            if spaces:
                space_clause = ' OR '.join(f'space = "{space}"' for space in spaces)
                cql += f' AND ({space_clause})'
            if not include_archived:
                cql += ' AND status != archived'
                
            # Search using CQL
            try:
                results = self.confluence.cql(cql, limit=max_results)
                
                # Process and enrich results
                processed_results = []
                for result in results.get('results', []):
                    processed_result = self._process_search_result(result)
                    if processed_result:
                        processed_results.append(processed_result)
                        
                return processed_results
            except Exception as e:
                logger.error(f"Error searching Confluence: {str(e)}")
                return []
        except Exception as e:
            logger.error(f"Error searching Confluence: {str(e)}")
            return []
            
    def get_page_content(
        self,
        page_id: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get detailed content of a Confluence page.
        
        Args:
            page_id: ID of the page to retrieve
            use_cache: Whether to use cached content
            
        Returns:
            Dict containing page content and metadata
        """
        cache_file = Path(self.cache_dir) / f"page_{page_id}.json"
        
        # Check cache first
        if use_cache and cache_file.exists():
            try:
                with cache_file.open('r') as f:
                    cached_data = json.load(f)
                if self._is_cache_valid(cached_data):
                    return cached_data
            except Exception as e:
                logger.warning(f"Error reading cache for page {page_id}: {str(e)}")
                
        try:
            # Fetch page content
            try:
                page = self.confluence.get_page_by_id(
                    page_id,
                    expand='body.storage,version,space,history,metadata'
                )
                
                if not page:
                    logger.warning(f"Page {page_id} not found")
                    return None
            except Exception as e:
                logger.error(f"Error fetching page {page_id}: {str(e)}")
                return None
                
            # Process and cache the result
            result = {
                "id": page_id,
                "title": page.get('title'),
                "space_key": page.get('space', {}).get('key'),
                "content": page.get('body', {}).get('storage', {}).get('value'),
                "version": page.get('version', {}).get('number'),
                "last_modified": page.get('history', {}).get('lastUpdated', {}).get('when'),
                "creator": page.get('history', {}).get('createdBy', {}).get('displayName'),
                "metadata": page.get('metadata'),
                "cached_at": datetime.now().isoformat()
            }
            
            # Save to cache
            with cache_file.open('w') as f:
                json.dump(result, f)
                
            return result
            
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {str(e)}")
            return None
            
    def _process_search_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a raw Confluence search result.
        
        Args:
            result: Raw search result from Confluence
            
        Returns:
            Dict containing processed result
        """
        try:
            return {
                "id": result.get('content', {}).get('id'),
                "title": result.get('content', {}).get('title'),
                "type": result.get('content', {}).get('type'),
                "space_key": result.get('content', {}).get('space', {}).get('key'),
                "space_name": result.get('content', {}).get('space', {}).get('name'),
                "excerpt": result.get('excerpt'),
                "url": result.get('content', {}).get('_links', {}).get('webui'),
                "last_modified": result.get('lastModified'),
                "score": result.get('score')
            }
        except Exception as e:
            logger.error(f"Error processing search result: {str(e)}")
            return None
            
    def _is_cache_valid(self, cached_data: Dict[str, Any], max_age_hours: int = 24) -> bool:
        """Check if cached data is still valid.
        
        Args:
            cached_data: Cached data to check
            max_age_hours: Maximum age of cache in hours
            
        Returns:
            bool: Whether cache is still valid
        """
        try:
            cached_at = datetime.fromisoformat(cached_data['cached_at'])
            age = datetime.now() - cached_at
            return age < timedelta(hours=max_age_hours)
        except (KeyError, ValueError):
            return False
            
    def clear_cache(self, older_than_hours: Optional[int] = None):
        """Clear the Confluence content cache.
        
        Args:
            older_than_hours: Only clear cache older than this many hours
        """
        try:
            cache_path = Path(self.cache_dir)
            for cache_file in cache_path.glob('*.json'):
                if older_than_hours:
                    # Check file age
                    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_age > timedelta(hours=older_than_hours):
                        cache_file.unlink()
                else:
                    cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            
    def get_space_content(
        self,
        space_key: str,
        content_type: str = 'page',
        expand: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all content from a Confluence space.
        
        Args:
            space_key: Key of the space to get content from
            content_type: Type of content to retrieve (page, blogpost, etc.)
            expand: Whether to expand content details
            
        Returns:
            List of content items in the space
        """
        try:
            content = []
            start = 0
            limit = 50
            
            while True:
                try:
                    results = self.confluence.get_space_content(
                        space_key,
                        content_type=content_type,
                        start=start,
                        limit=limit,
                        expand='body.storage' if expand else None
                    )
                    
                    if not results or not results.get('results'):
                        break
                except Exception as e:
                    logger.error(f"Error getting space content for {space_key}: {str(e)}")
                    break
                    
                content.extend(results['results'])
                if len(results['results']) < limit:
                    break
                    
                start += limit
                
            return [self._process_search_result(item) for item in content if item]
            
        except Exception as e:
            logger.error(f"Error getting space content for {space_key}: {str(e)}")
            return []
