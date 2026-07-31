from fastapi.testclient import TestClient

from app.web import create_app
from app.facts import FactsStore
from app.db import FactsDatabase
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def client():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = FactsStore()
    db = FactsDatabase(db_path)
    app = create_app(store, db)
    with TestClient(app) as c:
        yield c
    Path(db_path).unlink(missing_ok=True)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Science Facts Bot" in response.text


def test_random_fact(client):
    response = client.get("/api/fact")
    assert response.status_code == 200
    assert "text" in response.json()


def test_search(client):
    response = client.get("/api/search?q=tree")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "tree"
    assert len(data["results"]) > 0


def test_categories(client):
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert len(response.json()["categories"]) > 0


def test_stats(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_facts"] > 0
