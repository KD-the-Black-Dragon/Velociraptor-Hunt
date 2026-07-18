from __future__ import annotations

"""CP437 tileset-safe text for HUD and message logs."""

# Alloy CP437 font lacks many Unicode punctuation glyphs; normalize before draw/log.
_CP437_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("\u2014", " - "),  # em dash
    ("\u2013", "-"),  # en dash
    ("\u2018", "'"),  # left single quote
    ("\u2019", "'"),  # right single quote
    ("\u201c", '"'),  # left double quote
    ("\u201d", '"'),  # right double quote
)


def cp437_safe(text: str) -> str:
    """Replace Unicode punctuation with ASCII so libtcod CP437 rendering shows it."""
    for old, new in _CP437_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def enforce_sentence_capitalization(text: str) -> str:
    """Capitalize ``the …`` at line start and after ``.``, ``?``, or ``!`` (not ``-``)."""
    if not text:
        return text
    chars = list(text)

    def capitalize_at(index: int) -> None:
        if index < len(chars) and chars[index].isalpha():
            chars[index] = chars[index].upper()

    if text.startswith("the "):
        capitalize_at(0)
    for index, char in enumerate(chars):
        if char not in ".?!":
            continue
        next_index = index + 1
        while next_index < len(chars) and chars[next_index].isspace():
            next_index += 1
        capitalize_at(next_index)
    return "".join(chars)


class _SafeFormatMap(dict[str, str]):
    """``str.format_map`` helper: unknown keys stay as ``{name}`` literals."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def format_narrative_template(template: str, **placeholders: str) -> str:
    """Substitute known narrative placeholders; leave unknown ``{keys}`` verbatim.

    Data/mod typos (e.g. ``{predtaor}``) surface in-game instead of crashing.
    """
    try:
        return template.format_map(_SafeFormatMap(placeholders))
    except (ValueError, IndexError):
        # Unmatched braces or other format issues — show template as written.
        return template