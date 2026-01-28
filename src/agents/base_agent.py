"""Base agent class for Supply Chain Intel agents."""

import os
from abc import ABC, abstractmethod
from typing import Any, Optional

import anthropic

from ..utils.config_loader import ConfigLoader


class BaseAgent(ABC):
    """Base class for all Supply Chain Intel agents."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        self.config_loader = config_loader or ConfigLoader()
        self.api_config = self.config_loader.get_api_config()
        self.client = anthropic.Anthropic()

    def _call_claude(
        self,
        system_prompt: str,
        user_message: str,
        tools: Optional[list[dict]] = None,
        max_tokens: Optional[int] = None
    ) -> anthropic.types.Message:
        """Make a call to Claude API with optional tool use."""
        kwargs: dict[str, Any] = {
            "model": self.api_config["model"],
            "max_tokens": max_tokens or self.api_config["max_tokens"],
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }

        if tools:
            kwargs["tools"] = tools

        return self.client.messages.create(**kwargs)

    def _call_claude_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict],
        max_iterations: int = 10
    ) -> tuple[str, list[dict]]:
        """
        Call Claude with tools, handling the tool use loop.
        Returns the final text response and list of tool results.
        """
        messages = [{"role": "user", "content": user_message}]
        tool_results = []

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.api_config["model"],
                max_tokens=self.api_config["max_tokens"],
                system=system_prompt,
                messages=messages,
                tools=tools
            )

            # Process response
            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            # Check if we need to handle tool use
            tool_use_blocks = [b for b in assistant_content if b.type == "tool_use"]

            if not tool_use_blocks:
                # No more tool use, extract final text
                text_blocks = [b.text for b in assistant_content if b.type == "text"]
                return "\n".join(text_blocks), tool_results

            # Process tool calls
            tool_result_content = []
            for tool_use in tool_use_blocks:
                result = self._handle_tool_call(tool_use.name, tool_use.input)
                tool_results.append({
                    "tool": tool_use.name,
                    "input": tool_use.input,
                    "result": result
                })
                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result
                })

            messages.append({"role": "user", "content": tool_result_content})

        # If we hit max iterations, return what we have
        text_blocks = [b.text for b in assistant_content if b.type == "text"]
        return "\n".join(text_blocks), tool_results

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Handle a tool call. Override in subclasses for custom tools."""
        return f"Tool {tool_name} not implemented"

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Run the agent. Must be implemented by subclasses."""
        pass
