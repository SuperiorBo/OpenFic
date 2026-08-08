"""Tests for :mod:`app.models.clients.deepseek_payload`."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.models.clients.deepseek_payload import (
    _EMPTY_REASONING_PLACEHOLDER,
    patch_deepseek_reasoning_payload,
)


def _payload(messages: list) -> dict:
    """Build a payload whose messages mirror the source list (zip-aligned)."""
    roles = {
        SystemMessage: "system",
        HumanMessage: "user",
        AIMessage: "assistant",
        ToolMessage: "tool",
    }
    return {
        "messages": [
            {"role": roles.get(type(m), "user"), "content": m.content or ""}
            for m in messages
        ]
    }


def test_preserves_existing_reasoning_content() -> None:
    src = [
        HumanMessage(content="hi"),
        AIMessage(
            content="",
            additional_kwargs={"reasoning_content": "thinking..."},
            tool_calls=[{"name": "f", "args": {}, "id": "c1", "type": "tool_call"}],
        ),
    ]
    payload = _payload(src)
    patch_deepseek_reasoning_payload(src, payload)
    assert payload["messages"][1]["reasoning_content"] == "thinking..."


def test_backfills_placeholder_for_assistant_without_reasoning() -> None:
    """Regression: assistant tool-call turn with no reasoning text used to
    trigger 'reasoning_content must be passed back' 400 from the gateway."""
    src = [
        HumanMessage(content="do it"),
        AIMessage(
            content="继续写入 READ-05 快照",
            tool_calls=[{"name": "f", "args": {}, "id": "c1", "type": "tool_call"}],
        ),
    ]
    payload = _payload(src)
    patch_deepseek_reasoning_payload(src, payload)
    assert payload["messages"][1]["reasoning_content"] == _EMPTY_REASONING_PLACEHOLDER


def test_does_not_touch_user_tool_or_system_messages() -> None:
    src = [
        SystemMessage(content="sys"),
        HumanMessage(content="hi"),
        AIMessage(content="answer"),
        ToolMessage(content="ok", tool_call_id="c1"),
    ]
    payload = _payload(src)
    patch_deepseek_reasoning_payload(src, payload)
    assert "reasoning_content" not in payload["messages"][0]
    assert "reasoning_content" not in payload["messages"][1]
    # assistant with content but no tool_calls still gets placeholder
    assert payload["messages"][2]["reasoning_content"] == _EMPTY_REASONING_PLACEHOLDER
    assert "reasoning_content" not in payload["messages"][3]


def test_empty_payload_messages_is_noop() -> None:
    src = [HumanMessage(content="hi")]
    payload = {"messages": []}
    patch_deepseek_reasoning_payload(src, payload)
    assert payload["messages"] == []
