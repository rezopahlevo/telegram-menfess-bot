import os
from datetime import datetime, timedelta, time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ENV
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # ex: @namachannel
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Ganti dengan ID kamu

# Data
KUOTA_AWAL = 5
user_kuota = {}
premium_user = {}  # user_id: expired_date
emoji_user = {}    # user_id: emoji
last_reset_date = None
is_paused = False

# Emoji Premium
emoji_tier = {
    "common": ["😇", "😎", "😁", "🐣", "🌻"],
    "rare": ["💎", "🔥", "🧠", "🌈", "🦄"],
    "legendary": ["👑", "💀", "🌟", "😈", "⚡"]
}
emoji_chance = {
    "common": 60,
    "rare": 30,
    "legendary": 10
}

# Reset kuota harian (jam 6 pagi WIB)
def reset_kuota_harian():
    global last_reset_date, user_kuota
    now_utc = datetime.utcnow()
    now_wib = now_utc + timedelta(hours=7)

    if (now_wib.time() >= time(6, 0)) and (last_reset_date != now_wib.date()):
        for user_id in user_kuota:
            user_kuota[user_id] = KUOTA_AWAL
        last_reset_date = now_wib.date()

# Cek apakah user masih premium
def is_user_premium(user_id):
    now = datetime.utcnow()
    expired = premium_user.get(user_id)
    return expired and now < expired

# 🎰 Gacha emoji premium
def gacha_emoji():
    roll = random.randint(1, 100)
    if roll <= emoji_chance["common"]:
        return random.choice(emoji_tier["common"])
    elif roll <= emoji_chance["common"] + emoji_chance["rare"]:
        return random.choice(emoji_tier["rare"])
    else:
        return random.choice(emoji_tier["legendary"])

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang di bot Menfess!\n\n"
        "Kirim menfess dengan format:\n"
        "`#menfess isi pesan kamu`\n"
        "atau kirim foto + caption pakai `#menfess`\n\n"
        "📊 Kuota harian: 5x, reset tiap jam 06.00 WIB\n"
        "🛡️ Member Premium bisa dapat emoji eksklusif via /gachaemoji\n"
        "📌 Cek kuota dengan /kuota\n"
        "🔑 Info premium via admin",
        parse_mode="Markdown"
    )

# /kuota
async def cek_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_kuota_harian()
    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)
    await update.message.reply_text(f"📊 Kuota kamu hari ini: {kuota}")

# /pause
async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    is_paused = True
    await update.message.reply_text("⏸️ Bot sekarang dalam mode PAUSE.")

# /resume
async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    is_paused = False
    await update.message.reply_text("▶️ Bot sudah aktif kembali.")

# /tambahkuota
async def tambah_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    try:
        user_id = int(context.args[0])
        jumlah = int(context.args[1])
        user_kuota[user_id] = user_kuota.get(user_id, KUOTA_AWAL) + jumlah
        await update.message.reply_text(f"✅ Kuota user {user_id} ditambah {jumlah}.")
    except:
        await update.message.reply_text("❌ Format salah. /tambahkuota user_id jumlah")

# /premium (admin)
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    try:
        user_id = int(context.args[0])
        hari = int(context.args[1])
        premium_user[user_id] = datetime.utcnow() + timedelta(days=hari)
        await update.message.reply_text(f"✅ User {user_id} jadi premium selama {hari} hari.")
    except:
        await update.message.reply_text("❌ Format: /premium user_id hari")

# /gachaemoji
async def gachaemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_premium(user_id):
        return await update.message.reply_text("❌ Fitur ini hanya untuk member premium.")

    emoji = gacha_emoji()
    emoji_user[user_id] = emoji
    await update.message.reply_text(f"🎰 Kamu mendapatkan emoji premium: {emoji}")

# /kirimemoji user_id
async def kirimemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pengirim = update.effective_user.id
    if not is_user_premium(pengirim):
        return await update.message.reply_text("❌ Kamu bukan member premium.")

    try:
        penerima = int(context.args[0])
        if not is_user_premium(penerima):
            return await update.message.reply_text("❌ Penerima bukan member premium.")
        if pengirim not in emoji_user:
            return await update.message.reply_text("❌ Kamu belum punya emoji.")

        emoji_user[penerima] = emoji_user[pengirim]
        del emoji_user[pengirim]
        await update.message.reply_text(f"🔁 Emoji kamu sudah dikirim ke {penerima}.")
    except:
        await update.message.reply_text("❌ Format: /kirimemoji user_id")

# handle menfess
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    reset_kuota_harian()
    user_id = update.effective_user.id

    kuota = user_kuota.get(user_id, KUOTA_AWAL)
    if is_paused:
        return await update.message.reply_text("🚫 Bot sedang pause.")
    if kuota <= 0:
        return await update.message.reply_text("❌ Kuota kamu habis. Tunggu besok jam 06.00 WIB.")

    msg_text = update.message.text or update.message.caption or ""
    if not msg_text.lower().startswith("#menfess"):
        return

    isi = msg_text[len("#menfess"):].strip()

    # Tambahkan emoji premium jika ada
    prefix = ""
    if is_user_premium(user_id) and user_id in emoji_user:
        prefix = f"{emoji_user[user_id]} "

    message = None
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        message = await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=prefix + isi)
    elif update.message.text:
        message = await context.bot.send_message(chat_id=CHANNEL_ID, text=prefix + isi)
    else:
        return await update.message.reply_text("❌ Format tidak didukung.")

    user_kuota[user_id] = kuota - 1
    sisa = user_kuota[user_id]

    # Tombol lihat postingan
    if CHANNEL_ID.startswith("@"):
        channel_username = CHANNEL_ID[1:]
        post_link = f"https://t.me/{channel_username}/{message.message_id}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Lihat Postingan", url=post_link)]
        ])
        await update.message.reply_text(
            f"✅ Menfess dikirim!\n📊 Sisa kuota: {sisa}",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(f"✅ Menfess dikirim!\n📊 Sisa kuota: {sisa}")

# App init
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kuota", cek_kuota))
app.add_handler(CommandHandler("pause", pause))
app.add_handler(CommandHandler("resume", resume))
app.add_handler(CommandHandler("tambahkuota", tambah_kuota))
app.add_handler(CommandHandler("premium", premium))
app.add_handler(CommandHandler("gachaemoji", gachaemoji))
app.add_handler(CommandHandler("kirimemoji", kirimemoji))
app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_menfess))

app.run_polling()
