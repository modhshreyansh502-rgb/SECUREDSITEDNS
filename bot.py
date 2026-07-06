import os
import json
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

USERS_FILE = "users.json"

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Tumhara naam SecuredSiteDns AI Bot hai.

Rules:
- Kabhi mat bolna ki tum Gemini ho.
- Kabhi mat bolna ki tum Google AI ho.
- Agar koi puche tum kaun ho to bolo: Main SecuredSiteDns AI Bot hoon.
- Hinglish me friendly aur helpful jawab do.
- Jawab short, clear aur direct do.
- Agar user coding puche to clean code ke sath explain karo.
"""

PROMO = """

━━━━━━━━━━━━━━━━━━━━━━━
🌐 Hosting | Domain | VPS
👉 https://SecuredSiteDns.in
━━━━━━━━━━━━━━━━━━━━━━━
"""

user_memory = {}


def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)


users = load_users()


def is_admin(user_id):
    return user_id in ADMIN_IDS


def split_message(text, limit=4000):
    return [text[i:i + limit] for i in range(0, len(text), limit)]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)
    save_users(users)

    msg = (
        "👋 Welcome!\n\n"
        "Main SecuredSiteDns AI Bot hoon.\n"
        "Kuch bhi puchiye.\n\n"
        "Commands:\n"
        "/help - Help dekho\n"
        "/reset - Chat memory clear karo"
    )
    await update.message.reply_text(msg + PROMO)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)
    save_users(users)

    msg = """
🤖 SecuredSiteDns AI Bot Help

Aap mujhse puch sakte ho:
• Coding help
• Error solve
• Content writing
• Translation
• Business ideas
• General questions

Commands:
/start - Bot start
/help - Help
/reset - Chat memory reset
"""
    await update.message.reply_text(msg + PROMO)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_memory.pop(chat_id, None)
    await update.message.reply_text("✅ Chat memory reset ho gayi." + PROMO)


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Aap admin nahi ho.")

    msg = """
🔐 Admin Panel

/stats - Bot stats dekho
/users - Total users dekho
/broadcast message - Sab users ko message bhejo
"""
    await update.message.reply_text(msg)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Aap admin nahi ho.")

    msg = f"""
📊 Bot Stats

👥 Total users: {len(users)}
🧠 Active memory chats: {len(user_memory)}
👑 Admins: {len(ADMIN_IDS)}
"""
    await update.message.reply_text(msg)


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Aap admin nahi ho.")

    await update.message.reply_text(f"👥 Total users: {len(users)}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Aap admin nahi ho.")

    message = " ".join(context.args)

    if not message:
        return await update.message.reply_text(
            "Use aise karo:\n/broadcast Hello everyone!"
        )

    sent = 0
    failed = 0

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast complete\n\nSent: {sent}\nFailed: {failed}"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_message = update.message.text

    users.add(user_id)
    save_users(users)

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action=ChatAction.TYPING
    )

    if chat_id not in user_memory:
        user_memory[chat_id] = []

    user_memory[chat_id].append(f"User: {user_message}")
    recent_chat = "\n".join(user_memory[chat_id][-6:])

    prompt = f"""
{SYSTEM_PROMPT}

Previous chat:
{recent_chat}

Bot:
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text.strip()
        user_memory[chat_id].append(f"Bot: {answer}")

    except Exception as e:
        print("GEMINI ERROR:", e)
        answer = "❌ Sorry, abhi response generate nahi ho pa raha. Thodi der baad try kare."
    final_answer = answer + PROMO

    for part in split_message(final_answer):
        await update.message.reply_text(part)


def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing hai")
        return

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing hai")
        return

    if not ADMIN_IDS:
        print("⚠️ ADMIN_IDS missing hai. Admin commands work nahi karenge.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✅ SecuredSiteDns AI Bot with Admin Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
