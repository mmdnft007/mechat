import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import random

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# توکن ربات خودتون رو اینجا بذارید
TOKEN = "8425796435:AAGl33lJhkNTk3hmdiJTHKfNTtK4pofj078"

# دیکشنری برای ذخیره جفت‌های چت و لیست بلاک‌شده‌ها
chat_pairs = {}  # {user_id: partner_id}
blocked_users = {}  # {user_id: set(blocked_user_ids)}
waiting_users = []  # لیست کاربران در انتظار

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("اتصال به یک ناشناس", callback_data='connect')],
        [InlineKeyboardButton("توقف چت", callback_data='stop')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "به ربات چت ناشناس خوش آمدید! برای شروع چت با یک فرد ناشناس، روی دکمه زیر کلیک کنید:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'connect':
        if user_id in chat_pairs:
            await query.message.reply_text("شما در حال حاضر در یک چت هستید. برای خروج از چت، از دکمه 'توقف چت' استفاده کنید.")
            return
        if user_id in waiting_users:
            await query.message.reply_text("شما در لیست انتظار هستید. لطفاً منتظر بمانید.")
            return

        waiting_users.append(user_id)
        if len(waiting_users) >= 2:
            partner_id = random.choice([uid for uid in waiting_users if uid != user_id and (user_id not in blocked_users.get(uid, set()))])
            waiting_users.remove(user_id)
            waiting_users.remove(partner_id)
            chat_pairs[user_id] = partner_id
            chat_pairs[partner_id] = user_id
            await context.bot.send_message(user_id, "شما به یک فرد ناشناس متصل شدید! شروع به چت کنید.")
            await context.bot.send_message(partner_id, "شما به یک فرد ناشناس متصل شدید! شروع به چت کنید.")
        else:
            await query.message.reply_text("در حال جستجوی یک فرد ناشناس... لطفاً منتظر بمانید.")

    elif query.data == 'stop':
        if user_id in chat_pairs:
            partner_id = chat_pairs.pop(user_id)
            chat_pairs.pop(partner_id, None)
            await context.bot.send_message(user_id, "چت شما پایان یافت.")
            await context.bot.send_message(partner_id, "طرف مقابل چت را پایان داد.")
        else:
            await query.message.reply_text("شما در هیچ چتی نیستید.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_pairs:
        partner_id = chat_pairs[user_id]
        await context.bot.send_message(partner_id, update.message.text)
    else:
        await update.message.reply_text("شما در حال حاضر در هیچ چتی نیستید. از /start استفاده کنید.")

async def block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_pairs:
        partner_id = chat_pairs[user_id]
        blocked_users.setdefault(user_id, set()).add(partner_id)
        chat_pairs.pop(user_id)
        chat_pairs.pop(partner_id, None)
        await context.bot.send_message(user_id, "کاربر مقابل بلاک شد و چت پایان یافت.")
        await context.bot.send_message(partner_id, "طرف مقابل چت را پایان داد.")
    else:
        await update.message.reply_text("شما در هیچ چتی نیستید.")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("block", block))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await app.initialize()
    await app.start()
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())