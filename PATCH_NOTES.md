# Instagram 5-Question Pipeline Patch

## Fix
The previous repository had a version mismatch: `services/video_service.py` imported `VIDEO_PRESET`, but `config.py` did not define it. This patch adds the missing setting and makes the video service use it.

## Included behavior
- Instagram only
- Exactly one mixed quiz per run
- Exactly 5 questions
- Source: `smart_learning_lab_50000_mixed_questions.json`
- Instagram resumable Reel upload/publish flow
- 30 FPS, 720x1280, H.264/AAC output
- `VIDEO_PRESET=ultrafast`
- Counter advances only after successful Instagram publishing

## Replace these files
- `config.py`
- `services/video_service.py`
- `services/quiz_service.py`
- `services/pipeline.py`
- `services/instagram_service.py`
- `.github/workflows/run.yml`
- `.env.example`

Do not replace `data/history/history.json`; keep your existing counter/history.

## 2026-09-29 Instagram visual update
- Applied subject-specific professional themes to Instagram Reels.
- Removed diagonal/cross-line decorations and inner frame.
- Fixed A/B/C/D marker-to-text spacing and Hindi/English option layout.
- Reserved explanation space and improved explanation contrast.
- Passed subject from pipeline through video service into renderer.
- Explicitly suppresses subtitle streams with FFmpeg `-sn`.
- Preserved Instagram upload/authentication workflow.
