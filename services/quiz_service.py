import json
import random
from pathlib import Path

from config import MIXED_QUIZ_FILE, QUIZ_DIR
from utils.memory import load_memory, save_memory

QUIZ_SIZE = 5


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def fetch_quizzes():
    """Return exactly one 5-question quiz from the mixed JSON source."""
    path = Path(QUIZ_DIR) / MIXED_QUIZ_FILE
    if not path.is_file():
        raise FileNotFoundError(f"Mixed quiz JSON not found: {path}")

    data = _load_json(path)
    if len(data) < QUIZ_SIZE:
        raise ValueError(
            f"{path.name} contains only {len(data)} questions; "
            f"at least {QUIZ_SIZE} are required."
        )

    memory = load_memory()
    counters = memory.setdefault("counters", {})
    counter = int(counters.get(path.name, 0) or 0)

    # Restart at the beginning when the next 5-question window would exceed
    # the source. This prevents partial quizzes.
    if counter + QUIZ_SIZE > len(data):
        counter = 0

    batch = list(data[counter:counter + QUIZ_SIZE])
    if len(batch) != QUIZ_SIZE:
        raise ValueError(
            f"Could not select exactly {QUIZ_SIZE} questions from {path.name} "
            f"at counter {counter}"
        )

    random.shuffle(batch)

    item = {
        "questions": batch,
        "subject": "ALL SUBJECTS",
        "source_file": path.name,
        "quiz_number": (counter // QUIZ_SIZE) + 1,
        "quiz_count_for_source": max(1, len(data) // QUIZ_SIZE),
        "counter": counter,
    }

    print(
        f"🎯 ALL SUBJECTS: selected exactly {QUIZ_SIZE} questions from "
        f"{path.name}; starting counter {counter}"
    )
    return [item]


def commit_quiz_counter(source_file: str, amount: int = QUIZ_SIZE) -> int:
    """Advance the source counter only after successful video publishing."""
    memory = load_memory()
    counters = memory.get("counters")
    if not isinstance(counters, dict):
        counters = {}

    current = int(counters.get(source_file, 0) or 0)
    new_value = current + int(amount)
    counters[source_file] = new_value
    memory["counters"] = counters
    save_memory(memory)
    print(f"💾 Counter committed: {source_file}: {current} -> {new_value}")
    return new_value
