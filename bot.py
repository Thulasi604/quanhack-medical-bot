from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import json
import re
import datetime
import threading
import time

# My keys
TELEGRAM_TOKEN = "8763947687:AAETVPi6d2QBfBRPfuF1Y4T-IQ7jEcFJt_4"


# Connect to Groq
client = Groq(api_key=GROQ_API_KEY)

# Store pending bookings and confirmed bookings
pending = {}
confirmed_bookings = []
reminder_sent = set()

async def send_reminder(user_id, test, date, time):
    """Send reminder 24 hours before test"""
    await application.bot.send_message(
        chat_id=user_id,
        text=f"🔔 REMINDER\n\nYour {test} test is scheduled for {date} at {time}.\n\nPlease arrive 15 minutes early."
    )

def schedule_reminder(user_id, test, date, time):
    """Schedule a reminder (simplified for demo)"""
    # In real app, calculate actual time. For demo, send after 30 seconds
    def reminder_job():
        time.sleep(30)  # Wait 30 seconds for demo
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
        "I'll book it and send you a reminder.",
    )

async def report_ready(update, context):
    """Manual command to send report ready notification"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "📄 Your lab report is ready!\n\n"
        "You can download it from our portal or visit the lab.\n\n"
        "Thank you for choosing our services."
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
            f"Thank you!"
        )
        
        # Schedule reminder (in demo, sends after 30 seconds)
        schedule_reminder(user_id, b['test'], b['date'], b['time'])
        
        del pending[user_id]
        return
    
    # Handle REPORT command
    if user_msg.upper() == '/REPORT':
        await report_ready(update, context)
        return
    
    # Pure AI - No fallback
    prompt = f'Extract test, date, time from: "{user_msg}". Return ONLY JSON: {{"test":"","date":"","time":""}}'
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    # Clean and parse JSON
    result = response.choices[0].message.content
    result = re.sub(r'```json\s*', '', result)
    result = re.sub(r'```\s*', '', result)
    result = result.strip()
    
    data = json.loads(result)
    
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
    global application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("report", report_ready))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("AI Medical Bot with Reminders running...")
    application.run_polling()

if __name__ == '__main__':
    main()
