from dotenv import load_dotenv
from agents import PromptAgent, TriageAgent, ResearchAgent, DebugAgent
import logging
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiAgentSystem:
    """Main class for the multi-agent system."""
    
    def __init__(self):
        """Initialize the multi-agent system with all required agents."""
        # Initialize agents
        self.prompt_agent = PromptAgent()
        self.triage_agent = TriageAgent()
        self.research_agent = ResearchAgent()
        self.debug_agent = DebugAgent()
        
        # Set up agent communication
        self.triage_agent.setup_group_chat({
            "prompt": self.prompt_agent,
            "researcher": self.research_agent,
            "debugger": self.debug_agent
        })
        
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the agent system.
        
        Args:
            query: User's query string
            
        Returns:
            Dict containing the processed results
        """
        try:
            # Step 1: Analyze query with Prompt Agent
            logger.info(f"Analyzing query: {query}")
            analysis = self.prompt_agent.process_message(query)
            
            # Step 2: Triage and delegate to specialized agents
            logger.info(f"Triaging query of type: {analysis['task_type']}")
            results = self.triage_agent.process_message(analysis)
            
            return {
                "query": query,
                "analysis": analysis,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "query": query
            }

def main():
    """Main entry point for the application."""
    # Initialize the system
    system = MultiAgentSystem()
    
    # Example usage
    query = "Find any error logs from last week related to authentication"
    result = system.process_query(query)
    
    # Print results
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nQuery Analysis:")
        print(f"Type: {result['analysis']['task_type']}")
        print("\nResults:")
        print(result['results'])

if __name__ == "__main__":
    main()
