"""Unit tests for check_mas_core (OpenAI client mocked)."""
import json
import pytest


def _make_fake_response(content: str):
    class Message:
        def __init__(self, c):
            self.content = c
    class Choice:
        def __init__(self, c):
            self.message = Message(c)
    class Response:
        def __init__(self, c):
            self.choices = [Choice(c)]
    return Response(content)


def _fake_client(content: str):
    class Completions:
        def create(self, **kwargs):
            return _make_fake_response(content)
    class Chat:
        completions = Completions()
    class FakeClient:
        chat = Chat()
    return FakeClient()


def test_phi_returns_pass_when_mocked(monkeypatch):
    """phi() returns structure with action when client is mocked."""
    from src import check_mas_core

    monkeypatch.setattr(
        check_mas_core, "get_client",
        lambda: _fake_client(json.dumps({"flagged": False, "action": "PASS", "reasoning": "OK"})),
    )
    result = check_mas_core.phi("claim", "evidence", "argument")
    assert result.get("action") == "PASS"
    assert result.get("flagged") is False


def test_phi_returns_block_when_mocked(monkeypatch):
    """phi() returns BLOCK when mock returns flagged."""
    from src import check_mas_core

    monkeypatch.setattr(
        check_mas_core, "get_client",
        lambda: _fake_client(json.dumps({
            "flagged": True, "action": "BLOCK",
            "detected_fallacies": ["Ad Hominem"], "reasoning": "Attack on source.",
        })),
    )
    result = check_mas_core.phi("claim", "evidence", "Mallory attacks Alice.")
    assert result.get("action") == "BLOCK"
    assert result.get("flagged") is True


def test_phi_handles_invalid_json(monkeypatch):
    """When API returns non-JSON, phi returns PASS and raw reasoning."""
    from src import check_mas_core

    monkeypatch.setattr(check_mas_core, "get_client", lambda: _fake_client("Not valid JSON here"))
    result = check_mas_core.phi("c", "e", "a")
    assert result.get("action") == "PASS"
    assert "reasoning" in result
