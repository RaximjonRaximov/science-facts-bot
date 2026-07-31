from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

from .db import FactsDatabase
from .facts import FactsStore, format_fact

HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Science Facts Bot</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; background: #f7f7f5; color: #222; }
  h1 { margin-bottom: 8px; }
  .card { background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); margin-bottom: 16px; }
  button { padding: 10px 16px; border: none; border-radius: 8px; background: #0f5e9e; color: #fff; cursor: pointer; }
  .fact { font-size: 1.1rem; line-height: 1.6; }
  .meta { color: #666; font-size: 0.9rem; margin-top: 12px; }
  input[type="text"] { padding: 10px; border: 1px solid #ccc; border-radius: 8px; width: 60%; margin-right: 8px; }
  ul { line-height: 1.8; }
  a { color: #0f5e9e; }
</style>
</head>
<body>
  <h1>Science Facts Bot</h1>
  <p>A Telegram bot with 10,000 science facts. Use the API or start the bot on Telegram.</p>

  <div class="card">
    <h2>Random fact</h2>
    <p class="fact" id="fact">Loading…</p>
    <p class="meta" id="fact-meta"></p>
    <button onclick="loadFact()">New fact</button>
  </div>

  <div class="card">
    <h2>Search</h2>
    <input id="q" type="text" placeholder="e.g. tree" />
    <button onclick="searchFacts()">Search</button>
    <ul id="results"></ul>
  </div>

  <div class="card">
    <h2>Categories</h2>
    <ul id="categories">Loading…</ul>
  </div>

  <div class="card">
    <h2>Stats</h2>
    <ul id="stats">Loading…</ul>
  </div>

  <script>
    async function loadFact(category) {
      const url = category ? `/api/fact?category=${encodeURIComponent(category)}` : '/api/fact';
      const res = await fetch(url);
      const data = await res.json();
      document.getElementById('fact').textContent = data.text;
      document.getElementById('fact-meta').textContent = `Category: ${data.category}`;
    }
    async function searchFacts() {
      const q = document.getElementById('q').value;
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      const list = document.getElementById('results');
      list.innerHTML = data.results.map(r => `<li>${r.text}</li>`).join('');
    }
    async function loadCategories() {
      const res = await fetch('/api/categories');
      const data = await res.json();
      document.getElementById('categories').innerHTML = data.categories.map(c => `<li>${c}</li>`).join('');
    }
    async function loadStats() {
      const res = await fetch('/api/stats');
      const data = await res.json();
      document.getElementById('stats').innerHTML = `
        <li>Total facts: ${data.total_facts}</li>
        <li>Categories: ${data.total_categories}</li>
        <li>Users: ${data.users}</li>
      `;
    }
    loadFact();
    loadCategories();
    loadStats();
  </script>
</body>
</html>
"""


def create_app(store: FactsStore | None = None, db: FactsDatabase | None = None) -> FastAPI:
    store = store or FactsStore()
    db = db or FactsDatabase()
    app = FastAPI(title="Science Facts Bot", version="1.0.0")

    @app.get("/", response_class=HTMLResponse)
    async def root():
        return HTMLResponse(content=HTML_PAGE)

    @app.get("/api/fact")
    async def fact(category: str | None = None):
        return store.random(category)

    @app.get("/api/search")
    async def search(q: str = Query(..., min_length=1), limit: int = 10):
        return {"query": q, "results": store.search(q, limit)}

    @app.get("/api/categories")
    async def categories():
        return {"categories": store.categories}

    @app.get("/api/stats")
    async def stats():
        db_stats = db.get_stats()
        return {
            "total_facts": store.count,
            "total_categories": len(store.categories),
            "users": db_stats["users"],
            "favorites": db_stats["favorites"],
            "daily_subscribers": db_stats["daily_subscribers"],
        }

    @app.get("/api/fact/{fact_id}")
    async def fact_by_id(fact_id: int):
        fact = store.get(fact_id)
        if not fact:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        return {**fact, "id": fact_id}

    return app
