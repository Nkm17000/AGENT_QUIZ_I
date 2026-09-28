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

#sscpreparation #upsc #bankexam #railwayexam #ras #ias #mocktest #govtexams #studyreels"""


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
            f"{item['source_file']} quiz must contain exactly "
            f"{QUIZ_SIZE} questions; got {len(quiz)}"
        )

    print("\n" + "=" * 80)
    print(f"🎯 Generating Instagram mixed quiz #{item['quiz_number']}")
    print(f"📊 Questions: {len(quiz)} | source counter: {item['counter']}")
    print("=" * 80)

    print("🖼️ Rendering slides...")
    images = generate_images(quiz)
    output_video = _output_path(item)
    output_video.unlink(missing_ok=True)

    try:
        print("🎬 Creating video...")
        create_video(quiz, output_video)
        if not output_video.is_file():
            raise RuntimeError(f"Video file was not created: {output_video}")

        if not INSTAGRAM_BUSINESS_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
            raise RuntimeError(
                "Instagram publishing is enabled but credentials are missing. "
                "Set INSTAGRAM_BUSINESS_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN."
            )

        print("📤 Publishing Reel to Instagram...")
        result = publish_video_to_instagram(str(output_video), _caption(item["subject"]))
        print(f"✅ Instagram publish successful: {result}")

        new_counter = commit_quiz_counter(item["source_file"], QUIZ_SIZE)
        memory = load_memory()
        last_run = memory.setdefault("last_run", {})
        last_run[item["source_file"]] = {
            "platform": "instagram",
            "subject": item["subject"],
            "quiz_number": item["quiz_number"],
            "question_count": QUIZ_SIZE,
            "source_counter_after": new_counter,
        }
        save_memory(memory)
        return str(output_video)
    finally:
        cleanup(images)


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("📥 Preparing 5-question mixed quiz...")
    quiz_jobs = fetch_quizzes()
    if not quiz_jobs:
        print("🚫 No quiz available")
        return

    for item in quiz_jobs:
        _generate_one(item)

    print("🎉 Instagram mixed quiz pipeline completed successfully.")
