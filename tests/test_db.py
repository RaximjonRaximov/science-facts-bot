import tempfile
from pathlib import Path

import pytest

from app.db import FactsDatabase


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = FactsDatabase(path)
    yield db
    Path(path).unlink(missing_ok=True)


def test_ensure_user_and_daily(db):
    db.ensure_user(1, 100, "alice")
    assert not db.is_daily_enabled(1)
    db.set_daily(1, True)
    assert db.is_daily_enabled(1)
    db.set_daily(1, False)
    assert not db.is_daily_enabled(1)


def test_favorite(db):
    db.ensure_user(1, 100, "alice")
    assert db.add_favorite(1, 5) is True
    assert db.add_favorite(1, 5) is False
    assert db.get_favorites(1) == [5]
    db.remove_favorite(1, 5)
    assert db.get_favorites(1) == []


def test_stats(db):
    db.ensure_user(1, 100, "alice")
    db.ensure_user(2, 101, "bob")
    db.set_daily(1, True)
    db.add_favorite(1, 3)
    stats = db.get_stats()
    assert stats["users"] == 2
    assert stats["daily_subscribers"] == 1
    assert stats["favorites"] == 1
