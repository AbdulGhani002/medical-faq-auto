"""Pytest fixtures shared across the test suite."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Always run tests against the in-memory store.
os.environ.setdefault("FAQ_FORCE_MEMORY", "1")


@pytest.fixture(scope="session")
def faq_corpus() -> list[dict]:
    """A small, deterministic 6-FAQ corpus used by retrieval-level tests."""
    return [
        {"_id": "1", "specialty": "cardiovascular",
         "question": "What is angina?",
         "answer": "Angina is chest discomfort due to reduced blood flow.",
         "approved": True},
        {"_id": "2", "specialty": "cardiovascular",
         "question": "When should I take my blood pressure medicine?",
         "answer": "Most BP medicines are once daily, in the morning.",
         "approved": True},
        {"_id": "3", "specialty": "cardiovascular",
         "question": "Is chest pain always a heart attack?",
         "answer": "No. Chest pain has many causes.",
         "approved": True},
        {"_id": "4", "specialty": "radiology",
         "question": "Do I need to fast before my MRI scan?",
         "answer": "Most MRI scans do not require fasting.",
         "approved": True},
        {"_id": "5", "specialty": "physiotherapy",
         "question": "How often should I do my home exercises?",
         "answer": "Daily, two short sets, unless told otherwise.",
         "approved": True},
        {"_id": "6", "specialty": "physiotherapy",
         "question": "Is it normal to feel sore after a session?",
         "answer": "Mild soreness for 24-48 hours is normal.",
         "approved": True},
    ]
