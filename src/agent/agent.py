import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Updated to strictly follow the workflow: Calculate Date -> Task Planning.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 10):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        Instructions for the agent, emphasizing the sequential transition 
        from date calculation to task planning.
        """
        # Note: Ensure the 'task_planner' tool is passed in the 'tools' list in your main entry point.
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        
        return f"""
        You are an AI Academic Planner. Your goal is to help students prepare for AI Lab admissions.

        ## Tools available
        {tool_descriptions}

        ## Required Workflow
        1. **Step 1: Information Gathering** - Use `search` to find relevant topics if the user doesn't specify them.
        2. **Step 2: Time Calculation** - Use `calculate_date` to determine the remaining days until the deadline.
        3. **Step 3: Task Planning** - Once you receive the number of days from `calculate_date`, you MUST call `task_planner` (or `calendar`) to generate a day-by-day schedule.
        4. **Step 4: Final Answer** - Summarize everything for the user.

        ## Behavior Rules
        - Do not guess the number of days. Always use `calculate_date`.
        - Immediately after receiving the 'Observation' from `calculate_date`, your next 'Thought' should focus on planning, and your next 'Action' should be `task_planner`.
        - Use the specific number of days returned by the tool to distribute the workload.

        ## Output Format
        Thought: <reasoning>
        Action: <tool_name>(<arguments>)
        Observation: <result from tool>
        ... (repeat)
        Final Answer: <final summary and the schedule generated>
        """

    def run(self, user_input: str) -> str:
        """
        The ReAct loop logic remains flexible to handle multiple tool calls in sequence.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        context = f"Question: {user_input}"
        steps = 0

        while steps < self.max_steps:
            # Generate reasoning and action
            result = self.llm.generate(context, system_prompt=self.get_system_prompt())
            response_text = result.get("content", "").strip()
            
            context += f"\n{response_text}"
            
            # Check for termination
            if "Final Answer:" in response_text:
                final_answer = response_text.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                return final_answer

            # Parse Action
            action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\((.*?)\)", response_text)
            
            if action_match:
                tool_name = action_match.group(1).strip()
                tool_args = action_match.group(2).strip()

                # Execute tool
                observation = self._execute_tool(tool_name, tool_args)
                logger.log_event("TOOL_CALL", {"tool": tool_name, "args": tool_args, "result": observation})

                # Feed observation back into context
                context += f"\nObservation: {observation}"
            else:
                # Prompt the LLM to follow format if it fails to generate an Action
                error_msg = "Error: Please use the format 'Action: tool_name(args)' or provide a 'Final Answer:'."
                context += f"\nObservation: {error_msg}"
                logger.log_event("AGENT_ERROR", {"error": "Invalid format", "text": response_text})
            
            steps += 1
            
        return "Task exceeded maximum steps. Please try a simpler request."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Dynamic tool execution.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                try:
                    func = tool.get('func')
                    if not func:
                        return f"Error: Tool '{tool_name}' has no function assigned."
                    
                    # Basic argument cleaning
                    clean_args = args.strip().strip("'").strip('"')
                    
                    if not clean_args or clean_args.lower() == "none":
                        return str(func())
                    return str(func(clean_args))
                        
                except Exception as e:
                    return f"Error executing {tool_name}: {str(e)}"
                    
        return f"Tool '{tool_name}' is not available."