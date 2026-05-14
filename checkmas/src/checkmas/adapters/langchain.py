"""CHECK-MAS LangChain adapter — middleware and tool for LangChain / LangGraph.

Provides two integration patterns:

1. **CheckMASMiddleware** — wraps an LLM and filters every response through
   the semantic firewall before passing it downstream.
2. **CheckMASTool** — a LangChain ``BaseTool`` that agents can invoke
   to verify arguments on demand.

Usage::

    # Install: pip install checkmas[langchain]

    # Pattern 1: Middleware
    from checkmas.adapters.langchain import CheckMASMiddleware
    wrapped_llm = CheckMASMiddleware(llm=my_llm, claim=..., evidence=...)

    # Pattern 2: Tool
    from checkmas.adapters.langchain import CheckMASTool
    tool = CheckMASTool()
    result = tool.invoke({"claim": ..., "evidence": ..., "argument": ...})
"""

from __future__ import annotations

from typing import Any

from checkmas.firewall import SemanticFirewall, FirewallResult
from checkmas.providers.base import LLMProvider


class CheckMASTool:
    """LangChain-compatible tool that exposes the CHECK-MAS firewall.

    Can be used as a tool in LangGraph nodes or CrewAI task flows.

    Parameters
    ----------
    provider : LLMProvider, optional
        LLM backend for the firewall.  ``None`` = rule-based fallback.
    phi_mode : str
        ``"graded"`` or ``"binary"``.

    Example::

        tool = CheckMASTool()
        result = tool.invoke({
            "claim": "Earth is flat",
            "evidence": "NASA confirms spherical shape...",
            "argument": "Sources are biased...",
        })
        print(result)  # {"flagged": True, "score": 0.7, ...}
    """

    name: str = "checkmas_firewall"
    description: str = (
        "Analyze an argument for logical fallacies and evidence contradictions. "
        "Input: JSON with keys 'claim', 'evidence', 'argument'. "
        "Output: JSON with keys 'flagged', 'score', 'fallacies', 'action', 'reasoning'."
    )

    def __init__(
        self,
        provider: LLMProvider | None = None,
        phi_mode: str = "graded",
    ) -> None:
        self._fw = SemanticFirewall(provider=provider, phi_mode=phi_mode)

    def invoke(self, input: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Run the firewall check.

        Parameters
        ----------
        input : dict
            Must contain ``claim``, ``evidence``, ``argument`` keys.

        Returns
        -------
        dict
            Firewall result as a plain dictionary.
        """
        result = self._fw.check(
            claim=input["claim"],
            evidence=input["evidence"],
            argument=input["argument"],
        )
        return {
            "flagged": result.flagged,
            "score": result.score,
            "fallacies": result.fallacies,
            "action": result.action,
            "reasoning": result.reasoning,
        }

    def _to_langchain_tool(self):
        """Convert to a native LangChain BaseTool (requires langchain-core).

        Returns
        -------
        langchain_core.tools.BaseTool
        """
        try:
            from langchain_core.tools import StructuredTool
        except ImportError:
            raise ImportError(
                "LangChain integration requires langchain-core.\n"
                "Install with: pip install checkmas[langchain]"
            ) from None

        def _run(claim: str, evidence: str, argument: str) -> str:
            import json
            result = self.invoke({
                "claim": claim,
                "evidence": evidence,
                "argument": argument,
            })
            return json.dumps(result, indent=2)

        return StructuredTool.from_function(
            func=_run,
            name=self.name,
            description=self.description,
        )


def checkmas_node(
    state: dict[str, Any],
    *,
    provider: LLMProvider | None = None,
    phi_mode: str = "graded",
    claim_key: str = "claim",
    evidence_key: str = "evidence",
    messages_key: str = "messages",
) -> dict[str, Any]:
    """LangGraph node that filters agent messages through CHECK-MAS.

    Adds ``checkmas_score`` and ``checkmas_action`` metadata to each message.

    Parameters
    ----------
    state : dict
        LangGraph state dict.  Expected keys: ``claim``, ``evidence``,
        ``messages`` (list of message objects with ``.content`` and ``.metadata``).
    provider : LLMProvider, optional
    phi_mode : str
    claim_key, evidence_key, messages_key : str
        State dict key names (override if your state uses different keys).

    Returns
    -------
    dict
        Updated state with annotated messages.

    Example in LangGraph::

        from checkmas.adapters.langchain import checkmas_node

        graph.add_node("firewall", checkmas_node)
        graph.add_edge("agents", "firewall")
        graph.add_edge("firewall", "decision")
    """
    fw = SemanticFirewall(provider=provider, phi_mode=phi_mode)
    claim = state.get(claim_key, "")
    evidence = state.get(evidence_key, "")
    messages = state.get(messages_key, [])

    for msg in messages:
        content = getattr(msg, "content", str(msg))
        result = fw.check(claim=claim, evidence=evidence, argument=content)
        metadata = getattr(msg, "metadata", {})
        if isinstance(metadata, dict):
            metadata["checkmas_score"] = result.score
            metadata["checkmas_action"] = result.action
            metadata["checkmas_fallacies"] = result.fallacies

    return state
