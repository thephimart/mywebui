"""Agent orchestrator for handling chat interactions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from mywebui.core.models import BaseChatModel, Message, get_chat_model, get_embedding_model
from mywebui.core.tools import get_tool_registry, ToolResult


@dataclass
class AgentState:
    """Current state of the agent."""
    messages: list[Message] = field(default_factory=list)
    tool_results: dict[str, ToolResult] = field(default_factory=dict)
    iteration_count: int = 0
    max_iterations: int = 3


@dataclass
class AgentResponse:
    """Response from the agent."""
    content: str
    done: bool
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class AgentOrchestrator:
    """Orchestrates agent interactions with tools and models."""

    def __init__(
        self,
        max_iterations: int = 3,
        stop_on_repeat: bool = True,
    ):
        self.max_iterations = max_iterations
        self.stop_on_repeat = stop_on_repeat
        self.tool_registry = get_tool_registry()
        self._previous_tool_inputs: set[str] = set()

    async def process_message(
        self,
        user_message: str,
        system_prompt: str | None = None,
        session_context: list[Message] | None = None,
    ) -> AgentResponse:
        """Process a user message and return agent response."""
        
        state = AgentState(max_iterations=self.max_iterations)
        
        messages: list[Message] = []
        
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        
        if session_context:
            messages.extend(session_context)
        
        messages.append(Message(role="user", content=user_message))
        
        tools = self._get_available_tools()
        
        while state.iteration_count < self.max_iterations:
            state.iteration_count += 1
            
            chat_model = get_chat_model("main")
            
            try:
                result = await chat_model.generate(
                    messages,
                    temperature=0.7,
                    tools=tools if state.iteration_count == 1 else None,
                )
            except Exception as e:
                return AgentResponse(
                    content="",
                    done=True,
                    error=f"Model error: {str(e)}",
                )
            
            choice = result.choices[0]
            assistant_message = choice.message
            
            messages.append(assistant_message)
            
            if assistant_message.tool_calls:
                tool_call_results = []
                
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]
                    
                    if isinstance(tool_args, str):
                        tool_args = eval(tool_args)
                    
                    input_key = f"{tool_name}:{str(tool_args)}"
                    
                    if self.stop_on_repeat and input_key in self._previous_tool_inputs:
                        break
                    
                    self._previous_tool_inputs.add(input_key)
                    
                    tool_result = await self.tool_registry.execute(
                        tool_name,
                        **tool_args,
                    )
                    
                    tool_result_message = Message(
                        role="tool",
                        content=json.dumps({
                            "success": tool_result.success,
                            "output": tool_result.output,
                            "error": tool_result.error,
                        }),
                        tool_call_id=tool_call["id"],
                    )
                    
                    messages.append(tool_result_message)
                    tool_call_results.append({
                        "tool": tool_name,
                        "result": tool_result,
                    })
                
                if tool_call_results:
                    continue
            
            if choice.finish_reason == "stop":
                return AgentResponse(
                    content=assistant_message.content,
                    done=True,
                )
            
            return AgentResponse(
                content=assistant_message.content,
                done=False,
            )
        
        return AgentResponse(
            content=messages[-1].content if messages else "",
            done=True,
            error=f"Max iterations ({self.max_iterations}) reached",
        )

    def _get_available_tools(self) -> list[dict[str, Any]]:
        """Get available tools in OpenAI function calling format."""
        tools = []
        
        for tool in self.tool_registry.list_tools():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            })
        
        return tools

    def reset(self):
        """Reset the agent state."""
        self._previous_tool_inputs.clear()


import json
