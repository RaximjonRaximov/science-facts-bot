import os

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from .db import FactsDatabase
from .facts import FactsStore, format_fact


class FactsBot:
    def __init__(self, token: str, store: FactsStore, db: FactsDatabase):
        self.token = token
        self.store = store
        self.db = db
        self.application = Application.builder().token(token).build()
        self._register_handlers()

    def _register_handlers(self) -> None:
        app = self.application
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("fact", self.fact))
        app.add_handler(CommandHandler("categories", self.categories))
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("favorite", self.favorite))
        app.add_handler(CommandHandler("favorites", self.favorites))
        app.add_handler(CommandHandler("daily", self.daily))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("stats", self.stats))
        app.add_handler(CallbackQueryHandler(self.category_callback, pattern="^cat:"))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        if user and chat:
            self.db.ensure_user(user.id, chat.id, user.username)
        text = (
            "Welcome to the Science Facts Bot! ")
        await update.message.reply_text(
            f"{text}\n\n"
            "Commands:\n"
            "/fact — random fact\n"
            "/categories — browse by topic\n"
            "/search <word> — find facts\n"
            "/favorite — save last fact\n"
            "/favorites — your saved facts\n"
            "/daily — toggle daily facts\n"
            "/help — show help"
        )

    async def fact(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        category = " ".join(context.args) if context.args else None
        fact = self.store.random(category)

        if user and chat:
            self.db.ensure_user(user.id, chat.id, user.username)
            context.user_data["last_fact_id"] = fact["id"]

        await update.message.reply_text(format_fact(fact))

    async def categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        cats = self.store.categories
        lines = [f"/{i+1}. {name}" for i, name in enumerate(cats[:20])]
        await update.message.reply_text(
            "Available categories:\n\n" + "\n".join(lines)
            + "\n\nUse /fact <category> for a random fact in a category."
        )

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args)
        if not query:
            await update.message.reply_text("Usage: /search <keyword>")
            return

        results = self.store.search(query, limit=5)
        if not results:
            await update.message.reply_text("No facts found for that query.")
            return

        messages = [format_fact(r) for r in results]
        await update.message.reply_text("\n\n---\n\n".join(messages))

    async def favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not user:
            return

        fact_id = context.user_data.get("last_fact_id")
        if fact_id is None:
            await update.message.reply_text("Send /fact first, then /favorite to save it.")
            return

        if self.db.add_favorite(user.id, fact_id):
            await update.message.reply_text("Saved to your favorites.")
        else:
            await update.message.reply_text("Already in your favorites.")

    async def favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not user:
            return

        ids = self.db.get_favorites(user.id)
        if not ids:
            await update.message.reply_text("You have no favorites yet.")
            return

        facts = [self.store.get(i) for i in ids[:10]]
        messages = [format_fact({**f, "id": i}) for i, f in zip(ids[:10], facts) if f]
        await update.message.reply_text("Your favorites:\n\n---\n\n".join(messages))

    async def daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        if not user or not chat:
            return

        current = self.db.is_daily_enabled(user.id)
        self.db.ensure_user(user.id, chat.id, user.username)
        self.db.set_daily(user.id, not current)
        status = "enabled" if not current else "disabled"
        await update.message.reply_text(f"Daily facts {status}.")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Commands:\n"
            "/fact — random fact\n"
            "/fact <category> — fact from a category\n"
            "/categories — list categories\n"
            "/search <word> — search facts\n"
            "/favorite — save the last fact\n"
            "/favorites — list saved facts\n"
            "/daily — toggle daily delivery\n"
            "/stats — bot statistics"
        )

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        db_stats = self.db.get_stats()
        text = (
            f"Total facts: {self.store.count}\n"
            f"Categories: {len(self.store.categories)}\n"
            f"Users: {db_stats['users']}\n"
            f"Favorites: {db_stats['favorites']}\n"
            f"Daily subscribers: {db_stats['daily_subscribers']}"
        )
        await update.message.reply_text(text)

    async def category_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.callback_query.answer()
        category = update.callback_query.data.replace("cat:", "")
        fact = self.store.random(category)
        await update.callback_query.edit_message_text(format_fact(fact))

    async def run(self) -> None:
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()


async def build_bot() -> FactsBot | None:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return None
    store = FactsStore()
    db = FactsDatabase()
    return FactsBot(token, store, db)
