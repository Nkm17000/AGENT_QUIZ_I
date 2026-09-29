import os
from pathlib import Path

from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID, OUTPUT_DIR, PAGE_URL
from services.instagram_service import publish_video_to_instagram
from services.quiz_service import QUIZ_SIZE, commit_quiz_counter, fetch_quizzes
from services.video_service import create_video, generate_images
from utils.file_utils import cleanup
from utils.memory import load_memory, save_memory


def _caption(subject: str) -> str:
    return f"""📊 ALL Subject Exam Focus

📚 Daily practice for serious aspirants

🎯 SSC | UPSC | Banking | Railway | RAS | IAS

For more quizzes, visit: {PAGE_URL}

💬 Drop your answer below

#sscpreparation #upsc #bankexam #railwayexam #mocktest #govtexams #studyreels"""


def _safe_name(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def _output_path(item) -> Path:
    source = _safe_name(Path(item["source_file"]).stem)
    number = item["quiz_number"]
    return OUTPUT_DIR / f"instagram_mixed_quiz_{source}_{number:05d}.mp4"


def _generate_one(item):
    quiz = item["questions"]
    if len(quiz) != QUIZ_SIZE:
        raise RuntimeError(
            f"{item['source_file']} quiz must contain exactly {QUIZ_SIZE} questions; "
            f"got {len(quiz)}"
        )

    print("\n" + "=" * 80)
    print(f"🎯 Generating Instagram Reel: {QUIZ_SIZE}-question mixed quiz")
    print(f"📊 Source: {item['source_file']} | counter: {item['counter']}")
    print("=" * 80)

    images = []
    output_video = _output_path(item)
    output_video.unlink(missing_ok=True)

    try:
        print("🖼️ Rendering slides...")
        images = generate_images(quiz, subject=item["subject"])

        print("🎬 Creating video...")
        create_video(quiz, output_video, subject=item["subject"])

        if not output_video.is_file() or output_video.stat().st_size <= 0:
            raise RuntimeError(f"Video file was not created correctly: {output_video}")

        if not INSTAGRAM_BUSINESS_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
            raise RuntimeError(
                "Instagram credentials are missing. Set "
                "INSTAGRAM_BUSINESS_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN."
            )

        print("📤 Publishing Reel to Instagram...")
        result = publish_video_to_instagram(str(output_video), _caption(item["subject"]))
        print(f"✅ Instagram published successfully: {result}")

        new_counter = commit_quiz_counter(item["source_file"], QUIZ_SIZE)
        memory = load_memory()
        last_run = memory.setdefault("last_run", {})
        last_run[item["source_file"]] = {
            "subject": item["subject"],
            "quiz_number": item["quiz_number"],
            "source_counter_after": new_counter,
            "platform": "instagram",
            "questions": QUIZ_SIZE,
        }
        save_memory(memory)
        return str(output_video)
    finally:
        cleanup(images)


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("📥 Preparing one 5-question mixed quiz...")
    quiz_jobs = fetch_quizzes()
    if not quiz_jobs:
        raise RuntimeError("No mixed quiz available")

    # A manual GitHub Actions run must publish exactly one video.
    # Scheduled/push runs keep the existing behavior and may process all jobs.
    is_manual_run = os.getenv("GITHUB_EVENT_NAME", "").strip().lower() == "workflow_dispatch"
    jobs_to_process = quiz_jobs[:1] if is_manual_run else quiz_jobs

    if is_manual_run:
        print("🖐️ Manual run detected: hard limit = 1 Instagram video")
    else:
        print(f"🤖 Automated run: processing {len(jobs_to_process)} available quiz job(s)")

    completed = 0
    try:
        for item in jobs_to_process:
            _generate_one(item)
            completed += 1
    finally:
        # Leave the generated MP4 in output for debugging/inspection.
        pass

    print("=" * 80)
    print(f"✅ Instagram quiz jobs completed: {completed}/{len(jobs_to_process)}")
    print("=" * 80)
