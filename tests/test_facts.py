import json
import tempfile
from pathlib import Path

import pytest

from app.facts import FactsStore, format_fact


@pytest.fixture
def sample_facts_path():
    data = [
        {"text": "Fact one", "category": "space"},
        {"text": "Fact two", "category": "biology"},
        {"text": "Another space fact", "category": "space"},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


def test_store_count_and_categories(sample_facts_path):
    store = FactsStore(sample_facts_path)
    assert store.count == 3
    assert set(store.categories) == {"biology", "space"}


def test_random_returns_fact(sample_facts_path):
    store = FactsStore(sample_facts_path)
    fact = store.random()
    assert "text" in fact
    assert "id" in fact


def test_random_by_category(sample_facts_path):
    store = FactsStore(sample_facts_path)
    fact = store.random("space")
    assert "space" in fact["category"]


def test_search(sample_facts_path):
    store = FactsStore(sample_facts_path)
    results = store.search("space")
    assert len(results) == 2


def test_get_by_index(sample_facts_path):
    store = FactsStore(sample_facts_path)
    fact = store.get(1)
    assert fact["category"] == "biology"
    assert store.get(99) is None


def test_format_fact(sample_facts_path):
    store = FactsStore(sample_facts_path)
    fact = store.get(0)
    text = format_fact(fact)
    assert "Fact one" in text
    assert "Category" in text
