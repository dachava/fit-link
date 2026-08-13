# app/content/markdown.py
import re

_HEADING_RE = re.compile(r"^##\s+(.+)$")


def parse_sections(body: str) -> dict[str, str]:
    """Split a markdown body into sections keyed by lowercased '## Heading' text."""
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for line in body.splitlines():
        match = _HEADING_RE.match(line.strip())
        if match:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = match.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)

    if current is not None:
        sections[current] = "\n".join(buf).strip()

    return sections
