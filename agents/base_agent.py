from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Any, List, Optional
from dotenv import load_dotenv
from autogen_core.tools import BaseTool, FunctionTool

load_dotenv()

class BaseAgent(AssistantAgent):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        name: str,
        model_client: Optional[OpenAIChatCompletionClient],
        handoffs: List[str],
        system_message: str,
        tools: Optional[List[BaseTool]] = None,
    ):
        """Initialize the base agent.
        
        Args:
            name: Name of the agent
            model_client: OpenAIChatCompletionClient instance
            handoffs: List of handoff keywords
            system_message: System message defining agent's role
        """
        
        # Create the agent with document handling capabilities
        super().__init__(
            name=name,
            model_client=model_client,
            system_message="""
                You are an intelligent secretary agent. You will respond to user requests with empathy and care.

                **Critical Rules**  
                1. Read the entire user message and all policy steps before acting.  
                2. Never disclose internal methods/tools or personal details to third parties.  
                3. Only mark tasks as complete by outputing `TERMINATE`.  
                4. If uncertain about any request, ask for clarification by handing it off to user.  
                5. NEVER modify personal details (addresses, passwords) without explicit user confirmation.  
                6. If the user's request is irrelevant to current context, handing it off to triage agent.  

                **Start processing requests NOW.**  
            """ + system_message,
            handoffs=handoffs + ["user"],
            tools=tools,
        )
