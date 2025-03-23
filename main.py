from dotenv import load_dotenv
import logging
from typing import Dict, Any
import os
import time
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.triage_agent import TriageAgent
from agents.research_agent import ResearchAgent
from agents.debug_agent import DebugAgent

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
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        self.triage_agent = TriageAgent(model_client=model_client, handoffs=["Debugger", "Researcher"])
        self.research_agent = ResearchAgent(model_client=model_client, handoffs=["Triage"])
        self.debug_agent = DebugAgent(model_client=model_client, handoffs=["Triage"])

        # Set up agent communication
        termination = TextMentionTermination("TERMINATE")
        self.swarm = Swarm(
            participants=[self.triage_agent, self.research_agent, self.debug_agent], 
            termination_condition=termination
        )
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the agent system.
        
        Args:
            query: User's query string
            
        Returns:
            Dict containing the processed results
        """
        try:
            print("Querying...")
            task_result = await Console(self.swarm.run_stream(task=query))
            last_message = task_result.messages[-1]
            
            # while isinstance(last_message, HandoffMessage) and last_message.target == "user":
            #     user_message = input("User: ")

            #     task_result = await Console(
            #         self.swarm.run_stream(task=HandoffMessage(source="user", target=last_message.source, content=user_message))
            #     )
            #     last_message = task_result.messages[-1]
            
            return last_message.content
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return str(e)

async def main():
    """Main entry point for the application."""
    # Initialize the system
    system = MultiAgentSystem()
    
    # Example usage
    query = "read section 5 of /home/alex-shanyi-yuan/multi-agent-workers/assets/car_user_insturctions.pdf and find information about fuel/energy source"
    result = await system.process_query(query)
    logger.info("Query finished")
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
