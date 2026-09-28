# Smart Learning Lab — Instagram Quiz Reel Generator

This version is intentionally Instagram-only. Facebook publishing code has been removed.

## Current test scope

- Uses the mixed question JSON only.
- Generates exactly 5 questions per run.
- Shuffles those 5 questions.
- Creates a 720×1280, 30 FPS H.264/AAC MP4.
- Uploads the local MP4 through Instagram's resumable Reel upload flow.
- Waits for Meta processing to finish.
- Publishes the Reel.
- Advances the mixed-source counter only after successful Instagram publishing.

Meta's Reel publishing flow is container-based: create the Reel container, upload the video, poll until `FINISHED`, then call `media_publish`. Resumable upload avoids requiring a public video URL. See Meta's Reels sample and API documentation for the current flow and media requirements. 

## GitHub Actions secrets

Add:

- `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- `INSTAGRAM_ACCESS_TOKEN`

The Instagram account must be an eligible professional account and the Meta app/token must have the permissions required for content publishing.

## Schedule

The workflow supports:

- manual `workflow_dispatch`
- every push to `main`, except a history-only commit
- 02:00, 08:00, 14:00 and 20:00 UTC

## Local run

```bash
python -m pip install -r requirements.txt
python app.py
```

FFmpeg and FFprobe must be available on PATH.
