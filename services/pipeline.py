from pathlib import Path

from config import OUTPUT_DIR, PAGE_URL, QUIZ_SIZE
from services.instagram_service import publish_reel
from services.quiz_service import commit_quiz_counter, fetch_quiz
from services.video_service import create_video, generate_images, validate_video
from utils.file_utils import cleanup
from utils.memory import load_memory, save_memory


def _caption():
    return f"""🎯 5 Question Mixed Quiz\n\n📚 English • GK • Maths • Reasoning • Science\n\nComment your answers below 👇\n\nMore practice: {PAGE_URL}\n\n#smartlearninglab #quiz #dailyquiz #ssc #bankexam #railwayexam #gk #english #maths #reasoning #generalscience #reels"""


def _output_path(source_file, counter):
    stem = Path(source_file).stem.replace(" ", "_")
    return OUTPUT_DIR / f"instagram_mixed_quiz_{stem}_{counter:05d}.mp4"


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    job = fetch_quiz()
    questions = job["questions"]
    if len(questions) != QUIZ_SIZE:
        raise RuntimeError(f"Expected {QUIZ_SIZE} questions, got {len(questions)}")

    print("=" * 72)
    print(f"🚀 Instagram quiz test | {len(questions)} questions")
    print(f"📁 Source: {job['source_file']} | counter: {job['counter']}")
    print("=" * 72)

    images = []
    output_video = _output_path(job["source_file"], job["counter"])
    try:
        print("🖼️ Rendering quiz...")
        images = generate_images(questions)

        print("🎬 Creating Instagram-compatible MP4...")
        create_video(questions, output_video)
        validate_video(output_video)

        print("📤 Publishing Reel to Instagram...")
        result = publish_reel(output_video, _caption())

        new_counter = commit_quiz_counter(job["source_file"], QUIZ_SIZE)
        memory = load_memory()
        memory["last_run"] = {
            "platform": "instagram",
            "source_file": job["source_file"],
            "questions": QUIZ_SIZE,
            "source_counter_before": job["counter"],
            "source_counter_after": new_counter,
            "instagram_media_id": result.get("id"),
        }
        save_memory(memory)

        print("=" * 72)
        print("✅ Instagram test completed successfully")
        print(f"📹 Video: {output_video}")
        print(f"🆔 Media ID: {result.get('id')}")
        print("=" * 72)
    finally:
        cleanup(images)


if __name__ == "__main__":
    run_pipeline()
