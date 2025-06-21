import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
KUOTA_AWAL = 5

user_kuota = {}

# Handler untuk menfess
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)

    if kuota <= 0:
        await update.message.reply_text("❌ Kuota kamu habis. Hubungi admin untuk menambah kuota.")
        return

    msg_text = update.message.text or update.message.caption or ""
    if not msg_text.lower().startswith("#menfess"):
        return

    isi = msg_text[len("#menfess"):].strip()

    if update.message.photo:
        photo = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=isi)
    elif update.message.text:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=isi)
    else:
        await update.message.reply_text("❌ Format tidak didukung. Kirim teks atau foto saja.")
        return

    user_kuota[user_id] = kuota - 1
    sisa = user_kuota[user_id]
    await update.message.reply_text(
        f"✅ Menfess kamu dikirim ke channel!\n📊 Sisa kuota kamu: {sisa}"
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