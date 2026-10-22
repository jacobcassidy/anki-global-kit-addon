"""Recognize local stylesheet imports without mistaking comments for rules."""

import re
from posixpath import normpath
from urllib.parse import unquote, urlsplit

_STRING = r"""(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')"""
_TOKEN = re.compile(rf"/\*.*?(?:\*/|\Z)|{_STRING}|\\.|.", re.DOTALL)
_IMPORT = re.compile(
    rf"@import\b\s*(?:url\(\s*(?P<url>{_STRING}|[^\s()'\"]+)\s*\)|(?P<string>{_STRING}))",
    re.IGNORECASE | re.DOTALL,
)
_ESCAPE = re.compile(
    r"\\([0-9a-fA-F]{1,6})(?:\r\n|[\t\n\f\r ])?|\\(\r\n|[\n\r\f])|\\(.)",
    re.DOTALL,
)


def _leading_statements(css: str):
    statement = []
    parentheses = 0
    for match in _TOKEN.finditer(css):
        token = match[0]
        if token.startswith("/*"):
            statement.append(" ")
            continue
        if token == "{":
            # Imports after a style rule or block at-rule are ineffective.
            if parentheses == 0:
                return
        if token == "(":
            parentheses += 1
        elif token == ")":
            parentheses -= 1
        if token == ";" and parentheses == 0:
            yield "".join(statement).strip()
            statement = []
        else:
            statement.append(token)
    if statement:
        yield "".join(statement).strip()


def _unescape(value: str) -> str:
    def replace(match):
        if match[1] is not None:
            point = int(match[1], 16)
            return (
                chr(point)
                if 0 < point <= 0x10FFFF and not 0xD800 <= point <= 0xDFFF
                else "\ufffd"
            )
        return "" if match[2] is not None else match[3]

    return _ESCAPE.sub(replace, value)


def has_stylesheet_import(css: str, filename: str) -> bool:
    """Find a leading local @import, allowing charset and layer statements."""
    for statement in _leading_statements(css):
        if not statement:
            continue
        match = _IMPORT.match(statement)
        if match is None:
            if re.match(r"@(?:charset|layer)\b", statement, re.IGNORECASE):
                continue
            return False
        target = match["url"] or match["string"]
        if target.startswith(("'", '"')):
            target = target[1:-1]
        try:
            url = urlsplit(_unescape(target))
        except ValueError:
            continue
        if (
            not url.scheme
            and not url.netloc
            and normpath(unquote(url.path)) == filename
        ):
            return True
    return False
