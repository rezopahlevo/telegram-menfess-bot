import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
KUOTA_AWAL = 5

user_kuota = {}

# Handler untuk menfess
effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)

    if is_paused:
        await update.message.reply_text("🚫 Bot sedang pause, menfess tidak bisa dikirim sekarang.")
        return

    if kuota <= 0:
        await update.message.reply_text("❌ Kuota kamu habis. Hubungi admin untuk menambah kuota.")
        return

    msg_text = update.message.text or update.message.caption or ""
    if not msg_text.lower().startswith("#menfess"):
        return

    isi = msg_text[len("#menfess"):].strip()
    message = None

    if update.message.photo:
        photo = update.message.photo[-1].file_id
        message = await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=isi)
    elif update.message.text:
        message = await context.bot.send_message(chat_id=CHANNEL_ID, text=isi)
    else:
        await update.message.reply_text("❌ Format tidak didukung.")
        return

    # Kurangi kuota
    user_kuota[user_id] = kuota - 1
    sisa = user_kuota[user_id]

    # 🔗 Tambahkan tombol link jika channel public
    if CHANNEL_ID.startswith("@"):
        channel_username = CHANNEL_ID[1:]
        post_link = f"https://t.me/{channel_username}/{message.message_id}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Lihat Postingan", url=post_link)]
        ])
        await update.message.reply_text(
            f"✅ Menfess kamu sudah dikirim!\n📊 Sisa kuota: {sisa}",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            f"✅ Menfess kamu sudah dikirim!\n📊 Sisa kuota: {sisa}"
        )

# Cek kuota
async def cek_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)
    await update.message.reply_text(f"📊 Kuota kamu: {kuota}")

# Tambah kuota manual (admin only)
async def tambah_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = update.effective_user.id  # Ganti kalau perlu validasi lebih kuat
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Kamu bukan admin.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Format: /tambahkuota user_id jumlah")
        return

    try:
        user_id = int(context.args[0])
        jumlah = int(context.args[1])
        user_kuota[user_id] = user_kuota.get(user_id, KUOTA_AWAL) + jumlah
        await update.message.reply_text(f"✅ Kuota user {user_id} ditambah {jumlah}.")
    except:
        await update.message.reply_text("❌ Format salah.")

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Kirim menfess dengan format:\n\n"
        "`#menfess isi pesanmu`\n"
        "atau kirim foto + caption pakai `#menfess`",
        parse_mode="Markdown"
    )

# Jalankan bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kuota", cek_kuota))
app.add_handler(CommandHandler("tambahkuota", tambah_kuota))
app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_menfess))
app.run_polling()
