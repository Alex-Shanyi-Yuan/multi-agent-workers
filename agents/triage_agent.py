from typing import Dict, Any, List
from .base_agent import BaseAgent
from .prompt_agent import PromptAgent
import autogen
import os
import json

class TriageAgent(BaseAgent):
    """Agent responsible for distributing tasks to specialized agents."""
    
    def __init__(self):
        system_message = """You are a Triage Agent responsible for:
        1. Receiving analyzed queries from the Prompt Engineer
        2. Determining which specialized agents to involve
        3. Coordinating the workflow between agents
        4. Aggregating responses from multiple agents
        """
        
        super().__init__(
            name="Triage",
            system_message=system_message
        )
        
        # Initialize the group chat manager
        self.group_chat = None
        self.agents = {}
        
    def setup_group_chat(self, agents: Dict[str, BaseAgent]):
        """Set up the group chat for agent communication.
        
        Args:
            agents: Dictionary of agent names to agent instances
        """
        self.agents = agents
        
        # Create the group chat
        self.group_chat = autogen.GroupChat(
            agents=[agent.get_agent() for agent in agents.values()],
            messages=[],
            max_round=5,
            speaker_selection_method="round_robin"
        )
        
        # Create the group chat manager
        config_list = [
            {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4")
            }
        ]
        
        # Create a user proxy for interaction
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config={
                "config_list": config_list,
                "temperature": 0.7
            }
        )
        
        # Create the group chat manager
        self.manager = autogen.GroupChatManager(
            groupchat=self.group_chat,
            llm_config={
                "config_list": config_list,
                "temperature": 0.7
            }
        )
        
    def process_message(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Process an analyzed query and distribute to appropriate agents.
        
        Args:
            analysis: Analysis from the Prompt Engineer Agent
            
        Returns:
            Dict containing the aggregated responses from agents
        """
        task_type = analysis["task_type"]
        
        if task_type == "document_search":
            return self._handle_document_search(analysis)
        elif task_type == "log_analysis":
            return self._handle_log_analysis(analysis)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
            
    def _handle_document_search(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document search tasks.
        
        Args:
            analysis: Analysis from the Prompt Engineer
            
        Returns:
            Dict containing search results
        """
        if "researcher" not in self.agents:
            raise ValueError("Researcher agent not initialized")
            
        researcher = self.agents["researcher"]
        query = analysis["original_query"]
        
        # Create initial message with task details
        initial_message = {
            "task": "document_search",
            "query": query,
            "requirements": [
                "Read the specified PDF file",
                "Extract content from section 5",
                "Find information about fuel/energy source"
            ]
        }
        
        # Start the group chat
        response = self.user_proxy.initiate_chat(
            self.group_chat.agents[1],  # Use researcher agent
            message=initial_message
        )
        
        # Get the response
        if response and response.messages:
            last_message = response.messages[-1]['content']
            try:
                result = json.loads(last_message)
                if 'sections' in result:
                    sections = result['sections']
                    fuel_info = []
                    for section, text in sections.items():
                        if any(word in text.lower() for word in ['fuel', 'gas', 'diesel', 'electric']):
                            fuel_info.append(f"In {section}:\n{text}")
                    result = '\n\n'.join(fuel_info) if fuel_info else 'No fuel information found in the specified sections'
            except:
                result = last_message
        else:
            result = 'No response received'
        
        return {
            "task_type": "document_search",
            "results": result
        }
        
    def _handle_log_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle log analysis tasks.
        
        Args:
            analysis: Analysis from the Prompt Engineer
            
        Returns:
            Dict containing analysis results
        """
        if "debugger" not in self.agents:
            raise ValueError("Debug agent not initialized")
            
        debugger = self.agents["debugger"]
        query = analysis["original_query"]
        
        # Start the group chat
        response = self.user_proxy.initiate_chat(
            self.group_chat.agents[2],  # Use debugger agent
            message=f"LOG_ANALYSIS_TASK: {query}"
        )
        
        return {
            "task_type": "log_analysis",
            "results": response.messages[-1]['content'] if response and response.messages else 'No response received'
        }
