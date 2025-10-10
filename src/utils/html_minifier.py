"""HTML minification utilities for outbound emails."""

from typing import Optional

try:
    # htmlmin provides reliable whitespace control for HTML emails when configured
    from htmlmin import minify as _html_minify
except ImportError:  # pragma: no cover - handled by dependency management
    _html_minify = None


def minify_html(html: str, *, remove_comments: bool = True) -> str:
    """Return a minified version of the provided HTML string.

    Args:
        html: The HTML content to minify.
        remove_comments: When True, strips HTML comments as part of minification.

    Returns:
        The minified HTML string. If the htmlmin library is unavailable, returns
        the input unchanged to avoid breaking the email pipeline.
    """

    if not html:
        return html

    if _html_minify is None:
        return html

    return _html_minify(
        html,
        remove_comments=remove_comments,
        remove_empty_space=True,
        reduce_empty_attributes=True,
        reduce_boolean_attributes=True,
        remove_optional_attribute_quotes=False,
        convert_charrefs=False,
    )
