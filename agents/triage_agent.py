from typing import Dict, Any, List, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from .base_agent import BaseAgent
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TriageAgent(BaseAgent):
    """Agent responsible for distributing tasks to specialized agents."""
    
    def __init__(self,
        model_client: Optional[OpenAIChatCompletionClient],
        handoffs: List[str],
    ):
        system_message = """
            You are the **Workflow Orchestrator Agent**. Your role is to assign tasks to specialized agents.

            **Policies**:
            1. Review the query classification from the Prompt Engineer Agent.
            2. Assign tasks based on type:
            - **Information Query**: Handoff to Researcher Agent, it can read PDF and Word documents.
            - **Log Debug Analysis**: Handoff to Debug Agent.
            3. Never modify or interpret data - only route tasks.

            **Steps**:
            1. Confirm the query type (e.g., "Information Query: Common illness around the time").
            2. Validate that the task matches your policy categories.
            3. Assign to the correct agent using the appropriate function.
            4. Monitor progress and handoff to user when complete.

            **Notes**:
            - If an agent fails twice, reroute the task to another agent.
            - Use `update_task_status` to log all assignments.
        """
        
        super().__init__(
            name="Triage",
            system_message=system_message,
            model_client=model_client,
            handoffs=handoffs,
        )
