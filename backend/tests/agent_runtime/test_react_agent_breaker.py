import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from unittest.mock import patch

from app.agent_runtime.graph.react_agent import create_react_agent
from app.agent_runtime.tools.base import AgentTool, ToolExecutionError
from app.agent_runtime.types import (
    MAX_CONSECUTIVE_IDENTICAL_TOOL_FAILURES,
    ReactAgentConfig,
    TerminationCondition,
)


class _FailingTool(AgentTool):
    """Tool that always raises ToolExecutionError (e.g. edit miss)."""

    name: str = "edit_note"
    description: str = "always fails"
    access_level: str = "write"

    async def _execute(self, **kwargs) -> str:
        raise ToolExecutionError("未在笔记内容中找到要替换的文本")


def _failing_tool() -> AgentTool:
    return _FailingTool()


def _ai_call(tool_name: str, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {"id": call_id, "name": tool_name, "args": {"title": "x"}, "type": "tool_call"}
        ],
    )


@pytest.mark.asyncio
async def test_react_agent_breaks_same_tool_failure_streak() -> None:
    """Same tool failing N consecutive times ends the turn with a breaker hint.

    Regression: edit_note/edit_world_entry match failures used to loop until
    max_iterations, burning tokens and spamming the UI.
    """
    config = ReactAgentConfig(
        name="writer",
        tools=[_failing_tool()],
        termination=TerminationCondition(mode="no_tool_call"),
    )
    graph = create_react_agent(config)

    # Each LLM turn calls the same failing tool; tool map resolves it and
    # returns the ToolExecutionError payload as an error ToolMessage.
    async def _mock_invoke(*args, **kwargs):
        return _ai_call("edit_note", "call_fail")

    with patch(
        "app.agent_runtime.graph.react_agent._invoke_model",
        side_effect=_mock_invoke,
    ):
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="fix the note")],
                "iteration_count": 0,
                "is_done": False,
                "final_output": None,
            },
            config={"configurable": {"runtime_state": {"session_id": "sess_breaker"}}},
        )

    assert result["is_done"] is True
    # A breaker HumanMessage was injected after the failure streak.
    breaker = [
        m
        for m in result["messages"]
        if isinstance(m, HumanMessage) and "连续失败" in str(m.content)
    ]
    assert breaker, "expected a consecutive-failure breaker hint"
    # final_output records the breaker reason.
    assert result["final_output"] == {
        "error": "consecutive_tool_failures",
        "tool_name": "edit_note",
        "failures": MAX_CONSECUTIVE_IDENTICAL_TOOL_FAILURES,
    }
    # The error ToolMessages are present in history.
    error_tools = [
        m
        for m in result["messages"]
        if isinstance(m, ToolMessage) and "未在笔记内容中找到" in str(m.content)
    ]
    assert len(error_tools) >= MAX_CONSECUTIVE_IDENTICAL_TOOL_FAILURES
