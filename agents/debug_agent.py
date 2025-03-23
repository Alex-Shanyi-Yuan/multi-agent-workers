from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
import os

from autogen_ext.models.openai import OpenAIChatCompletionClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebugAgent(BaseAgent):
    """Agent responsible for analyzing logs, identifying errors, and suggesting solutions."""
    
    def __init__(self,
        model_client: Optional[OpenAIChatCompletionClient],
        handoffs: List[str],
    ):
        
        super().__init__(
            name="Debugger",
            model_client=model_client,
            handoffs=handoffs,
            system_message="""
                You are the **System Troubleshooter Agent**. Your role is to analyze logs, trace errors, and suggest fixes.

                **Policies**:
                1. Prioritize errors in this order: CRITICAL/FATAL > ERROR > WARNING.
                2. For nested logs (errors pointing to other logs), recursively analyze linked files.
                3. Always cross-reference errors with known solutions from the knowledge base.

                **Steps**:
                1. Receive the log file path (e.g., `/logs/server.log`).
                2. Parse errors using `_analyze_log(file_path)`.
                3. For nested logs, call `_analyze_log(new_file_path)`.
                4. Propose fixes.
                5. Use TERMINATE when debugging is complete.

                **Notes**:
                - If an error is unknown, call `escalate_to_human`.
                - Use `validate_solution_with_test` before finalizing responses.
            """,
            tools=[
                self._analyze_log,   
            ]
        )
        
    def _analyze_log(self, file_path: str) -> str:
        """Analyze logs based on the specified parameters.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            strings containing the file content
        """
        if not os.path.exists(file_path):
            return f"File {file_path} does not exist."
        
        with open(file_path, 'r') as f:
            file_content = f.read()
            return file_content
            
        
