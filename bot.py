import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB = "apple_fortune.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            result TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_round(user_id, result):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rounds (user_id, result, created_at) VALUES (?, ?, ?)",
        (user_id, result, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def get_stats(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM rounds WHERE user_id=?",
        (user_id,)
    )
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM rounds WHERE user_id=? AND result='win'",
        (user_id,)
    )
    wins = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM rounds WHERE user_id=? AND result='loss'",
        (user_id,)
    )
    losses = cur.fetchone()[0]

    conn.close()
    return total, wins, losses


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍎 Apple Fortune Analyzer botiga xush kelibsiz!\n\n"
        "Natija qo‘shish:\n"
        "/win — yutuq\n"
        "/loss — yutqazish\n\n"
        "/stats — statistika\n"
        "/history — tarix\n"
        "/clear — tarixni tozalash\n\n"
        "⚠️ Bu bot keyingi katakni oldindan aniqlamaydi. "
        "Faqat statistik tahlil qiladi."
    )


async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_round(update.effective_user.id, "win")
    await update.message.reply_text("🍎 Yutuq saqlandi.")


async def loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_round(update.effective_user.id, "loss")
    await update.message.reply_text("💥 Yutqazish saqlandi.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, wins, losses = get_stats(update.effective_user.id)

    if total == 0:
        await update.message.reply_text("📊 Hali ma'lumot yo‘q.")
        return

    win_percent = wins / total * 100
    loss_percent = losses / total * 100

    await update.message.reply_text(
        f"📊 STATISTIKA\n\n"
        f"Jami raund: {total}\n"
        f"🍎 Yutuq: {wins} ({win_percent:.1f}%)\n"
        f"💥 Yutqazish: {losses} ({loss_percent:.1f}%)"
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT result, created_at FROM rounds "
        "WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (update.effective_user.id,)
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📭 Tarix bo‘sh.")
        return

    text = "📜 Oxirgi 20 raund:\n\n"

    for i, (result, created_at) in enumerate(rows, 1):
        icon = "🍎" if result == "win" else "💥"
        text += f"{i}. {icon} {result}\n"

    await update.message.reply_text(text)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM rounds WHERE user_id=?",
        (update.effective_user.id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text("🧹 Tarixingiz tozalandi.")


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN topilmadi")

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("win", win))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("clear", clear))

    print("Apple Fortune Analyzer ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
