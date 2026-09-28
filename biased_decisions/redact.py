"""Remove contact information from published text."""

import re

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def redact_contact(text: str) -> str:
    """Replace email addresses with [email removed].

    A conservative regex matches: local@domain.tld (at least one alphanumeric char,
    @ symbol, domain with at least one dot, TLD with at least 2 letters).
    """
    return _EMAIL_PATTERN.sub("[email removed]", text)
