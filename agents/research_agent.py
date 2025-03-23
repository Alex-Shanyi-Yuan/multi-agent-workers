from typing import Dict, Any, List
from .base_agent import BaseAgent
import os
from processors.confluence import ConfluenceProcessor
from processors.pdf_processor import PDFProcessor
from processors.docx_processor import DocxProcessor

class ResearchAgent(BaseAgent):
    """Agent responsible for searching through documents and finding relevant information."""
    
    def __init__(self):
        system_message = """You are a Research Agent responsible for:
        1. Searching through various document sources (Confluence, PDFs, Word docs)
        2. Finding relevant information based on queries
        3. Summarizing and extracting key information
        4. Providing source references for found information
        """
        
        super().__init__(
            name="Researcher",
            system_message=system_message
        )
        
        # Initialize document processors
        self.confluence = ConfluenceProcessor()
        self.pdf_processor = PDFProcessor()
        self.docx_processor = DocxProcessor()
        
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a search query across all document sources.
        
        Args:
            message: The search query and task details
            
        Returns:
            Dict containing search results from all sources
        """
        # Extract PDF content
        try:
            query = message.get('query', '')
            pdf_path = query.split('/assets/')[1].split(' ')[0]
            pdf_path = os.path.join('/home/alex-shanyi-yuan/multi-agent-workers/assets', pdf_path)
            
            # Extract text from the PDF
            content = self.pdf_processor.extract_text(pdf_path)
            if not content:
                return {
                    "error": "Could not extract text from PDF"
                }
            
            # Find sections 5 and 9
            sections = {}
            current_section = None
            section_text = ""
            
            for page in content['pages']:
                text = page['text']
                lines = text.split('\n')
                
                for line in lines:
                    if 'Section 5' in line or 'Section 9' in line:
                        if current_section:
                            sections[current_section] = section_text.strip()
                        current_section = line.strip()
                        section_text = ""
                    elif current_section:
                        section_text += line + "\n"
            
            if current_section:
                sections[current_section] = section_text.strip()
            
            return {
                "query": query,
                "sections": sections,
                "summary": "Found sections: " + ", ".join(sections.keys())
            }
            
        except Exception as e:
            return {
                "error": f"Error processing PDF: {str(e)}"
            }
        
    def _search_confluence(self, query: str) -> List[Dict[str, Any]]:
        """Search Confluence pages for relevant information.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant Confluence pages and excerpts
        """
        return self.confluence.search(query)
        
    def _search_pdfs(self, query: str) -> List[Dict[str, Any]]:
        """Search PDF documents for relevant information.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant PDF excerpts
        """
        return self.pdf_processor.search(query)
        
    def _search_docx(self, query: str) -> List[Dict[str, Any]]:
        """Search Word documents for relevant information.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant Word document excerpts
        """
        return self.docx_processor.search(query)
        
    def _rank_results(self, results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Rank and sort results by relevance.
        
        Args:
            results: Dictionary of results from different sources
            
        Returns:
            List of ranked results
        """
        all_results = []
        for source, source_results in results.items():
            for result in source_results:
                result["source_type"] = source
                all_results.append(result)
                
        # Sort by relevance score (assuming each result has a 'score' field)
        return sorted(all_results, key=lambda x: x.get("score", 0), reverse=True)
        
    def _generate_summary(self, ranked_results: List[Dict[str, Any]]) -> str:
        """Generate a summary of the top results.
        
        Args:
            ranked_results: List of ranked search results
            
        Returns:
            str: Summary of top findings
        """
        if not ranked_results:
            return "No relevant results found."
            
        # Take top 3 results for summary
        top_results = ranked_results[:3]
        
        summary = "Top findings:\n\n"
        for i, result in enumerate(top_results, 1):
            summary += f"{i}. From {result['source_type']}: {result.get('title', 'Untitled')}\n"
            summary += f"   Excerpt: {result.get('excerpt', 'No excerpt available')}\n\n"
            
        return summary
