"""Tests for NoteRef string coercion (model serialization bug)."""

import pytest

from app.agent_runtime.tools.impls.note.refs import NoteRef


def test_note_ref_accepts_dict() -> None:
    ref = NoteRef.model_validate({"title": "全书故事大纲（双主角）"})
    assert ref.title == "全书故事大纲（双主角）"
    assert ref.id is None


def test_note_ref_accepts_json_string() -> None:
    """Regression: model passed note_ref as JSON string."""
    ref = NoteRef.model_validate('{"title": "霸业主线脉络"}')
    assert ref.title == "霸业主线脉络"


def test_note_ref_accepts_json_string_with_id() -> None:
    ref = NoteRef.model_validate('{"id": "H55CWgIfnHVVcxNWirNdL"}')
    assert ref.id == "H55CWgIfnHVVcxNWirNdL"


def test_note_ref_accepts_bare_title_string() -> None:
    ref = NoteRef.model_validate("第一阶段主线大纲")
    assert ref.title == "第一阶段主线大纲"


def test_note_ref_accepts_path_string() -> None:
    ref = NoteRef.model_validate("/剧情大纲/00-系统/DOC总索引")
    assert ref.path == "/剧情大纲/00-系统/DOC总索引"


def test_note_ref_accepts_empty_string_as_noop() -> None:
    ref = NoteRef.model_validate("")
    assert ref.id is None
    assert ref.title is None
    assert ref.path is None
