"""CHECK-MAS MCP Server — expose the semantic firewall via Model Context Protocol.

This adapter turns CHECK-MAS into an MCP tool server that any MCP-compatible
client can call (Claude Desktop, Cursor, LangChain, CrewAI, etc.).

Usage::

    # Install: pip install checkmas[mcp]
    # Run:     python -m checkmas.adapters.mcp_server
    #   or:    checkmas-mcp   (if installed as console script)

Configuration via environment variables:

    OPENAI_API_KEY   — required for LLM-powered analysis (omit for rule-based)
    CHECKMAS_MODEL   — LLM model name (default: gpt-4o-mini)
    CHECKMAS_PHI     — scoring mode: "graded" (default) or "binary"
"""

from __future__ import annotations

import json
import os
from typing import Any


def _get_firewall():
    """Lazily create a SemanticFirewall from env config."""
    from checkmas import SemanticFirewall

    phi_mode = os.environ.get("CHECKMAS_PHI", "graded")
    api_key = os.environ.get("OPENAI_API_KEY", "")

    provider = None
    if api_key:
        try:
            from checkmas import OpenAIProvider
            model = os.environ.get("CHECKMAS_MODEL", "gpt-4o-mini")
            provider = OpenAIProvider(api_key=api_key, model=model)
        except ImportError:
            pass

    return SemanticFirewall(provider=provider, phi_mode=phi_mode)


def create_mcp_server():
    """Create and return a FastMCP server instance with CHECK-MAS tools.

    Returns
    -------
    FastMCP
        Configured MCP server ready to ``.run()``.

    Raises
    ------
    ImportError
        If ``fastmcp`` / ``mcp`` is not installed.
    """
    try:
        from fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "MCP server requires the mcp package.\n"
            "Install with: pip install checkmas[mcp]"
        ) from None

    mcp = FastMCP(
        "CHECK-MAS",
        description=(
            "Semantic Firewall for Multi-Agent LLM Systems. "
            "Detect manipulation, fallacies, and adversarial agents."
        ),
    )

    _fw = _get_firewall()

    @mcp.tool()
    def check_argument(claim: str, evidence: str, argument: str) -> str:
        """Analyze an agent's argument for logical fallacies and evidence contradictions.

        Args:
            claim: The factual claim being debated.
            evidence: Reference evidence to compare against.
            argument: The agent's argument to inspect.

        Returns:
            JSON with fields: flagged, score, fallacies, action, reasoning.
        """
        result = _fw.check(claim=claim, evidence=evidence, argument=argument)
        return json.dumps({
            "flagged": result.flagged,
            "score": result.score,
            "fallacies": result.fallacies,
            "action": result.action,
            "reasoning": result.reasoning,
        }, indent=2)

    @mcp.tool()
    def check_batch(claim: str, evidence: str, arguments: str) -> str:
        """Analyze multiple agent arguments at once.

        Args:
            claim: The factual claim being debated.
            evidence: Reference evidence to compare against.
            arguments: JSON array of argument strings, one per agent.

        Returns:
            JSON array of results, one per agent.
        """
        try:
            arg_list = json.loads(arguments)
        except json.JSONDecodeError:
            return json.dumps({"error": "arguments must be a valid JSON array of strings"})

        results = _fw.check_batch(claim=claim, evidence=evidence, arguments=arg_list)
        return json.dumps([
            {
                "flagged": r.flagged,
                "score": r.score,
                "fallacies": r.fallacies,
                "action": r.action,
                "reasoning": r.reasoning,
            }
            for r in results
        ], indent=2)

    @mcp.tool()
    def get_fallacy_weights() -> str:
        """Return the current fallacy severity weights used for graded scoring.

        Returns:
            JSON object mapping fallacy names to weights.
        """
        from checkmas import FALLACY_WEIGHTS
        return json.dumps(FALLACY_WEIGHTS, indent=2)

    return mcp


def main() -> None:
    """Entry point for ``python -m checkmas.adapters.mcp_server``."""
    server = create_mcp_server()
    server.run()


if __name__ == "__main__":
    main()
