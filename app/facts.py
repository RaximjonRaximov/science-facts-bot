import json
import random
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent.parent / "data" / "facts.json"


class FactsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or DATA_PATH
        self._facts: list[dict[str, Any]] = []
        self._by_category: dict[str, list[int]] = {}
        self._load()

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            self._facts = json.load(f)

        self._by_category = {}
        for idx, fact in enumerate(self._facts):
            category = fact.get("category", "general")
            self._by_category.setdefault(category, []).append(idx)

    @property
    def count(self) -> int:
        return len(self._facts)

    @property
    def categories(self) -> list[str]:
        return sorted(self._by_category.keys())

    def get(self, index: int) -> dict[str, Any] | None:
        try:
            return self._facts[index]
        except IndexError:
            return None

    def random(self, category: str | None = None) -> dict[str, Any]:
        if category and category in self._by_category:
            idx = random.choice(self._by_category[category])
        else:
            idx = random.randrange(len(self._facts))
        fact = self._facts[idx].copy()
        fact["id"] = idx
        return fact

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = query.lower()
        results = []
        for idx, fact in enumerate(self._facts):
            text = fact.get("text", "").lower()
            category = fact.get("category", "").lower()
            if q in text or q in category:
                item = fact.copy()
                item["id"] = idx
                results.append(item)
                if len(results) >= limit:
                    break
        return results

    def facts_in_category(self, category: str, limit: int = 50) -> list[dict[str, Any]]:
        indices = self._by_category.get(category, [])[:limit]
        return [{**self._facts[i], "id": i} for i in indices]


def format_fact(fact: dict[str, Any]) -> str:
    text = fact.get("text", "")
    category = fact.get("category", "science").replace("_", " ").title()
    source = fact.get("source_url", "")
    footer = f"\n\nCategory: {category}"
    if source:
        footer += f"\nSource: {source}"
    return text + footer
