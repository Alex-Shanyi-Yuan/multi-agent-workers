from typing import Dict, Any
from .base_agent import BaseAgent
import autogen
import os
import logging

logger = logging.getLogger(__name__)

class PromptAgent(BaseAgent):
    """Agent responsible for interpreting user queries and initiating workflows."""
    
    def __init__(self):
        system_message = """You are a Prompt Engineer Agent responsible for:
        1. Interpreting user queries and understanding their intent
        2. Breaking down complex queries into subtasks
        3. Determining whether a query requires document search or log analysis
        4. Formatting queries appropriately for other agents
        
        You should analyze each query to determine:
        - The primary task type (document search vs log analysis)
        - Required subtasks and their order
        - Specific parameters or constraints mentioned
        """
        
        super().__init__(
            name="PromptEngineer",
            system_message=system_message
        )
        
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process an incoming user query.
        
        Args:
            message: The user's query
            
        Returns:
            Dict containing:
                - task_type: "document_search" or "log_analysis"
                - subtasks: List of subtasks to perform
                - parameters: Any specific parameters mentioned
        """
        # Process the message
        try:
            # Parse the message to determine task type and subtasks
            is_log_related = any(word in message.lower() 
                               for word in ['log', 'error', 'debug', 'trace'])
            
            task_type = "log_analysis" if is_log_related else "document_search"
            
            return {
                "task_type": task_type,
                "original_query": message,
                "parameters": {
                    "priority": "high" if "urgent" in message.lower() else "normal"
                }
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "task_type": "unknown",
                "original_query": message,
                "error": str(e)
            }
        

        
    def format_for_researcher(self, query: str) -> str:
        """Format a query specifically for the Researcher Agent.
        
        Args:
            query: Original user query
            
        Returns:
            str: Formatted query for researcher
        """
        # Add specific formatting for document search
        return f"DOCUMENT_SEARCH: {query}"
        
    def format_for_debugger(self, query: str) -> str:
        """Format a query specifically for the Debug Agent.
        
        Args:
            query: Original user query
            
        Returns:
            str: Formatted query for debugger
        """
        # Add specific formatting for log analysis
        return f"LOG_ANALYSIS: {query}"
