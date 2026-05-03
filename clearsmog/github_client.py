import base64

import httpx

_BASE = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def list_pr_files(token: str, owner: str, repo: str, pr_number: int) -> list[dict]:
    url = f"{_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_headers(token), params={"per_page": 100})
        response.raise_for_status()
        return response.json()


async def fetch_blob_content(token: str, owner: str, repo: str, blob_sha: str) -> str:
    url = f"{_BASE}/repos/{owner}/{repo}/git/blobs/{blob_sha}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_headers(token))
        response.raise_for_status()
        data = response.json()
        return base64.b64decode(data["content"]).decode("utf-8")


async def fetch_file_at_ref(token: str, owner: str, repo: str, path: str, ref: str) -> str | None:
    url = f"{_BASE}/repos/{owner}/{repo}/contents/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_headers(token), params={"ref": ref})
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return base64.b64decode(data["content"]).decode("utf-8")


async def list_pr_comments(token: str, owner: str, repo: str, pr_number: int) -> list[dict]:
    url = f"{_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_headers(token), params={"per_page": 100})
        response.raise_for_status()
        return response.json()


async def post_pr_comment(token: str, owner: str, repo: str, pr_number: int, body: str) -> dict:
    url = f"{_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=_headers(token), json={"body": body})
        response.raise_for_status()
        return response.json()


async def edit_pr_comment(token: str, owner: str, repo: str, comment_id: int, body: str) -> dict:
    url = f"{_BASE}/repos/{owner}/{repo}/issues/comments/{comment_id}"
    async with httpx.AsyncClient() as client:
        response = await client.patch(url, headers=_headers(token), json={"body": body})
        response.raise_for_status()
        return response.json()
