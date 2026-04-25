import re

from clearsmog import github_client

_MARKER_RE = re.compile(r"<!-- clearsmog:cell:([^>]+) -->")


def parse_bot_comments(comments: list[dict]) -> dict[str, int]:
    """Return {cell_key: comment_id} for all bot-managed comments."""
    result = {}
    for comment in comments:
        body = comment.get("body", "")
        match = _MARKER_RE.search(body)
        if match:
            result[match.group(1)] = comment["id"]
    return result


async def get_bot_comments(token: str, owner: str, repo: str, pr_number: int) -> dict[str, int]:
    comments = await github_client.list_pr_comments(token, owner, repo, pr_number)
    return parse_bot_comments(comments)


async def upsert_comment(
    token: str,
    owner: str,
    repo: str,
    pr_number: int,
    cell_key: str,
    body: str,
    existing: dict[str, int],
) -> None:
    if cell_key in existing:
        await github_client.edit_pr_comment(token, owner, repo, existing[cell_key], body)
    else:
        await github_client.post_pr_comment(token, owner, repo, pr_number, body)
