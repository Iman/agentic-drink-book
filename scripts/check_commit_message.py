"""Commit-message guard; call from an existing hook without replacing it."""

import re
import sys
from pathlib import Path

ATTRIBUTION = re.compile(
    r"(?im)^(?:author|committer|co-authored-by|signed-off-by|reviewed-by|reported-by|"
    r"contributor|participant|collaborator):[^\n]*(?:codex|chatgpt|openai|assistant|\bbot\b)"
    r"|(?:generated|written|authored|co-authored)\s+(?:by|with)\s+"
    r"(?:codex|chatgpt|openai|(?:an?\s+)?ai(?:\s+assistant)?)"
)


def allowed(message: str) -> bool:
    return ATTRIBUTION.search(message) is None


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_commit_message.py COMMIT_MESSAGE_FILE", file=sys.stderr)
        return 2
    if not allowed(Path(sys.argv[1]).read_text(encoding="utf-8")):
        print("Commit rejected: prohibited automated attribution.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
