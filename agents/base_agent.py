from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import autogen
from dotenv import load_dotenv
import os

load_dotenv()

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        name: str,
        system_message: str,
        temperature: float = float(os.getenv("TEMPERATURE", "0.7")),
        model: str = os.getenv("MODEL_NAME", "gpt-4")
    ):
        """Initialize the base agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent's role
            temperature: Temperature for response generation
            model: Model to use for the agent
        """
        self.name = name
        # Load PDF processor
        from processors.pdf_processor import PDFProcessor
        self.pdf_processor = PDFProcessor()
        
        # Configure LLM
        config_list = [
            {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4")
            }
        ]
        
        # Create the agent with document handling capabilities
        self.agent = autogen.AssistantAgent(
            name=name,
            system_message=system_message + "\n\nYou can process documents using the following functions:\n- read_pdf(file_path): Read content from a PDF file\n- extract_section(content, section_number): Extract content from a specific section",
            llm_config={
                "config_list": config_list,
                "temperature": temperature,
                "timeout": 60
            },
            function_map={
                "read_pdf": self.read_pdf,
                "extract_section": self.extract_section
            },
            max_consecutive_auto_reply=1
        )
        
    def read_pdf(self, file_path: str) -> dict:
        """Read content from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            dict: Content from the PDF file
        """
        try:
            content = self.pdf_processor.extract_text(file_path)
            if content:
                return content
            else:
                return {"error": "Failed to read PDF file"}
        except Exception as e:
            return {"error": str(e)}
        
    def extract_section(self, content: dict, section_number: int) -> str:
        """Extract content from a specific section.
        
        Args:
            content: Content from the PDF file
            section_number: Section number to extract
            
        Returns:
            str: Content from the specified section
        """
        try:
            if "error" in content:
                return f"Error: {content['error']}"
                
            section_text = []
            current_section = None
            section_pattern = re.compile(f"^{section_number}[.\s]")
            next_section_pattern = re.compile(f"^{section_number + 1}[.\s]")
            
            for page in content['pages']:
                lines = page['text'].split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if section_pattern.match(line):
                        current_section = line
                        section_text.append(line)
                    elif current_section and next_section_pattern.match(line):
                        break
                    elif current_section:
                        section_text.append(line)
                        
            return '\n'.join(section_text) if section_text else "Section not found"
        except Exception as e:
            return f"Error extracting section: {str(e)}"
        
    @abstractmethod
    def process_message(self, message: str) -> str:
        """Process an incoming message.
        
        Args:
            message: The incoming message to process
            
        Returns:
            str: The response message
        """
        pass
    
    def _format_response(self, response: Any) -> str:
        """Format the response for output.
        
        Args:
            response: The response to format
            
        Returns:
            str: Formatted response
        """
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return str(response)
        else:
            return str(response)
            
    def get_agent(self) -> autogen.AssistantAgent:
        """Get the underlying AutoGen agent.
        
        Returns:
            autogen.AssistantAgent: The AutoGen agent instance
        """
        return self.agent
