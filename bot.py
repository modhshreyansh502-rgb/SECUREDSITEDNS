import os
from dotenv import load_dotenv
from google import genai
from telegram import Update
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

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Tumhara naam SecuredSiteDns AI Bot hai.

Rules:
- Kabhi mat bolna ki tum Gemini ho.
- Kabhi mat bolna ki tum Google AI ho.
- Agar koi puche tum kaun ho to bolo:
  "Main SecuredSiteDns AI Bot hoon."
- Hinglish me friendly aur helpful jawab do.
"""

PROMO = """

━━━━━━━━━━━━━━━━━━━━━━━
🌐 Hosting | Domain | VPS

Agar Hosting, Domain ya VPS chahiye to visit kare:

👉 https://SecuredSiteDns.in

━━━━━━━━━━━━━━━━━━━━━━━
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nMain SecuredSiteDns AI Bot hoon.\nKuch bhi puchiye." + PROMO
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\nUser: {user_message}"
        )

        answer = response.text

    except Exception as e:
        answer = f"❌ Error:\n{e}"

    await update.message.reply_text(answer + PROMO)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✅ SecuredSiteDns AI Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
