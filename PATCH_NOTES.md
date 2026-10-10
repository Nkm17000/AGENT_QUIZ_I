# Impacted files — Smart Learning Lab 247 quiz 17 update

- `assets/logo.png`: replaced with supplied full logo.
- `services/renderer.py`: fixed outdated fixed-coordinate crop that cut out the new logo; renderer now uses the complete logo asset.
- `services/pipeline.py`: adds `@smartlearinglab247` to every generated Instagram caption.
- `services/quiz_service.py`: starts at source counter 160 (quiz 17) and blocks quiz generation once a source counter reaches 170.
- `data/history/history.json`: sets each source counter to 160 so the next successful quiz is quiz 17 and commits to 170.
- `config.py`: logo path is now used by the renderer through `LOGO_FILE`.

Regression: Python compilation, caption check, counter-state check, logo-render check, and a 2-second H.264 MP4 render/ffprobe validation passed. This test MP4 is a technical rendering check, not a full narration/publishing integration test.
