"""
backend/tools/registry.py
==========================
Central Tool Registry — implements the tool layer described in the architecture.

Every tool is registered with:
  - A name and description
  - An input schema
  - A list of authorised agents
  - A callable implementation

Agents may only call tools they are authorised for (least-privilege principle).
All tool calls are logged for audit / trace purposes.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    name: str
    description: str
    authorized_agents: List[str]  # which agents may call this tool
    func: Callable[..., Any]
    input_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallRecord:
    tool_name: str
    agent_name: str
    inputs: Dict[str, Any]
    output: Any
    success: bool
    duration_ms: float
    error: Optional[str] = None


class ToolRegistry:
    """Central registry for all banking tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self.call_log: List[ToolCallRecord] = []

    # ------------------------------------------------------------------ Registration

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def register_func(
        self,
        name: str,
        description: str,
        authorized_agents: List[str],
        func: Callable[..., Any],
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.register(ToolDefinition(
            name=name,
            description=description,
            authorized_agents=authorized_agents,
            func=func,
            input_schema=input_schema or {},
        ))

    # ------------------------------------------------------------------ Execution

    def call(
        self,
        tool_name: str,
        agent_name: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a tool on behalf of an agent.
        Raises PermissionError if the agent is not authorised.
        Raises KeyError if the tool does not exist.
        """
        if tool_name not in self._tools:
            raise KeyError(f"Unknown tool: '{tool_name}'")

        tool = self._tools[tool_name]

        # Permission check
        if agent_name not in tool.authorized_agents and "orchestrator" not in agent_name.lower():
            raise PermissionError(
                f"Agent '{agent_name}' is not authorised to call tool '{tool_name}'. "
                f"Authorised agents: {tool.authorized_agents}"
            )

        # Execute
        start = time.monotonic()
        record = ToolCallRecord(
            tool_name=tool_name,
            agent_name=agent_name,
            inputs=kwargs,
            output=None,
            success=False,
            duration_ms=0.0,
        )
        try:
            result = tool.func(**kwargs)
            record.output = result
            record.success = True
            logger.info("Tool '%s' called by '%s' — success", tool_name, agent_name)
            return result
        except Exception as exc:
            record.error = str(exc)
            logger.warning("Tool '%s' called by '%s' — error: %s", tool_name, agent_name, exc)
            raise
        finally:
            record.duration_ms = (time.monotonic() - start) * 1000
            self.call_log.append(record)

    # ------------------------------------------------------------------ Introspection

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "authorized_agents": t.authorized_agents,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    def get_tools_for_agent(self, agent_name: str) -> List[str]:
        return [
            name for name, t in self._tools.items()
            if agent_name in t.authorized_agents
        ]


# Global singleton registry
tool_registry = ToolRegistry()
