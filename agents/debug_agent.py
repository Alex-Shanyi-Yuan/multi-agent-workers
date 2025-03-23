from typing import Dict, Any, List
from .base_agent import BaseAgent
from processors.log_analyzer import LogAnalyzer
import os

class DebugAgent(BaseAgent):
    """Agent responsible for analyzing logs, identifying errors, and suggesting solutions."""
    
    def __init__(self):
        system_message = """You are a Debug Agent responsible for:
        1. Analyzing log files to identify errors and issues
        2. Tracing through nested log entries
        3. Identifying patterns in errors
        4. Suggesting potential solutions
        5. Providing context for identified issues
        """
        
        super().__init__(
            name="Debugger",
            system_message=system_message
        )
        
        self.log_analyzer = LogAnalyzer()
        self.max_depth = int(os.getenv("MAX_LOG_DEPTH", "5"))
        
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process a log analysis request.
        
        Args:
            message: The analysis request
            
        Returns:
            Dict containing analysis results and suggestions
        """
        # Parse the analysis request
        analysis_params = self._parse_request(message)
        
        # Analyze logs
        log_analysis = self._analyze_logs(analysis_params)
        
        # Generate solutions
        solutions = self._generate_solutions(log_analysis)
        
        return {
            "request": message,
            "analysis": log_analysis,
            "solutions": solutions,
            "summary": self._generate_summary(log_analysis, solutions)
        }
        
    def _parse_request(self, message: str) -> Dict[str, Any]:
        """Parse the analysis request to extract parameters.
        
        Args:
            message: The analysis request
            
        Returns:
            Dict containing analysis parameters
        """
        # Extract time range if specified
        time_range = None
        if "last week" in message.lower():
            time_range = "1w"
        elif "last day" in message.lower():
            time_range = "1d"
        elif "last hour" in message.lower():
            time_range = "1h"
            
        # Extract error types to focus on
        error_focus = []
        if "error" in message.lower():
            error_focus.append("ERROR")
        if "warning" in message.lower():
            error_focus.append("WARN")
            
        return {
            "time_range": time_range,
            "error_focus": error_focus or ["ERROR", "WARN", "INFO"],
            "max_depth": self.max_depth
        }
        
    def _analyze_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze logs based on the specified parameters.
        
        Args:
            params: Analysis parameters
            
        Returns:
            Dict containing analysis results
        """
        return self.log_analyzer.analyze(
            time_range=params["time_range"],
            error_types=params["error_focus"],
            max_depth=params["max_depth"]
        )
        
    def _generate_solutions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate potential solutions for identified issues.
        
        Args:
            analysis: Log analysis results
            
        Returns:
            List of potential solutions
        """
        solutions = []
        
        for error in analysis.get("errors", []):
            solution = {
                "error_type": error["type"],
                "error_message": error["message"],
                "potential_causes": self._identify_causes(error),
                "suggested_actions": self._suggest_actions(error)
            }
            solutions.append(solution)
            
        return solutions
        
    def _identify_causes(self, error: Dict[str, Any]) -> List[str]:
        """Identify potential causes for an error.
        
        Args:
            error: Error information
            
        Returns:
            List of potential causes
        """
        # This would use the agent's knowledge to identify likely causes
        # For now, return a simple example
        return [
            f"Potential cause 1 for {error['type']}",
            f"Potential cause 2 for {error['type']}"
        ]
        
    def _suggest_actions(self, error: Dict[str, Any]) -> List[str]:
        """Suggest actions to resolve an error.
        
        Args:
            error: Error information
            
        Returns:
            List of suggested actions
        """
        # This would use the agent's knowledge to suggest actions
        # For now, return a simple example
        return [
            f"Suggested action 1 for {error['type']}",
            f"Suggested action 2 for {error['type']}"
        ]
        
    def _generate_summary(self, analysis: Dict[str, Any], solutions: List[Dict[str, Any]]) -> str:
        """Generate a summary of the analysis and solutions.
        
        Args:
            analysis: Log analysis results
            solutions: Generated solutions
            
        Returns:
            str: Summary of findings and solutions
        """
        summary = "Log Analysis Summary:\n\n"
        
        # Add error statistics
        summary += "Error Statistics:\n"
        for error_type, count in analysis.get("error_counts", {}).items():
            summary += f"- {error_type}: {count} occurrences\n"
            
        # Add top issues and solutions
        summary += "\nTop Issues and Solutions:\n"
        for solution in solutions[:3]:  # Top 3 issues
            summary += f"\nIssue: {solution['error_message']}\n"
            summary += "Suggested Actions:\n"
            for action in solution['suggested_actions']:
                summary += f"- {action}\n"
                
        return summary
