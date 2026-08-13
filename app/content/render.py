# app/content/render.py
import markdown as _markdown

_MD = _markdown.Markdown(extensions=["extra", "sane_lists"])


def render_markdown(text: str) -> str:
    _MD.reset()
    return _MD.convert(text)
