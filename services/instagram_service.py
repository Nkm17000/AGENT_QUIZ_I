import json
import time
from pathlib import Path

import requests

from config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_BUSINESS_ACCOUNT_ID,
    INSTAGRAM_SHARE_TO_FEED,
    INSTAGRAM_STATUS_POLL_SECONDS,
    INSTAGRAM_STATUS_TIMEOUT,
    INSTAGRAM_UPLOAD_TIMEOUT,
    META_GRAPH_VERSION,
)

MAX_REEL_BYTES = 1_000 * 1024 * 1024
GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"


def _require_config():
    if not INSTAGRAM_ACCESS_TOKEN:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN is missing.")
    if not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        raise ValueError("INSTAGRAM_BUSINESS_ACCOUNT_ID is missing.")


def _details(response):
    try:
        return json.dumps(response.json(), ensure_ascii=False)
    except ValueError:
        return response.text[:4000]


def _check(response, action):
    if not response.ok:
        raise RuntimeError(
            f"Instagram {action} failed: HTTP {response.status_code}. Meta response: {_details(response)}"
        )


def validate_account():
    _require_config()
    response = requests.get(
        f"{GRAPH_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}",
        params={
            "fields": "id,username,account_type",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )
    _check(response, "account validation")
    data = response.json()
    returned_id = str(data.get("id", ""))
    if returned_id != INSTAGRAM_BUSINESS_ACCOUNT_ID:
        raise RuntimeError(
            f"Instagram ID mismatch: configured {INSTAGRAM_BUSINESS_ACCOUNT_ID}, returned {returned_id}"
        )
    print(f"✅ Instagram account: @{data.get('username', 'unknown')} ({data.get('account_type', 'unknown')})")
    return data


def create_resumable_container(video_path, caption):
    """Create a Reel container and obtain Meta's direct upload URI."""
    path = Path(video_path)
    size = path.stat().st_size
    response = requests.post(
        f"{GRAPH_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media",
        data={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": caption,
            "share_to_feed": str(INSTAGRAM_SHARE_TO_FEED).lower(),
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )
    _check(response, "container creation")
    data = response.json()
    container_id = data.get("id")
    upload_uri = data.get("uri") or data.get("upload_uri")
    if not container_id or not upload_uri:
        raise RuntimeError(f"Incomplete Instagram container response: {json.dumps(data, ensure_ascii=False)}")
    print(f"📦 Container created: {container_id} | {size / 1024 / 1024:.1f} MB")
    return container_id, upload_uri


def upload_binary(upload_uri, video_path):
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("Video file is empty.")
    if size > MAX_REEL_BYTES:
        raise ValueError(f"Video is {size / 1024 / 1024:.1f} MB; Instagram limit is 1 GB.")

    print(f"📤 Uploading {size / 1024 / 1024:.1f} MB to Instagram...")
    with path.open("rb") as video:
        response = requests.post(
            upload_uri,
            headers={
                "Authorization": f"OAuth {INSTAGRAM_ACCESS_TOKEN}",
                "offset": "0",
                "file_size": str(size),
                "Content-Type": "application/octet-stream",
            },
            data=video,
            timeout=INSTAGRAM_UPLOAD_TIMEOUT,
        )
    _check(response, "binary upload")
    try:
        result = response.json()
    except ValueError:
        result = {"raw": response.text[:2000]}
    if result.get("success") is not True:
        raise RuntimeError(f"Instagram upload did not return success=true: {result}")
    print("✅ Binary upload completed")
    return result


def wait_until_ready(container_id):
    deadline = time.monotonic() + INSTAGRAM_STATUS_TIMEOUT
    last_status = None
    while time.monotonic() < deadline:
        response = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={
                "fields": "id,status_code,status",
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=60,
        )
        _check(response, "container status check")
        data = response.json()
        status = data.get("status_code") or data.get("status")
        if status != last_status:
            print(f"⏳ Instagram processing: {status}")
            last_status = status
        if status == "FINISHED":
            return data
        if status in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram processing failed: {json.dumps(data, ensure_ascii=False)}")
        time.sleep(INSTAGRAM_STATUS_POLL_SECONDS)
    raise TimeoutError(f"Instagram container {container_id} was not ready within {INSTAGRAM_STATUS_TIMEOUT}s.")


def publish_container(container_id):
    response = requests.post(
        f"{GRAPH_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )
    _check(response, "publish")
    result = response.json()
    media_id = result.get("id")
    if not media_id:
        raise RuntimeError(f"Instagram publish response has no media ID: {result}")
    print(f"📸 Instagram Reel published: {media_id}")
    return result


def publish_reel(video_path, caption):
    validate_account()
    container_id, upload_uri = create_resumable_container(video_path, caption)
    upload_binary(upload_uri, video_path)
    wait_until_ready(container_id)
    return publish_container(container_id)
