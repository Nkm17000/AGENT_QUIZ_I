import json
import time
from pathlib import Path

import requests

from config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_BUSINESS_ACCOUNT_ID,
    META_GRAPH_VERSION,
)

MAX_REEL_BYTES = 1_000 * 1024 * 1024
GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"


def _require_config():
    if not INSTAGRAM_ACCESS_TOKEN:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN is missing.")

    if not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        raise ValueError("INSTAGRAM_BUSINESS_ACCOUNT_ID is missing.")

    print("📸 Instagram Business Account ID: configured")


def _response_details(response: requests.Response) -> str:
    """Return Meta's JSON error without exposing access tokens."""
    try:
        payload = response.json()
        return json.dumps(payload, ensure_ascii=False)
    except ValueError:
        return response.text[:4000]


def _raise_meta_error(response: requests.Response, action: str):
    if response.ok:
        return

    details = _response_details(response)
    raise RuntimeError(
        f"Instagram {action} failed: HTTP {response.status_code}. "
        f"Meta response: {details}"
    )


def _validate_account():
    """Confirm that the configured ID is an Instagram professional account."""
    url = f"{GRAPH_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}"
    response = requests.get(
        url,
        params={
            "fields": "id,username",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )
    _raise_meta_error(response, "account validation")

    data = response.json()
    returned_id = str(data.get("id", ""))
    username = data.get("username") or "unknown"

    if returned_id != str(INSTAGRAM_BUSINESS_ACCOUNT_ID):
        raise RuntimeError(
            "Instagram account validation returned a different account ID. "
            f"Configured={INSTAGRAM_BUSINESS_ACCOUNT_ID}, returned={returned_id}"
        )

    print(f"✅ Instagram account validated: @{username}")


def _create_resumable_container(caption):
    """Create an Instagram Reel upload container for a local MP4."""
    url = f"{GRAPH_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
    response = requests.post(
        url,
        data={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": caption,
            "share_to_feed": "true",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )

    if not response.ok:
        _raise_meta_error(response, "Reel container creation")

    data = response.json()
    container_id = data.get("id")
    upload_uri = data.get("uri")

    if not container_id or not upload_uri:
        raise RuntimeError(
            "Instagram Reel container response is incomplete: "
            f"{json.dumps(data, ensure_ascii=False)}"
        )

    print(f"📦 Instagram Reel container created: {container_id}")
    return container_id, upload_uri


def _upload_video(upload_uri, video_path):
    """Upload the local MP4 to Meta's resumable upload endpoint."""
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Instagram video not found: {path}")

    file_size = path.stat().st_size
    if file_size <= 0:
        raise ValueError(f"Instagram video is empty: {path}")
    if file_size > MAX_REEL_BYTES:
        raise ValueError(
            f"Instagram Reel is {file_size / 1024 / 1024:.1f} MB; "
            f"maximum supported size is {MAX_REEL_BYTES / 1024 / 1024:.0f} MB."
        )

    headers = {
        "Authorization": f"OAuth {INSTAGRAM_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size),
        "Content-Type": "video/mp4",
    }

    print(f"📤 Uploading video to Instagram: {file_size / 1024 / 1024:.1f} MB")
    with path.open("rb") as video_file:
        response = requests.post(
            upload_uri,
            headers=headers,
            data=video_file,
            timeout=900,
        )

    if not response.ok:
        _raise_meta_error(response, "binary video upload")

    try:
        result = response.json()
    except ValueError:
        result = {"raw_response": response.text[:4000]}

    if result.get("success") is not True:
        raise RuntimeError(f"Instagram binary upload was not successful: {result}")

    print("✅ Instagram video upload completed")


def _wait_until_ready(container_id, timeout_seconds=900, poll_seconds=10):
    url = f"{GRAPH_BASE}/{container_id}"
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        response = requests.get(
            url,
            params={
                "fields": "status_code,status",
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=60,
        )
        _raise_meta_error(response, "container status check")

        data = response.json()
        status = data.get("status_code") or data.get("status")
        print(f"⏳ Instagram processing status: {status}")

        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise RuntimeError(
                "Instagram video processing failed: "
                f"{json.dumps(data, ensure_ascii=False)}"
            )

        time.sleep(poll_seconds)

    raise TimeoutError(
        f"Instagram Reel container {container_id} did not finish within "
        f"{timeout_seconds} seconds."
    )


def _publish_container(container_id):
    url = f"{GRAPH_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
    response = requests.post(
        url,
        data={
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=60,
    )

    if not response.ok:
        _raise_meta_error(response, "Reel publishing")

    result = response.json()
    media_id = result.get("id")
    if not media_id:
        raise RuntimeError(
            "Instagram publish response has no media ID: "
            f"{json.dumps(result, ensure_ascii=False)}"
        )

    print(f"📸 Instagram Reel published: {media_id}")
    return result


def publish_video_to_instagram(video_path, caption):
    """Upload one local MP4 as a Reel and publish it to Instagram."""
    _require_config()
    _validate_account()
    container_id, upload_uri = _create_resumable_container(caption)
    _upload_video(upload_uri, video_path)
    _wait_until_ready(container_id)
    return _publish_container(container_id)
