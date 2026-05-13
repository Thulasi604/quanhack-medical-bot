from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from dotenv import load_dotenv
import os
import json
import re
import threading
import time

# Load API keys from .env
load_dotenv()

# Get keys from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Connect to Groq AI
client = Groq(api_key=GROQ_API_KEY)

# Store pending bookings before confirmation
pending = {}

# Store confirmed bookings
confirmed_bookings = []

async def send_reminder(user_id, test, date, time):
    """Send reminder to user"""
    try:
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        await app.bot.send_message(
            chat_id=user_id,
            text=f"🔔 REMINDER\n\nYour {test} test is scheduled for {date} at {time}.\n\nPlease arrive 15 minutes early."
        )
    except Exception as e:
        print(f"Reminder error: {e}")

def schedule_reminder(user_id, test, date, time):
    """Schedule reminder in background thread"""
    def reminder_job():
        time.sleep(30)  # 30 seconds for demo
        import asyncio
        asyncio.run(send_reminder(user_id, test, date, time))
    
    thread = threading.Thread(target=reminder_job)
    thread.start()

async def start(update, context):
    await update.message.reply_text(
        "🏥 *Lab Booking Assistant*\n\n"
        "Just tell me what test you need.\n\n"
        "*Examples:*\n"
        "• 'I need a sugar test tomorrow at 10am'\n"
        "• 'Book blood test for Friday 2pm'\n\n"
        "I'll book it and send you a reminder.\n\n"
        "*Commands:*\n"
        "/report - Check your report status",
        parse_mode='Markdown'
    )

async def report_command(update, context):
    """Send report ready notification"""
    await update.message.reply_text(
        "📄 *Report Update*\n\n"
        "Your lab report is being processed.\n"
        "You will be notified when it's ready.\n\n"
        "For urgent inquiries, please contact the lab directly.",
        parse_mode='Markdown'
    )

async def handle_message(update, context):
    user_msg = update.message.text
    user_id = update.effective_user.id
    
    # Handle CONFIRM
    if user_msg.upper() == 'CONFIRM' and user_id in pending:
        b = pending[user_id]
        
        # Save to confirmed bookings
        confirmed_bookings.append({
            "user_id": user_id,
            "test": b['test'],
            "date": b['date'],
            "time": b['time']
        })
        
        await update.message.reply_text(
            f"✅ Confirmed!\n\n"
            f"Test: {b['test']}\n"
            f"Date: {b['date']}\n"
            f"Time: {b['time']}\n\n"
            f"🔔 I will send you a reminder before your test.\n\n"
            f"Thank you for choosing our lab!"
        )
        
        # Schedule reminder 
        schedule_reminder(user_id, b['test'], b['date'], b['time'])
        
        del pending[user_id]
        return
    
    # AI prompt to extract test, date, time
    prompt = f'Extract test, date, time from: "{user_msg}". Return ONLY JSON: {{"test":"","date":"","time":""}}'
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    # Clean and parse JSON response
    result = response.choices[0].message.content
    result = re.sub(r'```json\s*', '', result)
    result = re.sub(r'```\s*', '', result)
    result = result.strip()
    
    data = json.loads(result)
    
    # Store pending booking
    pending[user_id] = {
        "test": data.get("test", "test"),
        "date": data.get("date", "tomorrow"),
        "time": data.get("time", "10am")
    }
    
    await update.message.reply_text(
        f"AI understood:\n\n"
        f"Test: {pending[user_id]['test']}\n"
        f"Date: {pending[user_id]['date']}\n"
        f"Time: {pending[user_id]['time']}\n\n"
        f"Reply CONFIRM to book.\n\n"
        f"I will send you a reminder before your test!"
    )

def main():
    global app
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 AI Medical Bot with Reminders is running...")
    print("✅ Reminders will be sent 30 seconds after booking")
    print("✅ Type /report to check report status")
    app.run_polling()

if __name__ == '__main__':
    main()
