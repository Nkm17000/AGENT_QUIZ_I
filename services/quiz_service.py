import json
import random
from pathlib import Path

from config import QUIZ_DIR, QUIZ_SIZE, MIX_ONLY
from utils.memory import load_memory, save_memory


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def _is_mix_file(path: Path) -> bool:
    return "mixed" in path.stem.casefold()


def _find_mix_file(files):
    mix_files = [path for path in files if _is_mix_file(path)]
    if not mix_files:
        raise FileNotFoundError(
            f"No mixed quiz JSON found in {QUIZ_DIR}. Expected a filename containing 'mixed'."
        )
    if len(mix_files) > 1:
        raise ValueError(
            "Multiple mixed quiz JSON files found: " + ", ".join(p.name for p in mix_files)
        )
    return mix_files[0]


def fetch_quiz():
    """Load exactly one shuffled five-question quiz from the mixed question bank."""
    files = sorted(Path(QUIZ_DIR).glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No quiz JSON files found in {QUIZ_DIR}")

    source = _find_mix_file(files) if MIX_ONLY else files[0]
    data = _load_json(source)
    if len(data) < QUIZ_SIZE:
        raise ValueError(f"{source.name} contains {len(data)} questions; need {QUIZ_SIZE}.")

    memory = load_memory()
    counters = memory.setdefault("counters", {})
    counter = int(counters.get(source.name, 0) or 0)
    if counter + QUIZ_SIZE > len(data):
        counter = 0

    selected = list(data[counter:counter + QUIZ_SIZE])
    if len(selected) != QUIZ_SIZE:
        raise ValueError(f"Could not select {QUIZ_SIZE} questions from {source.name}.")

    random.shuffle(selected)

    print(f"🎯 Mixed source: {source.name}")
    print(f"📊 Selected questions: {len(selected)} | source counter: {counter}")
    return {
        "questions": selected,
        "subject": "ALL SUBJECTS",
        "source_file": source.name,
        "counter": counter,
    }


def commit_quiz_counter(source_file: str, amount: int = QUIZ_SIZE) -> int:
    memory = load_memory()
    counters = memory.setdefault("counters", {})
    current = int(counters.get(source_file, 0) or 0)
    new_value = current + int(amount)
    counters[source_file] = new_value
    save_memory(memory)
    print(f"💾 Counter committed: {source_file}: {current} -> {new_value}")
    return new_value
