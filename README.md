# Science Facts Bot

A useful Telegram bot and web admin for sharing daily science facts. It ships with 10,003 curated science facts across 32 categories.

## Features

- **10,003 science facts** from a public dataset (`data/facts.json`).
- **Telegram bot** with commands: `/start`, `/fact`, `/categories`, `/search`, `/favorite`, `/favorites`, `/daily`, `/stats`.
- **Web admin** built with FastAPI for browsing facts, searching, and viewing stats.
- **SQLite database** for user subscriptions and favorites.
- **Test coverage** with `pytest` for facts store, database, and API endpoints.

## Commands

```text
/fact              random fact
/fact <category>   random fact from category
/categories        list categories
/search <word>     search facts
/favorite          save the last shown fact
/favorites         list saved facts
/daily             toggle daily fact delivery
/stats             bot statistics
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Run web admin

```bash
python -m uvicorn app.main:app --reload
```

## Run Telegram bot

Set the environment variable and start the app. The bot runs alongside the web admin.

```bash
export TELEGRAM_TOKEN=your_token
python -m uvicorn app.main:app
```

## Data

Facts are stored in `data/facts.json` and loaded at startup. Each fact contains `text`, `category`, `source_file`, and `source_url`.

## License

MIT
