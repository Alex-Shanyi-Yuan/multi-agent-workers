import os
import logging
from typing import Dict, List, Any, Optional, Generator
from pathlib import Path
import PyPDF2
import re
from datetime import datetime
import json
from tqdm import tqdm

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Processor for searching and extracting content from PDF files."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the PDF processor.
        
        Args:
            cache_dir: Directory for caching extracted PDF content
        """
        self.cache_dir = cache_dir or os.getenv('DOCUMENT_CACHE_DIR', './cache/pdf')
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        self.max_file_size = int(os.getenv('MAX_PDF_SIZE_MB', '10')) * 1024 * 1024  # Convert to bytes
        
    def search(
        self,
        query: str,
        pdf_dir: str,
        recursive: bool = True,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for text in PDF files.
        
        Args:
            query: Search query
            pdf_dir: Directory containing PDF files
            recursive: Whether to search subdirectories
            use_cache: Whether to use cached content
            
        Returns:
            List of search results with metadata
        """
        results = []
        query_pattern = re.compile(query, re.IGNORECASE)
        
        # Find all PDF files
        pdf_files = self._find_pdf_files(pdf_dir, recursive)
        
        for pdf_file in tqdm(pdf_files, desc="Searching PDFs"):
            try:
                # Check file size
                if os.path.getsize(pdf_file) > self.max_file_size:
                    logger.warning(f"Skipping {pdf_file}: File too large")
                    continue
                    
                # Get content (from cache or by extraction)
                content = self._get_pdf_content(pdf_file, use_cache)
                if not content:
                    continue
                    
                # Search for matches
                matches = self._find_matches(content, query_pattern)
                if matches:
                    results.append({
                        "file_path": str(pdf_file),
                        "title": content.get("title", os.path.basename(pdf_file)),
                        "matches": matches,
                        "metadata": content.get("metadata", {}),
                        "page_count": content.get("page_count", 0)
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                
        return results
        
    def _find_pdf_files(self, directory: str, recursive: bool) -> Generator[Path, None, None]:
        """Find PDF files in directory.
        
        Args:
            directory: Directory to search
            recursive: Whether to search subdirectories
            
        Yields:
            Path objects for PDF files
        """
        directory = Path(directory)
        pattern = '**/*.pdf' if recursive else '*.pdf'
        
        for pdf_file in directory.glob(pattern):
            if pdf_file.is_file():
                yield pdf_file
                
    def _get_pdf_content(
        self,
        pdf_path: Path,
        use_cache: bool
    ) -> Optional[Dict[str, Any]]:
        """Get PDF content, either from cache or by extraction.
        
        Args:
            pdf_path: Path to PDF file
            use_cache: Whether to use cached content
            
        Returns:
            Dict containing PDF content and metadata
        """
        cache_file = Path(self.cache_dir) / f"{pdf_path.stem}_{pdf_path.stat().st_mtime}.json"
        
        # Check cache first
        if use_cache and cache_file.exists():
            try:
                with cache_file.open('r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache for {pdf_path}: {str(e)}")
                
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Extract text and metadata
                content = {
                    "pages": [],
                    "metadata": reader.metadata,
                    "page_count": len(reader.pages),
                    "title": reader.metadata.get('/Title', pdf_path.name),
                    "extracted_at": datetime.now().isoformat()
                }
                
                # Extract text from each page
                for page_num, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        content["pages"].append({
                            "page_number": page_num + 1,
                            "text": text
                        })
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        
                # Cache the content
                with cache_file.open('w') as f:
                    json.dump(content, f)
                    
                return content
                
        except Exception as e:
            logger.error(f"Error extracting content from {pdf_path}: {str(e)}")
            return None
            
    def _find_matches(
        self,
        content: Dict[str, Any],
        pattern: re.Pattern
    ) -> List[Dict[str, Any]]:
        """Find pattern matches in PDF content.
        
        Args:
            content: Extracted PDF content
            pattern: Compiled regex pattern
            
        Returns:
            List of matches with context
        """
        matches = []
        
        for page in content["pages"]:
            page_text = page["text"]
            page_matches = pattern.finditer(page_text)
            
            for match in page_matches:
                # Get context around match
                start = max(0, match.start() - 100)
                end = min(len(page_text), match.end() + 100)
                
                matches.append({
                    "page_number": page["page_number"],
                    "match": match.group(),
                    "context": page_text[start:end],
                    "position": {
                        "start": match.start(),
                        "end": match.end()
                    }
                })
                
        return matches
        
    def extract_text(
        self,
        pdf_path: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Extract all text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            use_cache: Whether to use cached content
            
        Returns:
            Dict containing extracted text and metadata
        """
        return self._get_pdf_content(Path(pdf_path), use_cache)
        
    def clear_cache(self, older_than_days: Optional[int] = None):
        """Clear the PDF content cache.
        
        Args:
            older_than_days: Only clear cache older than this many days
        """
        try:
            cache_path = Path(self.cache_dir)
            for cache_file in cache_path.glob('*.json'):
                if older_than_days:
                    # Check file age
                    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_age.days > older_than_days:
                        cache_file.unlink()
                else:
                    cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            
    def get_metadata(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Get metadata from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict containing PDF metadata
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return {
                    "metadata": reader.metadata,
                    "page_count": len(reader.pages),
                    "file_size": os.path.getsize(pdf_path),
                    "last_modified": datetime.fromtimestamp(
                        os.path.getmtime(pdf_path)
                    ).isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting metadata from {pdf_path}: {str(e)}")
            return None
