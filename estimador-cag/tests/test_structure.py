"""Valida que el proyecto respeta la estructura de carpetas pedida en el ejercicio."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "app/__init__.py",
    "app/main.py",
    "app/config.py",
    "app/routers/__init__.py",
    "app/routers/estimations.py",
    "app/services/__init__.py",
    "app/services/llm_service.py",
    "app/context/__init__.py",
    "app/context/examples.py",
    ".env.example",
    ".gitignore",
    "pyproject.toml",
    "README.md",
]


@pytest.mark.parametrize("relative_path", REQUIRED_FILES)
def test_required_file_exists(relative_path):
    assert (ROOT / relative_path).is_file(), f"Falta {relative_path}"


def test_env_is_gitignored():
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in ignored


def test_env_example_documents_variables():
    content = (ROOT / ".env.example").read_text()
    for var in ("LLM_PROVIDER", "LLM_MODEL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        assert f"{var}=" in content


def test_env_example_has_no_secret_values():
    for line in (ROOT / ".env.example").read_text().splitlines():
        if line.endswith("_API_KEY=") or not line.split("=")[0].endswith("_API_KEY"):
            continue
        pytest.fail(f".env.example contiene un valor para una API key: {line.split('=')[0]}")


def test_sample_transcription_exists():
    transcripts = list((ROOT / "transcripts").glob("*.txt"))
    assert transcripts, "Debe haber al menos una transcripción de ejemplo en transcripts/"
