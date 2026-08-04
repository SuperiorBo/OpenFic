from dataclasses import dataclass
from typing import Literal

from langchain_core.tools import BaseTool

DEFAULT_AGENT_MAX_ITERATIONS = 80
DEFAULT_AGENT_RECURSION_LIMIT = 200
# Subagents (writer/composer/…) should not spin forever on edit failures.
DEFAULT_SUBAGENT_MAX_ITERATIONS = 40
# Same tool returning error this many times in a row ends the ReAct turn.
MAX_CONSECUTIVE_IDENTICAL_TOOL_FAILURES = 3


@dataclass
class TerminationCondition:
    mode: Literal["tool_success", "no_tool_call"]
    tool_name: str | None = None


@dataclass
class ReactAgentConfig:
    name: str
    tools: list[BaseTool]
    termination: TerminationCondition
    max_iterations: int = DEFAULT_AGENT_MAX_ITERATIONS
