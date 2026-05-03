import hashlib
import hmac
import json
import logging

from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI()
logger = logging.getLogger(__name__)

_processed_shas: set[str] = set()


def verify_signature(body: bytes, secret: str, signature_header: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@app.post("/webhook")
async def webhook(
    request: Request,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
):
    body = await request.body()

    from clearsmog.config import settings

    if not verify_signature(body, settings.webhook_secret, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {"ok": True}

    payload = json.loads(body)
    action = payload.get("action", "")
    if action not in {"opened", "synchronize", "reopened"}:
        return {"ok": True}

    head_sha = payload["pull_request"]["head"]["sha"]
    if head_sha in _processed_shas:
        logger.info("Already processed SHA %s, skipping", head_sha)
        return {"ok": True}

    try:
        await handle_pull_request(payload)
        _processed_shas.add(head_sha)
    except Exception:
        logger.exception("Error handling pull_request event for SHA %s", head_sha)

    return {"ok": True}


async def handle_pull_request(payload: dict) -> None:
    from clearsmog import comment_manager, github_auth, github_client, notebook_diff
    from clearsmog.comment_builder import build_comment

    installation_id = payload["installation"]["id"]
    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = payload["pull_request"]["number"]
    base_sha = payload["pull_request"]["base"]["sha"]

    from clearsmog.config import settings

    jwt = github_auth.generate_app_jwt(settings.app_id, settings.private_key)
    token = await github_auth.get_installation_token(jwt, installation_id)

    pr_files = await github_client.list_pr_files(token, owner, repo, pr_number)
    notebook_files = [f for f in pr_files if f["filename"].endswith(".ipynb")]

    if not notebook_files:
        return

    existing_comments = await comment_manager.get_bot_comments(token, owner, repo, pr_number)

    for nb_file in notebook_files:
        filename = nb_file["filename"]
        status = nb_file["status"]

        if status == "removed":
            continue

        head_content = await github_client.fetch_blob_content(token, owner, repo, nb_file["sha"])

        if status == "added":
            base_content = None
        else:
            base_content = await github_client.fetch_file_at_ref(
                token, owner, repo, filename, base_sha
            )

        diffs = notebook_diff.diff_notebooks(base_content, head_content)

        for diff in diffs:
            comment_body = build_comment(diff, filename)
            await comment_manager.upsert_comment(
                token, owner, repo, pr_number, diff.cell_key, comment_body, existing_comments
            )
