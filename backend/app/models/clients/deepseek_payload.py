# -*- coding: utf-8 -*-
"""DeepSeek payload helpers."""

from typing import Any, cast

from langchain_core.messages import AIMessage

# DeepSeek thinking mode: assistant messages in a conversation must carry
# `reasoning_content` back to the API. Upstream sometimes returns a tool-call
# turn without any reasoning text (e.g. mechanical "write step N" turns); the
# official gateway then rejects the NEXT request with:
#   The `reasoning_content` in the thinking mode must be passed back to the API.
# A non-empty placeholder (single space) satisfies the contract (verified 200).
_EMPTY_REASONING_PLACEHOLDER = " "


def patch_deepseek_reasoning_payload(input_: Any, payload: dict[str, Any]) -> None:
    """Preserve DeepSeek reasoning content when continuing tool-call messages.

    Also back-fills a placeholder for assistant messages that legitimately had
    no reasoning (mechanical tool turns) so the gateway does not 400 on the
    next round. Only applies to assistant turns, never to user/tool/system.
    """
    if isinstance(input_, list):
        source_messages = input_
    elif hasattr(input_, "to_messages"):
        source_messages = input_.to_messages()
    else:
        return

    payload_messages = payload.get("messages")
    if not isinstance(payload_messages, list):
        return

    for source, target in zip(source_messages, payload_messages, strict=False):
        if not isinstance(source, AIMessage) or not isinstance(target, dict):
            continue
        target = cast(dict[str, Any], target)
        reasoning_content = source.additional_kwargs.get("reasoning_content")
        if reasoning_content:
            target["reasoning_content"] = reasoning_content
        elif source.content or source.tool_calls:
            # Assistant turn without reasoning text — fill a placeholder so
            # the gateway doesn't reject the conversation for missing rc.
            target["reasoning_content"] = _EMPTY_REASONING_PLACEHOLDER
