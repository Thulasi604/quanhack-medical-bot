from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 👇 PUT YOUR TELEGRAM TOKEN HERE (the one you showed me)
TELEGRAM_TOKEN = "8763947687:AAETVPi6d2QBfBRPfuF1Y4T-IQ7jEcFJt_4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏥 *Welcome to Medical Lab Assistant!*\n\n"
        "I can help you book lab tests.\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/book - Book a lab test\n\n"
        "Type /book to get started!",
        parse_mode='Markdown'
    )

async def book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Book Your Test*\n\n"
        "Please send:\n"
        "1️⃣ Test type (blood, urine, xray)\n"
        "2️⃣ Date (tomorrow, May 10th)\n"
        "3️⃣ Time (10am, 2pm)\n\n"
        "*Example:* blood test, tomorrow, 10am",
        parse_mode='Markdown'
    )
    context.user_data['awaiting_booking'] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    
    if context.user_data.get('awaiting_booking'):
        parts = user_message.split(',')
        if len(parts) >= 3:
            test_type = parts[0].strip()
            date = parts[1].strip()
            time = parts[2].strip()
            
            await update.message.reply_text(
                f"✅ *Booking Details:*\n\n"
                f"Test: {test_type}\n"
                f"Date: {date}\n"
                f"Time: {time}\n\n"
                f"Reply with *CONFIRM* to book.",
                parse_mode='Markdown'
            )
            context.user_data['booking'] = {'test': test_type, 'date': date, 'time': time}
            context.user_data['awaiting_confirm'] = True
            context.user_data['awaiting_booking'] = False
        else:
            await update.message.reply_text(
                "Please use format: test type, date, time\n"
                "Example: blood test, tomorrow, 10am"
            )
    
    elif context.user_data.get('awaiting_confirm') and user_message == 'confirm':
        booking = context.user_data.get('booking', {})
        await update.message.reply_text(
            f"✅ *Booking Confirmed!*\n\n"
            f"Your {booking.get('test', 'test')} is booked for {booking.get('date', '')} at {booking.get('time', '')}.\n\n"
            f"You'll receive a reminder before your test.\n\n"
            f"Thank you for choosing our lab!",
            parse_mode='Markdown'
        )
        context.user_data.clear()
    
    else:
        await update.message.reply_text(
            "Type /start to begin or /book to book a test"
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("book", book_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Medical Bot is running... Press Ctrl+C to stop")
    app.run_polling()

if __name__ == '__main__':
    main()