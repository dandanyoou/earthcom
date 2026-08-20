"""M8 search normalization — widens the query, never ranks it.

Output has no boost/weight/sort fields by construction; the server owns
ordering. When nothing matches the dictionary the original terms pass through
unchanged, so a normalizer failure can never empty the results (§7.10, B07).
"""

import re

from pangaea_ai import lexicon

SCHEMA_VERSION = "search.v1"


def normalize(query: str) -> dict[str, list[str]]:
    tokens = [token for token in re.split(r"[\s,/]+", query.strip()) if token]
    terms: list[str] = []
    seen: set[str] = set()

    def add(term: str) -> None:
        key = term.lower()
        if key and key not in seen:
            seen.add(key)
            terms.append(term)

    for token in tokens:
        add(token)
        for expansion in lexicon.SEARCH_SYNONYMS.get(token.lower(), ()):
            add(expansion)
        # strip common Korean suffixes like "잘하는 사람" tails
        stripped = re.sub(r"(잘하는|하는|가능한|구합니다|찾아요|사람|분)$", "", token)
        if stripped and stripped != token:
            add(stripped)
            for expansion in lexicon.SEARCH_SYNONYMS.get(stripped.lower(), ()):
                add(expansion)

    return {"terms": terms[:12]}
