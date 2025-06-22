import os
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Env variables
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # contoh: @channelkamu
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # isi ID kamu

# Konfigurasi kuota
KUOTA_AWAL = 5
user_kuota = {}  # user_id: int
last_reset_date = None  # tanggal reset terakhir
is_paused = False

# 🔁 Reset kuota semua user setiap jam 06.00 WIB
def reset_kuota_harian():
    global last_reset_date, user_kuota

    now_utc = datetime.utcnow()
    now_wib = now_utc + timedelta(hours=7)  # WIB = UTC+7

    if (now_wib.time() >= time(6, 0)) and (last_reset_date != now_wib.date()):
        for user_id in user_kuota:
            user_kuota[user_id] = KUOTA_AWAL
        last_reset_date = now_wib.date()

# 🟢 Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang!\n\n"
        "Kirim menfess dengan format:\n"
        "`#menfess isi pesanmu`\n"
        "atau kirim foto + caption pakai `#menfess`\n\n"
        "Cek kuota kamu dengan /kuota",
        parse_mode="Markdown"
    )

# 📊 Kuota
async def cek_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_kuota_harian()
    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)
    await update.message.reply_text(f"📊 Kuota kamu hari ini: {kuota}")

# ➕ Tambah kuota (admin)
async def tambah_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ⏸ Pause bot (admin)
async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Kamu bukan admin.")
        return
    is_paused = True
    await update.message.reply_text("⏸️ Bot sekarang dalam mode PAUSE.")

# ▶ Resume bot (admin)
async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Kamu bukan admin.")
        return
    is_paused = False
    await update.message.reply_text("▶️ Bot sudah aktif kembali.")

# 📨 Handle #menfess
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    reset_kuota_harian()

    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)

    if is_paused:
        await update.message.reply_text("🚫 Bot sedang pause, menfess tidak bisa dikirim sekarang.")
        return

    if kuota <= 0:
        await update.message.reply_text("❌ Kuota kamu habis. Coba lagi besok jam 06.00 WIB!")
        return

    msg_text = update.message.text or update.message.caption or ""
    if not msg_text.lower().startswith("#menfess"):
        return

    isi = msg_text[len("#menfess"):].strip()
    message = None

    # Kirim ke channel
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
    # Tombol link postingan (jika channel public)
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

# 🚀 Jalankan bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kuota", cek_kuota))
app.add_handler(CommandHandler("tambahkuota", tambah_kuota))
app.add_handler(CommandHandler("pause", pause))
app.add_handler(CommandHandler("resume", resume))
app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_menfess))

app.run_polling()
