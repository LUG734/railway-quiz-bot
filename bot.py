import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    PollAnswerHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Retrieve token from cloud environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

QUIZ_QUESTIONS = [
    {
        "question": "1. What is the maximum permissible speed over non-interlocked facing points during NI working?",
        "options": ["15 kmph", "30 kmph", "50 kmph", "20 kmph"],
        "correct_option_id": 1,
        "explanation": "Para 257: Speed over non-interlocked facing points shall not exceed 30 kmph in any circumstances.",
    },
    {
        "question": "2. What is the total length of a standard Sand Hump used for isolation?",
        "options": ["30 meters", "45 meters", "60 meters", "180 meters"],
        "correct_option_id": 2,
        "explanation": "Para 230(b): A sand hump is 60 m in length (30 m normal track embedded in sand + 30 m earthen lump).",
    },
    {
        "question": "3. Station Working Rules (SWRs) must be reviewed after how many years?",
        "options": ["Every 1 year", "Every 3 years", "Every 5 years", "Every 10 years"],
        "correct_option_id": 2,
        "explanation": "Para 246: SWRs should be reviewed once every 5 years or after issue of 5 correction slips.",
    },
    {
        "question": "4. What is the button code on the control panel for Emergency Route Cancellation?",
        "options": ["EUYN", "EUUYN", "EGRN", "EWN"],
        "correct_option_id": 0,
        "explanation": "Para 231(b): EUYN (or ERRB) is the Emergency Route Cancellation button (Grey color).",
    },
    {
        "question": "5. What is the recommended flatter gradient in station yards for new works?",
        "options": ["1 in 100", "1 in 400", "1 in 1200", "1 in 200"],
        "correct_option_id": 2,
        "explanation": "Para 237: The recommended flatter gradient for new works in station yards is 1 in 1200 (0.083%).",
    },
    {
        "question": "6. For how long must the Caution Order Register and Books be preserved at stations?",
        "options": ["1 year", "3 years", "5 years", "Permanent Record"],
        "correct_option_id": 0,
        "explanation": "Para 223 (Item 2): Caution order register and Caution Order books must be preserved for 1 year.",
    },
    {
        "question": "7. What is the validity of a Temporary Working Order (TWO) from the date of issue?",
        "options": ["1 month", "2 months", "3 months", "6 months"],
        "correct_option_id": 2,
        "explanation": "Para 253(4)(n): The validity of TWO is 3 months from the date of issue.",
    },
    {
        "question": "8. Under Standard-IV Interlocking, what is the maximum permissible speed?",
        "options": ["Up to 110 kmph", "Up to 140 kmph", "Up to 160 kmph", "Up to 200 kmph"],
        "correct_option_id": 2,
        "explanation": "Para 228 (Table): Maximum permissible speed under Standard IV Interlocking is up to 160 kmph.",
    },
    {
        "question": "9. In Standard Layouts, what is the minimum CSR length for greenfield projects?",
        "options": ["650 meters", "750 meters", "798 meters", "850 meters"],
        "correct_option_id": 2,
        "explanation": "Para 237: CSR shall not be less than 798 meters (24m + 750m + 24m) for a green field project.",
    },
    {
        "question": "10. How frequently can the Relay Room key be taken for scheduled maintenance?",
        "options": ["Once a week", "Once in a calendar month", "Once every 15 days", "Twice a month"],
        "correct_option_id": 1,
        "explanation": "Para 261(b): Relay Room key for scheduled maintenance shall be taken only once in a calendar month.",
    },
]

user_sessions = {}
poll_mapping = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🚦 *Welcome to the Indian Railways Operating Manual Quiz Bot!* 🚉\n\n"
        "Commands:\n"
        "▶️ /quiz - Start the 10-question quiz\n"
        "🛑 /stop - Cancel ongoing quiz\n"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def send_next_question(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    session = user_sessions.get(user_id)
    if not session:
        return

    q_idx = session["current_q"]
    if q_idx >= len(QUIZ_QUESTIONS):
        score = session["score"]
        total = len(QUIZ_QUESTIONS)
        pct = (score / total) * 100
        msg = f"🏁 *Quiz Finished!*\n\nScore: *{score} / {total}* ({pct:.1f}%)\n\nType /quiz to try again!"
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        del user_sessions[user_id]
        return

    q_data = QUIZ_QUESTIONS[q_idx]
    poll_message = await context.bot.send_poll(
        chat_id=chat_id,
        question=q_data["question"],
        options=q_data["options"],
        type="quiz",
        correct_option_id=q_data["correct_option_id"],
        explanation=q_data["explanation"],
        is_anonymous=False,
    )

    poll_mapping[poll_message.poll.id] = {
        "user_id": user_id,
        "chat_id": chat_id,
        "question_idx": q_idx,
    }

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_sessions[user_id] = {"current_q": 0, "score": 0, "chat_id": chat_id}
    await update.message.reply_text("🚀 Starting Chapter 2 Quiz! Answer below:", parse_mode="Markdown")
    await send_next_question(chat_id, user_id, context)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("🛑 Quiz terminated. Press /quiz to restart.")
    else:
        await update.message.reply_text("No active quiz running.")

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    poll_id = answer.poll_id
    if poll_id not in poll_mapping:
        return
    info = poll_mapping.pop(poll_id)
    user_id = info["user_id"]
    chat_id = info["chat_id"]
    q_idx = info["question_idx"]

    if user_id not in user_sessions:
        return

    if answer.option_ids[0] == QUIZ_QUESTIONS[q_idx]["correct_option_id"]:
        user_sessions[user_id]["score"] += 1

    user_sessions[user_id]["current_q"] += 1
    await send_next_question(chat_id, user_id, context)

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN variable is missing.")
        return
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    application.run_polling()

if __name__ == "__main__":
    main()
