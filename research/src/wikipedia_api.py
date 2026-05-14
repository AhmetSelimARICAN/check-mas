"""
Wikipedia API — Evidence from Wikipedia for CHECK-MAS experiments.

Fetches real Wikipedia content to use as evidence for agent debates and Commander.
Uses the free MediaWiki API (no key required). User-Agent set per Wikimedia guidelines.

If you see SSL certificate errors, fix your Python cert bundle (e.g. on macOS run
the "Install Certificates.command" from your Python install, or use a venv with certifi).

Usage:
    from src.wikipedia_api import fetch_wikipedia_evidence

    evidence = fetch_wikipedia_evidence("Roman Empire")
    # or from a claim:
    evidence = fetch_wikipedia_evidence_for_claim("The Roman Empire fell in 1453.")
"""

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

# Wikimedia API: https://www.mediawiki.org/wiki/API
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "CHECK-MAS-Lab/1.0 (Educational research; https://github.com/...)"
MAX_EVIDENCE_CHARS = 2000  # cap so prompts stay manageable


def _ssl_context() -> ssl.SSLContext:
    """SSL context that works on macOS (avoids CERTIFICATE_VERIFY_FAILED). Prefer certifi."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _request(params: dict) -> dict:
    """GET request to Wikipedia API; returns JSON as dict."""
    url = WIKI_API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        ctx = _ssl_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        return {"error": str(e)}


def search_wikipedia(query: str, limit: int = 3) -> list[dict]:
    """
    Search Wikipedia; returns list of page info: title, pageid, snippet.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
    }
    data = _request(params)
    if "error" in data:
        return []
    return data.get("query", {}).get("search", [])


def get_page_extract(page_id: int, chars: int = MAX_EVIDENCE_CHARS) -> Optional[str]:
    """
    Get plain-text extract (intro) for a page by page_id.
    Trims to roughly `chars` characters.
    """
    params = {
        "action": "query",
        "pageids": page_id,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "format": "json",
    }
    data = _request(params)
    if "error" in data:
        return None
    pages = data.get("query", {}).get("pages", {})
    page = pages.get(str(page_id), {})
    extract = page.get("extract", "").strip()
    if not extract:
        return None
    if len(extract) > chars:
        extract = extract[: chars - 3].rsplit(" ", 1)[0] + "..."
    return extract


def fetch_wikipedia_evidence(query: str, max_chars: int = MAX_EVIDENCE_CHARS) -> str:
    """
    Fetch evidence text from Wikipedia for a given query (topic or claim).

    - Searches Wikipedia for the query.
    - Takes the first result and returns its intro extract.
    - If search fails or no extract, returns an empty string.

    Args:
        query: Search string (e.g. "Roman Empire", or full claim).
        max_chars: Maximum length of returned evidence text.

    Returns:
        Plain-text evidence string, or "" on failure.
    """
    results = search_wikipedia(query, limit=1)
    if not results:
        return ""
    page_id = results[0].get("pageid")
    if not page_id:
        return ""
    text = get_page_extract(page_id, chars=max_chars)
    return text or ""


def _claim_to_search_query(claim: str) -> list[str]:
    """
    Derive one or more search queries from a claim for Wikipedia search.

    Strategy:
      1. Extract noun-phrase subject (remove filler verbs, articles, numbers at end).
      2. Use full claim as fallback.
    Returns a list of candidate queries (best first).
    """
    claim = claim.strip()
    if not claim:
        return ["Wikipedia"]
    # Remove trailing period
    claim = re.sub(r"\s*\.\s*$", "", claim)

    # Stop words and filler verbs to remove for a cleaner topic query
    _stop = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "has", "have", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "can", "could", "that", "this", "it", "its",
        "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
        "not", "no", "and", "or", "but", "if", "than", "about", "into",
    }

    words = claim.split()

    # Strategy 1: extract key nouns — remove stop words and pure numbers
    key_words = [w for w in words if w.lower() not in _stop and not re.match(r"^\d+$", w)]
    topic_query = " ".join(key_words[:5]) if key_words else claim

    # Strategy 2: full claim (trimmed)
    full_query = " ".join(words[:8])

    # Strategy 3: subject-focused — first proper noun cluster
    proper = []
    for w in words:
        if w[0].isupper() and w.lower() not in _stop:
            proper.append(w)
        elif proper:
            break
    proper_query = " ".join(proper) if len(proper) >= 2 else None

    queries = []
    if proper_query and proper_query != topic_query:
        queries.append(proper_query)
    queries.append(topic_query)
    if full_query != topic_query:
        queries.append(full_query)
    return queries


def fetch_wikipedia_evidence_for_claim(claim: str, max_chars: int = MAX_EVIDENCE_CHARS) -> str:
    """
    Fetch Wikipedia evidence relevant to a fact-checking claim.

    Tries multiple search queries derived from the claim (topic-focused first,
    then full claim). Picks the first result that returns a non-empty extract.

    Args:
        claim: Full claim sentence.
        max_chars: Maximum length of evidence text.

    Returns:
        Plain-text evidence from Wikipedia, or "" on failure.
    """
    queries = _claim_to_search_query(claim)
    # Collect key terms from claim for relevance check
    _stop = {"the", "a", "an", "is", "are", "was", "were", "in", "at", "of", "to", "for", "on", "by", "and", "or", "that", "this"}
    claim_terms = {w.lower().strip(".,!?") for w in claim.split() if w.lower() not in _stop and len(w) > 2}
    best_evidence = ""
    best_overlap = 0
    for q in queries:
        evidence = fetch_wikipedia_evidence(q, max_chars=max_chars)
        if not evidence or len(evidence) < 50:
            continue
        # Count how many claim terms appear in evidence
        ev_lower = evidence.lower()
        overlap = sum(1 for t in claim_terms if t in ev_lower)
        if overlap > best_overlap:
            best_evidence = evidence
            best_overlap = overlap
        # If good overlap, use it immediately
        if overlap >= 2:
            return evidence
    return best_evidence


def main() -> None:
    """Quick test: fetch evidence for a few claims."""
    test_claims = [
        "The Roman Empire fell in 1453.",
        "Albert Einstein failed mathematics in school.",
        "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
    ]
    print("Wikipedia API — evidence fetch test\n" + "=" * 50)
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        evidence = fetch_wikipedia_evidence_for_claim(claim)
        if evidence:
            print(f"Evidence ({len(evidence)} chars):\n{evidence[:400]}...")
        else:
            print("(No evidence returned)")
    print("\n" + "=" * 50 + "\nDone.")


if __name__ == "__main__":
    main()
