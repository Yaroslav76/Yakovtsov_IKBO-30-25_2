"""Общие вспомогательные средства для модульных тестов."""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
DATA = os.path.join(ROOT, "tests", "data")
MOCK_REPO = os.path.join(ROOT, "tests", "mock_repo")


def write_json(data):
    """Записывает data во временный JSON-файл и возвращает путь."""
    handle, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(handle, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path
