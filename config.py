import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
QUIZ_DIR = Path(os.getenv("QUIZ_DIR", ASSETS_DIR / "quiz_data")).expanduser()
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output")).expanduser()
QUESTION_AUDIO_DIR = Path(os.getenv("QUESTION_AUDIO_DIR", ASSETS_DIR / "question_audio")).expanduser()

# Instagram Reels-friendly output.
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "720"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1280"))
FPS = int(os.getenv("FPS", "30"))
VIDEO_CRF = int(os.getenv("VIDEO_CRF", "30"))
VIDEO_PRESET = os.getenv("VIDEO_PRESET", "ultrafast")

COUNTDOWN_SECONDS = float(os.getenv("COUNTDOWN_SECONDS", "1"))
POST_AUDIO_WAIT_SECONDS = float(os.getenv("POST_AUDIO_WAIT_SECONDS", "1.5"))
ANSWER_SLIDE_DURATION = float(os.getenv("ANSWER_SLIDE_DURATION", "2"))

BACKGROUND_VOLUME = float(os.getenv("BACKGROUND_VOLUME", "0.22"))
TICK_VOLUME = float(os.getenv("TICK_VOLUME", "0.70"))
CORRECT_VOLUME = float(os.getenv("CORRECT_VOLUME", "0.90"))

TTS_VOICE = os.getenv("TTS_VOICE", "en-IN-NeerjaNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")
TTS_VOLUME = os.getenv("TTS_VOLUME", "+0%")
TTS_CONCURRENCY = max(1, int(os.getenv("TTS_CONCURRENCY", "5")))

BACKGROUND_AUDIO = ASSETS_DIR / "bg_music.mp3"
TICK_AUDIO = ASSETS_DIR / "tick.mp3"
CORRECT_AUDIO = ASSETS_DIR / "correct.mp3"

PAGE_URL = os.getenv("PAGE_URL", "https://smartlearninglab-react.pages.dev").strip()

# Instagram / Meta configuration.
META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0").strip()
INSTAGRAM_BUSINESS_ACCOUNT_ID = (os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID") or "").strip()
INSTAGRAM_ACCESS_TOKEN = (os.getenv("INSTAGRAM_ACCESS_TOKEN") or "").strip()
INSTAGRAM_SHARE_TO_FEED = os.getenv("INSTAGRAM_SHARE_TO_FEED", "true").strip().lower() == "true"
INSTAGRAM_STATUS_TIMEOUT = int(os.getenv("INSTAGRAM_STATUS_TIMEOUT", "600"))
INSTAGRAM_STATUS_POLL_SECONDS = int(os.getenv("INSTAGRAM_STATUS_POLL_SECONDS", "5"))
INSTAGRAM_UPLOAD_TIMEOUT = int(os.getenv("INSTAGRAM_UPLOAD_TIMEOUT", "900"))

# Test phase: exactly one mixed quiz containing five questions per run.
QUIZ_SIZE = int(os.getenv("QUIZ_SIZE", "5"))
MIX_ONLY = os.getenv("MIX_ONLY", "true").strip().lower() == "true"
